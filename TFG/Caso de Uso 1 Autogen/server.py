from mcp.server import Server
from mcp.types import TextContent
from pydantic import BaseModel
from nameclass import CompanyParams
from tools import (
    search_symbols_companys_USA,
    extract_financial_information_company,
    extract_information_company_yfinance,
    transform_data_to_pdf
)
from mcp.server.fastmcp import FastMCP

#https://github.com/jtanningbed/mcp-ag2-example/blob/main/server/mcp_server.py
mcp= FastMCP("mcp_server") #Define el servidor MCP con el nombre "mcp_server"

# Define los parámetros de entrada y salida para las herramientas
@mcp.tool()
async def search_symbols_companys_USA_tool(company: str) -> dict:
    params=CompanyParams(company=company)
    result = await search_symbols_companys_USA(params)
    return result.model_dump() # Devuelve el resultado como un diccionario

@mcp.tool()
async def extract_financial_information_company_tool(symbol: str) -> dict:
    result = await extract_financial_information_company(symbol)
    return result.model_dump()# Devuelve el resultado como un diccionario

@mcp.tool()
async def extract_information_company_yfinance_tool(symbol: str) -> dict:
    result = await extract_information_company_yfinance(symbol)
    return result.model_dump()# Devuelve el resultado como un diccionario

@mcp.tool()
async def transform_data_to_pdf_tool(data: dict) -> dict:
    result = await transform_data_to_pdf(data)
    return {"pdf_filename": result} # Devuelve el nombre del archivo PDF generado

#
if __name__ == "__main__":
    mcp.run(transport="stdio") # Inicia el servidor MCP utilizando la entrada/salida estándar


