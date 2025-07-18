from mcp.server.fastmcp import FastMCP
from nameclass import CompanyParams, SymbolInput

from tools import (
    search_symbols_companys,
    extract_financial_information_company,
    extract_information_company_yfinance,
    transform_data_to_pdf
)


# https://github.com/jtanningbed/mcp-ag2-example/blob/main/server/mcp_server.py

# En langchain te obligan a poner docstring en las tools

mcp = FastMCP("mcp_server")


@mcp.tool()
async def search_symbols_companys_tool(company: str) -> dict:
    """
    Busca el símbolo bursátil de una empresa utilizando su nombre.

    Args:
        company: Nombre de la empresa a buscar

    Returns:
        Diccionario con el símbolo bursátil encontrado o información de error
    """
    try:
        params = CompanyParams(company=company)
        result = search_symbols_companys(params)
        resultado = result.model_dump()
        return resultado
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def extract_financial_information_company_tool(symbol: str) -> dict:
    """
    Extrae información financiera completa desde la API de Finnhub.

    Args:
        symbol: Símbolo bursátil de la empresa

    Returns:
        Diccionario con métricas financieras y datos de Finnhub
    """
    try:
        result = extract_financial_information_company(symbol)
        resultado = result.model_dump()
        return resultado
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def extract_information_company_yfinance_tool(symbol: str) -> dict:
    """
    Extrae información financiera desde Yahoo Finance.

    Args:
        symbol: Símbolo bursátil (ej: 'AAPL', 'MSFT')

    Returns:
        Diccionario con información de la empresa, ratios financieros y datos de mercado desde Yahoo Finance
    """
    try:
        params = SymbolInput(symbol=symbol)
        result = extract_information_company_yfinance(params)
        resultado = result.model_dump()
        return resultado
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def transform_data_to_pdf_tool(data: dict) -> dict:
    """
    Genera un reporte financiero completo en formato PDF a partir de los datos de análisis.

    Args:
        data: Diccionario con datos de análisis financiero, información de la empresa y recomendaciones

    Returns:
        Diccionario con el nombre del archivo PDF generado o información de error
    """
    try:
        result = transform_data_to_pdf(data)
        return {"pdf_filename": result}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
