import os
import asyncio
from dotenv import load_dotenv
from mcp_agent import MCPAssistantAgent
from autogen import UserProxyAgent
import time
import psutil
from collections import defaultdict


load_dotenv()
contador_tokens = defaultdict(int)

def track_tokens(response):
    """Extrae y cuenta tokens de la respuesta de OpenAI"""
    if hasattr(response, 'usage') and response.usage:
        usage = response.usage
        contador_tokens["prompt"] += getattr(usage, 'prompt_tokens', 0)
        contador_tokens["completion"] += getattr(usage, 'completion_tokens', 0)
    elif hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
        usage = response.response_metadata['token_usage']
        contador_tokens["prompt"] += usage.get("prompt_tokens", 0)
        contador_tokens["completion"] += usage.get("completion_tokens", 0)

#Intercepta automaticamente las llamadas a OpenAI para contar los tokens utilizados.
try:
    import openai
    original_create=openai.resources.chat.completions.Completions.create

    def create(self, **kwargs):
        response = original_create(self, **kwargs)
        track_tokens(response)
        return response
    
    openai.resources.chat.completions.Completions.create = create
except ImportError:
    pass




def get_system_message() -> str:
    return """Eres un asistente financiero inteligente con acceso a herramientas especializadas mediante la interfaz MCP (Model Context Protocol). Tu objetivo es ayudar al usuario a obtener información financiera de empresas cotizadas.

        Herramientas disponibles:

        1. **search_symbols_companys_USA_tool**
        - Descripción: Dado un nombre de empresa, busca y devuelve su símbolo bursátil.
        - Parámetros: {"company": "Nombre de la empresa"}
        - Respuesta: Un objeto JSON con el símbolo bursátil de la empresa.

        2. **extract_financial_information_company_tool**
        - Descripción: Dado un símbolo bursátil, extrae los datos financieros completos de la empresa.
        - Parámetros: {"symbol": "Símbolo bursátil de la empresa"}

        3. **extract_information_company_yfinance_tool**
        - Descripción: Dado un símbolo bursátil, extrae información financiera utilizando la API de Yahoo Finance.
        - Parámetros: {"symbol": "Símbolo bursátil de la empresa"}

        4. **transform_data_to_pdf_tool**
        - Descripción: Transforma los datos financieros obtenidos en un informe PDF.
        - Parámetros: {"data": dict con el análisis detallado. Ejemplo:
            {
                "nombre_empresa": "Nombre de la empresa",
                "symbol": "SYM",
                "análisis": "Tu análisis MUY DETALLADO solo de métricas",
                "puntuación": "Número del 1 al 10",
                "justificación": "Justificación detallada con todos los datos y métricas utilizadas"
            }


        Buenas prácticas:
        - Siempre comienza listando las herramientas disponibles si no estás seguro de cuáles están activas.
        - Usa el esquema de parámetros exactamente como se especifica en cada herramienta.
        - Realiza llamadas a herramientas con `call_tool`, proporcionando el `name` y los `args` correctos.
        - No asumas que los nombres de herramientas o parámetros estarán disponibles en todos los servidores.

        FLUJO OBLIGATORIO:
        1. Buscar símbolo con search_symbols_companys_USA_tool
        2. Extraer datos con extract_financial_information_company_tool y si no funciona, utilizar extract_information_company_yfinance_tool.
        3. Realizar análisis completo basado en los datos obtenidos, incluyendo:
            - Evaluar métricas financieras clave
           - Identificar tendencias y patrones
           - Calcular ratios importantes
           - Dar recomendación de inversión (1-10)
           - Justificar tu recomendación
        4. CREAR un diccionario con TU ANÁLISIS (NO los datos brutos):
           {
             "nombre_empresa": "Nombre de la empresa",
             "symbol": "SÍMBOLO",
             "análisis": "Tu análisis MUY DETALLADO de las métricas 
             "puntuación": "Dar una puntuación de 1 a 10",
             "justificación": "Tu justificación completa Y quiero que pongas TODOS los datos que has utilizado para llegar a esa conclusión"
           }
        5. Pasar SOLO tu análisis al transform_data_to_pdf_tool para generar un informe PDF.
        5. Terminar con "ANÁLISIS FINANCIERO COMPLETADO" y NO QUIERO que se repita el análisis.


        Impportante: 
                - No pases los datos brutos al PDF
                - El PDF debe contener TU análisis, TUS conclusiones, TU recomendación. QUIERO QUE ESTEN BIEN SEPARADOS LOS APARTADOS Y NO SE COLAPSEN 
                - Sé específico en tus recomendaciones y justificaciones
                -En analisis, solo quiero que analices las metricas y no pongas nada de otros apartados (NO INCLUYAS NI RECOMENDACIÓN, NI PUNTUACIÓN, NI JUSTIFICACIÓN, NI CONCLUSIONES, NI RECOMENDACIÓN DE INVERSIÓN, NI RECOMENDACIONES GENERALES)",
                - Utiliza un lenguaje claro y profesional
                -En conclusión, quiero que seas muy detallado de porque has llegado a ese pensamiento, que datos has utilizado y que métricas has analizado.
                -EN LA TERMINAL, NO ESCRIBAS NADA, SOLO EN EL PDF. SOLO "ANÁLISIS FINANCIERO COMPLETADO" al final del análisis.

        Recuerda: estás trabajando con información financiera en tiempo real, así que valida siempre que el símbolo sea válido antes de consultar datos financieros."""

## Función para verificar si el mensaje final contiene la frase de terminación
def check_final_message(message):
    try:
        if not message or not isinstance(message, dict):
            return False
        content= message.get("content")
        if not content:
            return False
        if not isinstance(content, str):
            content = str(content)
        
        # Buscar frases de terminación
        termination_phrases = "ANÁLISIS FINANCIERO COMPLETADO"


        content_lower = content.lower()
        return termination_phrases.lower() in content_lower
        
    except Exception:
        return False
    
def track_tokens_from_response(response):
    """Extrae y cuenta tokens de la respuesta de OpenAI"""
    if hasattr(response, 'usage') and response.usage:
        usage = response.usage
        contador_tokens["prompt"] += getattr(usage, 'prompt_tokens', 0)
        contador_tokens["completion"] += getattr(usage, 'completion_tokens', 0)
    elif hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
        usage = response.response_metadata['token_usage']
        contador_tokens["prompt"] += usage.get("prompt_tokens", 0)
        contador_tokens["completion"] += usage.get("completion_tokens", 0)

async def main():
    # Instancia del agente MCP
    assistant = MCPAssistantAgent(
    name="FinancialMCPAgent",
    system_message=get_system_message(), # Mensaje del sistema que define el comportamiento del agente
    mcp_server_command="python",        # Comando para iniciar el servidor MCP
    mcp_server_args=["-m", "server"],    # Comando para iniciar el servidor MCP
    llm_config={
        "config_list": [
            {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("AZURE_API_KEY"),
                "base_url": os.getenv("azure_endpoint"),
                "api_type": "azure",
                "api_version": "2024-12-01-preview",
            }
        ]
    },
    human_input_mode="NEVER",           # Modo de entrada del usuario, en este caso nunca
    code_execution_config={"work_dir": "workspace", "use_docker": False}, # Configuración de ejecución de código
)

    # Instancia del usuario proxy
    executor = UserProxyAgent(
        name="Usuario",
        human_input_mode="NEVER",  
        code_execution_config={"work_dir": "data", "use_docker": False},
        function_map={
            "read_resource": assistant.read_resource,
            "call_tool": assistant.call_tool,
            "list_tools": assistant.list_tools,
        },
        is_termination_msg=check_final_message,

    )

    empresa = input("Escribe el nombre de la empresa que quieres analizar: ")

    prompt = (
        f"Quiero que realices un análisis financiero de la empresa '{empresa}'. "
        "Busca su símbolo bursátil, extrae sus datos financieros y genera un informe claro y muy detallado con SOLO tu analisis de la empresas."
    )

    await executor.a_initiate_chat(assistant, message=prompt, max_turns=10) #Esta función inicia una conversación entre el usuario y el asistente, pasando un mensaje inicial y estableciendo un límite de turnos.

if __name__ == "__main__":
    process = psutil.Process()
    memoria_inicial = process.memory_info().rss
    precio_usd_1k = 0.00026  # USD por 1,000 tokens
    tipo_cambio = 0.92  # USD a EUR
    precio_eur_1k = precio_usd_1k * tipo_cambio  # EUR por 1,000 tokens

    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    
    memoria_final = process.memory_info().rss

    prompt_tokens= contador_tokens["prompt"] # Los tokens del mensaje del usuario
    completion_tokens = contador_tokens["completion"] #Los tokens de la respuesta del modelo
    

    total_tokens = prompt_tokens + completion_tokens

    memoria_utilizada = (memoria_final - memoria_inicial) / (1024 ** 2)  # Convertir a MB
    execution_time = end_time - start_time
    coste = total_tokens / 1000 * precio_eur_1k

    print("Recursos utilizados")
    print(f"Memoria utilizada: {memoria_utilizada} MB")
    print(f"Tokens utilizados: {total_tokens}")
    print(f"Coste total: {coste} €")