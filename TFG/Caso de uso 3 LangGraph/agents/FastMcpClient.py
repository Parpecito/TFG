from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

from typing import List, Optional, Dict
import json
import asyncio
import concurrent.futures
from langchain_core.tools import tool


class FastMcpClient:
    def __init__(self, mcp_server_command: str = "python", mcp_server_args: Optional[List[str]] = None):

        self.server_params = StdioServerParameters(
            command=mcp_server_command,
            args=mcp_server_args or ["mcp_server.py"],
        )

    def call_tool(self, name: str, args: dict):
        try:
            async def _call_tool():
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(name, args)
                        print(result)

                        if not result:
                            return {"status": "success"}

                        if hasattr(result, 'content') and result.content:
                            content = result.content[0].text
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                return {"result": content}

                        return result

        except Exception as e:
            print(f"Error calling tool {name}: {e}")
            return {"error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_sync = executor.submit(lambda: asyncio.run(_call_tool()))
            return future_sync.result()

    def list_tools(self) -> List[Dict]:
        async def _list_tools():
            try:
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        tools = await session.list_tools()
                        if hasattr(tools, 'tools'):
                            return [{"name": tool.name, "description": tool.description} for tool in tools.tools]
                        else:
                            return [{"name": str(tools), "description": "No description available"}
                                    ]

            except Exception as e:
                print(f"Error listing tools: {e}")
                return []

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_sync = executor.submit(lambda: asyncio.run(_list_tools()))
            return future_sync.result()

    def read_resource(self, uri: str) -> str:
        async def read_resource():
            try:
                async with stdio_client(self.server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        content = await session.read_resource(uri)
                        return content
            except Exception as e:
                print(f"Error reading resource {uri}: {e}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future_sync = executor.submit(lambda: asyncio.run(read_resource()))
            return future_sync.result()


fastmcp_client = FastMcpClient()


def initialize_fastmcp() -> bool:
    """
    Inicializa el cliente FastMCP y verifica la conexión.

    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario
    """
    try:
        tools = fastmcp_client.list_tools()

        if isinstance(tools, list):
            for tool in tools:
                if isinstance(tool, dict):
                    name = tool.get('name', 'Desconocido')
                    desc = tool.get('description', 'Sin descripción')[:50]
                    print(f"   - {name}: {desc}...")

        return True
    except Exception as e:
        print(f"Error conectando FastMCP: {e}")
        print(f"Tipo de error: {type(e)}")
        print(f"Detalles del error: {str(e)}")
        return False


@tool
def search_company_symbol_fastmcp(company: str) -> dict:
    """
    Busca el símbolo bursátil de una empresa utilizando su nombre.

    Args:
        company: Nombre de la empresa a buscar

    Returns:
        dict: Diccionario con el símbolo bursátil encontrado o información de error
    """
    try:
        print(f" Buscando símbolo para la empresa: {company}")
        result = fastmcp_client.call_tool(
            "search_symbols_companys_tool", {"company": company})
        return result
    except Exception as e:
        return f"Error al buscar el símbolo: {e}"


@tool
def extract_finnhub_data_fastmcp(symbol: str) -> dict:
    """
    Extrae información financiera completa desde la API de Finnhub.

    Args:
        symbol: Símbolo bursátil de la empresa (ej: 'AAPL', 'MSFT')

    Returns:
        dict: Diccionario con métricas financieras y datos de Finnhub
    """
    try:

        result = fastmcp_client.call_tool(
            "extract_financial_information_company_tool", {"symbol": symbol})
        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def extract_yahoo_data_fastmcp(symbol: str) -> dict:
    """
    Extrae información financiera desde Yahoo Finance.

    Args:
        symbol: Símbolo bursátil (ej: 'AAPL', 'MSFT')

    Returns:
        dict: Diccionario con información de la empresa, ratios financieros y datos de mercado desde Yahoo Finance
    """
    try:
        result = fastmcp_client.call_tool(
            "extract_information_company_yfinance_tool", {"symbol": symbol})
        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def create_pdf_report_fastmcp(data: dict) -> dict:
    """
    Genera un reporte financiero completo en formato PDF a partir de datos de análisis.

    Args:
        data: Diccionario con datos de análisis financiero, información de la empresa y recomendaciones

    Returns:
        dict: Diccionario con el nombre del archivo PDF generado o información de error
    """
    try:
        result = fastmcp_client.call_tool(
            "transform_data_to_pdf_tool", {"data": data})
        return result
    except Exception as e:
        return {"error": str(e)}
