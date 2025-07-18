import os
import asyncio
import json
import re
from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from typing import Any, List, TypedDict, Annotated
from langchain_core.tools import tool
from tools import (
    search_symbols_companys_USA,
    extract_financial_information_company,
    extract_information_company_yfinance,
    transform_data_to_pdf
)
from nameclass import CompanyParams
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, END
from collections import defaultdict 


load_dotenv()

#Creamos un TypedDict para el estado del agente
class AgentState(TypedDict):
    messages: Annotated[List[Any], "Lista de mensajes"]
    company: str
    symbol: str
    next_action: str


def get_system_message() -> str:
    return """Eres un asistente financiero inteligente con acceso a herramientas especializadas mediante la interfaz MCP (Model Context Protocol).

FLUJO OBLIGATORIO:
1. Buscar símbolo con search_symbols_companys_USA_tool
2. Extraer datos con extract_financial_information_company_tool
2.1. Si no hay datos, usar extract_information_company_yfinance_tool
4. Crear análisis con formato:
   {
     "nombre_empresa": "NOMBRE REAL de la empresa",
     "symbol": "SÍMBOLO REAL obtenido",
     "análisis": "Análisis muy detallado de las métricas financieras",
     "puntuación": "Número del 1 al 10",
     "justificación": "Justificación completa con datos específicos"
   }
5. Generar PDF con transform_data_to_pdf_tool
6. Terminar con "análisis financiero completado"

PROHIBIDO:
- Usar datos genéricos como "Ejemplo Corp", "EXC"
- Inventar números
- Cambiar de empresa

IMPORTANTE:
- Solo métricas financieras en análisis
- El analisis tiene que ser muy detallado basandose en los datos obtenidos de los tools anteriores
- Separar bien los apartados en el PDF
- Lenguaje claro y profesional
- En terminal solo mostrar "análisis financiero completado" al final"""

#Las herramientas que usaremos en el agente
@tool
def search_symbols_companys_USA_tool(company: str) -> dict:
    """Busca el símbolo bursátil de una empresa en USA."""
    try:
        params = CompanyParams(company=company)
        print("Simbolo")
        result = asyncio.run(search_symbols_companys_USA(params))
        return result.model_dump()
    except Exception as e:
        return {"error": str(e)}


@tool
def extract_financial_information_company_tool(symbol: str) -> dict:
    """Extrae información financiera completa de una empresa usando Finnhub."""
    try:
        result = asyncio.run(extract_financial_information_company(symbol))
        data = result.model_dump()

        if not data or not data.get('data') or data['data'] == {} or not data['data'].get('metric'):
            return {
                "error": f"No hay datos válidos en Finnhub para {symbol}",
                "symbol": symbol,
                "usar_yfinance": True
            }

        return data
    except Exception as e:
        return {
            "error": f"Error en Finnhub para {symbol}: {str(e)}",
            "symbol": symbol,
            "usar_yfinance": True
        }


@tool
def extract_information_company_yfinance_tool(symbol: str) -> dict:
    """Extrae información financiera de una empresa usando Yahoo Finance."""
    try:
        result = asyncio.run(extract_information_company_yfinance(symbol))
        data = result.model_dump()
        return data
    except Exception as e:
        return {"error": str(e)}


@tool
def transform_data_to_pdf_tool(nombre_empresa: str, symbol: str, análisis: str, puntuación: str, justificación: str = "") -> dict:
    """Transforma los datos de análisis en un informe PDF."""
    try:
        data = {
            "nombre_empresa": nombre_empresa,
            "symbol": symbol,
            "análisis": análisis,
            "puntuación": puntuación,
            "justificación": justificación,
        }

        if "análisis financiero basado en datos obtenidos de finnhub" in análisis.lower():
            error_msg = "Error: Análisis genérico detectado, se requiere análisis específico"
            return {"error": error_msg}

        result = asyncio.run(transform_data_to_pdf(data))
        return {"pdf_filename": result, "success": True}

    except Exception as e:
        return {"error": str(e)}

## Definimos las herramientas que usaremos en el agente
tools = [
    search_symbols_companys_USA_tool,
    extract_financial_information_company_tool,
    extract_information_company_yfinance_tool,
    transform_data_to_pdf_tool
]

# Configuramos el modelo LLM de Azure OpenAI
llm = AzureChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("AZURE_API_KEY"),
    azure_endpoint=os.getenv("azure_endpoint"),
    api_version="2024-12-01-preview",
    temperature=0.1
)

llm_herramientas = llm.bind_tools(tools)

contador_tokens= defaultdict(int) # Contador de tokens usados

def call_agent(state: AgentState) -> AgentState:  # Maneja el flujo de la conversación
    messages = state["messages"]
    company = state.get("company", "")
    symbol = state.get("symbol", "")

    filtered_messages = []
    for msg in messages:
        # Filtramos los mensajes para mantener solo los relevantes
        if isinstance(msg, (SystemMessage, HumanMessage, AIMessage)):
            filtered_messages.append(msg)

    # Aseguramos que haya un mensaje del sistema al inicio
    if not any(isinstance(m, SystemMessage) for m in filtered_messages):
        filtered_messages = [SystemMessage(
            content=get_system_message())] + filtered_messages
        
    # Verificamos si ya tenemos datos de Finnhub o Yahoo Finance
    tiene_datos_finnhub = False
    tiene_datos_yfinance = False
    analisis_json = None
    finnhub_fallo = False

    # Revisamos los mensajes para encontrar datos relevantes
    for msg in messages:
        if hasattr(msg, 'content'):
            content = str(msg.content)

            # Verificamos si hay datos de Finnhub o Yahoo Finance
            if ("extract_financial_information_company_tool" in content and
                "metric" in content and
                "roe" in content.lower() and
                "pe" in content.lower() and
                    "error" not in content.lower()):
                tiene_datos_finnhub = True
            elif ("extract_financial_information_company_tool" in content and
                  ("error" in content.lower() or "no hay datos válidos" in content.lower())):
                finnhub_fallo = True

            # Verificamos si hay datos de Yahoo Finance
            elif ("extract_information_company_yfinance_tool" in content and
                  "symbol" in content and
                  "company_name" in content and
                  "error" not in content.lower()):
                tiene_datos_yfinance = True
            # Verificamos si hay un análisis JSON ya generado
            elif ("nombre_empresa" in content and "symbol" in content and
                  "análisis" in content and "puntuación" in content):
                try:
                
                    json_match = re.search(
                        r'\{.*?"nombre_empresa".*?\}', content, re.DOTALL)  # Buscamos un JSON válido
                    if json_match:
                        analisis_json = json.loads(json_match.group()) # Convertimos el JSON a un diccionario
                except Exception as e:
                    pass

    context = f"EMPRESA OBJETIVO: {company}\nSÍMBOLO: {symbol}\n\n"

    if not symbol:
        context += f"PASO 1: Buscar símbolo para {company}\nUsar: search_symbols_companys_USA_tool"

    elif analisis_json:
        context += f"PASO 5: Generar PDF final\nUsar: transform_data_to_pdf_tool con {analisis_json}"

    elif tiene_datos_finnhub:
        context += f"""PASO 4: CREAR ANÁLISIS CON DATOS DE FINNHUB
        Tienes datos financieros completos de Finnhub para {company} ({symbol}).
        Crear análisis JSON detallado basado en las métricas reales extraídas.
        Formato: {{"nombre_empresa": "{company}", "symbol": "{symbol}", "análisis": "análisis detallado", "puntuación": "1-10", "justificación": "con datos específicos"}}"""

    elif tiene_datos_yfinance:
        context += f"""PASO 4: CREAR ANÁLISIS CON DATOS DE YAHOO FINANCE  
        Tienes datos financieros de Yahoo Finance para {company} ({symbol}).
        Crear análisis JSON detallado basado en los datos reales extraídos.
        Formato: {{"nombre_empresa": "{company}", "symbol": "{symbol}", "análisis": "análisis detallado", "puntuación": "1-10", "justificación": "con datos específicos"}}"""

    elif finnhub_fallo:
        context += f"PASO 3: Finnhub falló, usar Yahoo Finance\nUsar: extract_information_company_yfinance_tool con symbol='{symbol}'"

    elif symbol and not tiene_datos_finnhub and not tiene_datos_yfinance:
        context += f"PASO 2: Extraer datos de Finnhub\nUsar: extract_financial_information_company_tool con symbol='{symbol}'"

    else:
        context += f"Continuar con el análisis de {company}"

    # Añadimos el mensaje de contexto al inicio de la conversación
    filtered_messages.append(HumanMessage(content=context)) 
    # Llamamos al modelo LLM con los mensajes filtrados
    response = llm_herramientas.invoke(filtered_messages)
    usage = response.response_metadata['token_usage']
    contador_tokens["prompt"] += usage.get("prompt_tokens", 0)
    contador_tokens["completion"] += usage.get("completion_tokens", 0)



    # Verificamos si la respuesta es un JSON válido
    return {
        "messages": state["messages"] + [response],
        "symbol": symbol,
        "company": company,
        "next_action": ""
    }

# Esta función maneja las llamadas a las herramientas según el estado del agente
def call_tools(state: AgentState) -> AgentState:

    messages = state["messages"]
    ultimo_mensaje = messages[-1]
    new_symbol = state.get("symbol", "")

    # Verificamos si el último mensaje contiene llamadas a herramientas
    if hasattr(ultimo_mensaje, 'tool_calls') and ultimo_mensaje.tool_calls:
        new_messages = []

        # Procesamos cada llamada a herramienta
        for tool_call in ultimo_mensaje.tool_calls:
            tool_name = tool_call.get('name', '')
            tool_args = tool_call.get('args', {})

            if tool_name == 'search_symbols_companys_USA_tool':
                result = search_symbols_companys_USA_tool.invoke(tool_args)

                if isinstance(result, dict) and 'symbol' in result:
                    new_symbol = result['symbol']

                # Verificamos si hay un error en la respuesta
                result_message = AIMessage(
                    content=f"Resultado de {tool_name}: {result}")
                # Añadimos el mensaje de resultado a la lista de nuevos mensajes
                new_messages.append(result_message)

            elif tool_name == 'extract_financial_information_company_tool':
                result = extract_financial_information_company_tool.invoke(
                    tool_args)
                # Verificamos si hay un error en la respuesta
                result_message = AIMessage(
                    content=f"Resultado de {tool_name}: {result}")
                # Añadimos el mensaje de resultado a la lista de nuevos mensajes
                new_messages.append(result_message)

            elif tool_name == 'extract_information_company_yfinance_tool':
                result = extract_information_company_yfinance_tool.invoke(
                    tool_args)
                result_message = AIMessage(
                    content=f"Resultado de {tool_name}: {result}")
                new_messages.append(result_message)

            elif tool_name == 'transform_data_to_pdf_tool':
                if tool_args and isinstance(tool_args, dict):
                    # Verificamos que los campos requeridos estén presentes y no vacíos
                    required_fields = ['nombre_empresa','symbol', 'análisis', 'puntuación']
                    # Comprobamos si todos los campos requeridos están presentes y no vacíos
                    has_all_fields = all(
                        field in tool_args and tool_args[field] for field in required_fields)

                    if has_all_fields:
                        result = transform_data_to_pdf_tool.invoke(tool_args)
                        # Verificamos si la respuesta es un PDF válido
                        result_message = AIMessage(
                            content=f"Resultado de {tool_name}: {result}")
                        new_messages.append(result_message)
                    else:
                        # Si faltan campos requeridos, generamos un mensaje de error
                        missing = []
                        for field in required_fields:
                            if field not in tool_args or not tool_args[field]:
                                missing.append(field)
                        error_msg = f"Error: Faltan campos obligatorios: {missing}"
                        result_message = AIMessage(content=error_msg)
                        new_messages.append(result_message)
                else:
                    error_msg = "Error: No se recibieron argumentos válidos para PDF"
                    result_message = AIMessage(content=error_msg)
                    new_messages.append(result_message)

        return {
            "messages": new_messages,
            "symbol": new_symbol,
            "company": state.get("company", ""),
            "next_action": ""
        }

    tool_node = ToolNode(tools)
    result = tool_node.invoke(state)

    return {
        "messages": result["messages"],
        "symbol": new_symbol,
        "company": state.get("company", ""),
        "next_action": ""
    }

# Esta función decide si el agente debe continuar con el flujo o terminar
def should_continue(state: AgentState) -> str:
    # Verificamos el último mensaje del estado
    ultimo_mensaje = state["messages"][-1]


    # Si el último mensaje es un error, terminamos
    if hasattr(ultimo_mensaje, 'tool_calls') and ultimo_mensaje.tool_calls:
        return "tools"

    if hasattr(ultimo_mensaje, 'content') and ultimo_mensaje.content:
        content = str(ultimo_mensaje.content)
        if ("pdf_filename" in content and "success" in content):
            return "end"
        elif "error" in content.lower():
            return "end"

    if len(state["messages"]) > 12:
        return "end"

    return "agent"


# Creamos el grafo de estados del agente
graph = StateGraph(AgentState)

# Añadimos los nodos al grafo
graph.add_node("agent", call_agent)
graph.add_node("tools", call_tools)

# Añadimos el nodo de INICIO
graph.set_entry_point("agent")

# Añadimos el condicional
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "agent": "agent",
        "end": END,
    }
)

# Añadimos el vertice
graph.add_edge("tools", "agent")

# Compilamos el grafo
app = graph.compile()
# Contadores de tokens
prompt_tokens = lambda: contador_tokens["prompt"]
completion_tokens = lambda: contador_tokens["completion"]

#Comprobar ultimo mensaje
def check_final_message(content: str) -> bool:
    """Verifica si el análisis está completado."""
    try:
        if not content:
            return False
        content_lower = str(content).lower()
        return "análisis financiero completado" in content_lower
    except Exception:
        return False
