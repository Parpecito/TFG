
from nameclass import CompanyParams
from tools import (
    search_symbols_companys,
    extract_financial_information_company,
    extract_information_company_yfinance,
    transform_data_to_pdf
)
from mcp.server.fastmcp import FastMCP

# https://github.com/jtanningbed/mcp-ag2-example/blob/main/server/mcp_server.py
mcp = FastMCP("mcp_server")


@mcp.tool()
async def search_symbols_companys_tool(company: str) -> dict:
    params = CompanyParams(company=company)
    result = await search_symbols_companys(params)
    return result.model_dump()


@mcp.tool()
async def extract_financial_information_company_tool(symbol: str) -> dict:
    result = await extract_financial_information_company(symbol)
    return result.model_dump()


@mcp.tool()
async def extract_information_company_yfinance_tool(symbol: str) -> dict:
    result = await extract_information_company_yfinance(symbol)
    return result.model_dump()


@mcp.tool()
async def transform_data_to_pdf_tool(data: dict) -> dict:
    result = await transform_data_to_pdf(data)
    return {"pdf_filename": result}

if __name__ == "__main__":
    mcp.run(transport="stdio")
