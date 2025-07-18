from langchain_openai import AzureChatOpenAI
import os
from langgraph.prebuilt import create_react_agent
from mcp_server import (
    search_symbols_companys_tool,
    extract_financial_information_company_tool,
    extract_information_company_yfinance_tool,
    transform_data_to_pdf_tool
)
from typing import Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.graph import StateGraph, START, MessagesState, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage
from agents.FastMcpClient import (
    initialize_fastmcp,
    search_company_symbol_fastmcp,
    extract_finnhub_data_fastmcp,
    extract_yahoo_data_fastmcp,
    create_pdf_report_fastmcp
)


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = description or f"Transfer to {agent_name}"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """Transfer control to another agent"""
        return Command(
            goto=agent_name,
            update={"messages": state["messages"] + [
                ToolMessage(
                    content=f"Successfully transferred to {agent_name}",
                    name=name,
                    tool_call_id=tool_call_id,
                )
            ]},
            graph=Command.PARENT,
        )
    return handoff_tool
# Handoffs


transfer_to_analysis_agent = create_handoff_tool(
    agent_name="FinancialAnalysisAgent",
    description="Transferir a agente de análisis para análisis financiero y generación de resúmenes.",
)

transfer_to_visualization_agent = create_handoff_tool(
    agent_name="FinancialVisualizationAgent",
    description="Transferir a agente de visualización para generación de informes PDF.",
)


class FinancialAgent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            model="gpt-4o-mini",
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0,  # Temperatura baja para respuestas más consistentes y precisas
        )
        print(" Intentando inicializar FastMCP...")
        fastmcp_success = initialize_fastmcp()

        if fastmcp_success:
            print("FastMCP inicializado correctamente. Usando herramientas FastMCP.")
            research_tools = [
                search_company_symbol_fastmcp,
                extract_finnhub_data_fastmcp,
                extract_yahoo_data_fastmcp,
                transfer_to_analysis_agent,
            ]
            traspaso_tools = [transfer_to_visualization_agent]

            pdf_tool = create_pdf_report_fastmcp

            tool_prefix = "fastmcp"
            self.search_tool_name = "search_company_symbol_fastmcp"
            self.finnhub_tool_name = "extract_finnhub_data_fastmcp"
            self.yahoo_tool_name = "extract_yahoo_data_fastmcp"
            self.pdf_tool_name = "create_pdf_report_fastmcp"
            self.agente_investigador = create_react_agent(
                model=self.llm,
                tools=research_tools,
                name="FinancialResearchAgent",
                prompt=f"""Eres un agente de investigación financiera. EJECUTA estos pasos EN ORDEN:

                PASO 1: {self.search_tool_name}({{ "company": "<EMPRESA>" }})
                PASO 2: {self.finnhub_tool_name}({{ "symbol": "<SIMBOLO>" }})
                PASO 3: EVALUAR los datos de Finnhub:
                   - SI Finnhub devuelve datos financieros válidos → CONTINUAR al PASO 4
                   - SI Finnhub NO devuelve datos o está vacío → Ejecutar {self.yahoo_tool_name}({{ "symbol": "<SIMBOLO>" }})
                PASO 4: transfer_to_FinancialAnalysisAgent()

                IMPORTANTE: 
                - Prioriza Finnhub sobre Yahoo
                - Solo usa Yahoo si Finnhub falla o no devuelve datos útiles

                Empresa solicitada: Usa el nombre de empresa del mensaje humano."""
            )
        else:
            print("  FastMCP falló. Usando herramientas mcp_server como fallback.")
            research_tools = [
                search_symbols_companys_tool,
                extract_financial_information_company_tool,
                extract_information_company_yfinance_tool,
                transfer_to_analysis_agent,
            ]
            traspaso_tools = [transfer_to_visualization_agent]

            pdf_tool = transform_data_to_pdf_tool
            print(f" PDF Tool FastMCP - Tipo: {type(pdf_tool)}")
            print(f"   Nombre: {getattr(pdf_tool, 'name', 'Sin nombre')}")
            tool_prefix = "mcp_server"
            self.search_tool_name = "search_symbols_companys_tool"
            self.finnhub_tool_name = "extract_financial_information_company_tool"
            self.yahoo_tool_name = "extract_information_company_yfinance_tool"
            self.pdf_tool_name = "transform_data_to_pdf_tool"
            self.agente_investigador = create_react_agent(
                model=self.llm,
                tools=research_tools,
                name="FinancialResearchAgent",
                prompt=f"""Eres un agente de investigación financiera. EJECUTA estos pasos EN ORDEN:

        PASO 1: {self.search_tool_name}({{ "company": "<EMPRESA>" }})
        PASO 2: {self.finnhub_tool_name}({{ "symbol": "<SIMBOLO>" }})
        PASO 3: EVALUAR los datos de Finnhub:
           - SI Finnhub devuelve datos financieros válidos → CONTINUAR al PASO 4
           - SI Finnhub NO devuelve datos o está vacío → Ejecutar {self.yahoo_tool_name}({{ "symbol": "<SIMBOLO>" }})
        PASO 4: transfer_to_FinancialAnalysisAgent()

        IMPORTANTE: 
        - Prioriza Finnhub sobre Yahoo
        - Solo usa Yahoo si Finnhub falla o no devuelve datos útiles
        - INCLUYE TODOS los datos obtenidos en tu mensaje final
        - El agente de análisis NO tiene acceso a herramientas de datos

        Empresa solicitada: Usa el nombre de empresa del mensaje humano."""
            )

        analysis_llm = AzureChatOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            model="gpt-4o-mini",
            api_version="2024-02-01",
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature=0,
        )
        self.agente_analizador = create_react_agent(
            model=analysis_llm,
            tools=traspaso_tools,
            name="FinancialAnalysisAgent",
            prompt="""Analista financiero. Pasos:

1. ANALIZAR datos del contexto anterior

DEBER TENER SOLO ACCESO EN EL APARTADO DE TOOLS A TRASPASO_TOOLS. LAS DEMÁS HERRAMIENTAS HEREDADAS DEL AGENTE ANTERIOR NO DEBERÍAN ESTAR DISPONIBLES.
REGLAS ABSOLUTAS:
- SOLO puedes usar la herramienta: transfer_to_FinancialVisualizationAgent
- NO puedes usar herramientas de búsqueda o extracción de datos
- Si intentas usar otras herramientas, FALLARÁS
2. GENERAR JSON:
{
    "nombre_empresa": "Nombre",
    "symbol": "Símbolo", 
    "análisis": "Análisis muy detallado de la empresa",
    "puntuación": "Número del 1 al 10, criterio riguroso Y MUY ESTRICTO",
    "justificación": "Justificación de la puntuación"
}

3. EJECUTAR: transfer_to_FinancialVisualizationAgent()
PROHIBIDO: Usar search_company_symbol_fastmcp, extract_finnhub_data_fastmcp, etc.
PERMITIDO: SOLO transfer_to_FinancialVisualizationAgent
Importante:
- El analisis debe ser exhaustivo y basado en datos reales y basados en datos de Finnhub o Yahoo Finance.
- Si la situación financiera es muy mala, no dudes en poner muy mala nota.
- En tu analisis muy detallado de la empresa, quiero que incluyas los datos que has sacado para ese analisis.
- En la puntuación tienes que ser super serio con el tema de su analisis financiero
- Cuando tienes los datos, sin importar de donde vienen, tienes que recopilarlos y generar un analisis muy detallado de esos datos
- Cuando ya tienes el analisis, ejecuta la acción transfer_to_FinancialVisualizationAgent().
Los datos financieros ya están en el contexto. NO BUSQUES NUEVOS DATOS."""

        )

        self.agente_visualizador = create_react_agent(
            model=self.llm,
            tools=[pdf_tool],
            name="FinancialVisualizationAgent",
            prompt=f"""Eres un agente de visualización especializado en crear reportes financieros en formato PDF usando {tool_prefix}.

FLUJO DE TRABAJO:
1. Tomar el análisis JSON del agente anterior
2. Utilizar {self.pdf_tool_name} con los datos del análisis
3. Confirmar que el PDF se ha generado exitosamente

DIRECTRICES:
- Utilizar el análisis recibido sin modificaciones
- Aplicar {self.pdf_tool_name} con los datos proporcionados
- Una vez generado el PDF, confirmar la creación exitosa
- NO llames a la función con un diccionario vacío {{}}
- Evitar regenerar el PDF si ya se ha creado

Tu función principal es extraer el JSON del análisis y generar el PDF."""
        )

        self.graph_multiagente = self.crear_grafo_multiagente()

    def crear_grafo_multiagente(self):
        return (
            StateGraph(MessagesState)
            .add_node("FinancialResearchAgent", self.agente_investigador)
            .add_node("FinancialAnalysisAgent", self.agente_analizador)
            .add_node("FinancialVisualizationAgent", self.agente_visualizador)
            .add_edge(START, "FinancialResearchAgent")
            .compile()
        )

    async def empezar_analisis(self, company: str) -> dict:
        estado_inicial = {
            "messages": [
                HumanMessage(
                    content=(
                        f"Realizar análisis financiero completo para la empresa: {company}. "
                        "Después del análisis, transferir automáticamente utilizando transfer_to_FinancialVisualizationAgent() "
                        "para generar el informe PDF."
                    )
                )
            ]
        }

        try:
            print(f"Iniciando análisis financiero para la empresa: {company}")
            estado_final = None
            contador = 0  # Evitar bucles infinitos
            config = {"recursion_limit": 50}
            for chunk in self.graph_multiagente.stream(estado_inicial, config=config):
                contador += 1

            estado_final = chunk

            # Verificar si el agente de visualización ha generado el PDF
            if estado_final:

                return {
                    "success": True,
                    "company": company,
                    "total_steps": contador,
                    "messages": "Analais finalizado con éxito.",
                }
            else:
                raise Exception(
                    "El análisis no se completó correctamente, no se obtuvo un estado final.")

        except Exception as e:
            print(f"Error al iniciar el análisis: {e}")
            return {"success": False, "error": str(e), "company": company}
