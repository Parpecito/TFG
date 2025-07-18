from pydantic import BaseModel
from typing import Optional


class CompanyParams(BaseModel):
    company: str


class SymbolResponse(BaseModel):
    symbol: str


class SearchSymbolsResponse(BaseModel):
    count: int
    result: list


class FinancialInformationResponse(BaseModel):
    data: dict


class SymbolInput(BaseModel):
    symbol: str


class YFinanceData(BaseModel):

    symbol: str  # Símbolo bursátil de la empresa
    company_name: Optional[str]  # Nombre de la empresa
    sector: Optional[str]  # Sector de la empresa
    industry: Optional[str]  # Industria de la empresa
    market_cap: Optional[float]  # Capitalización de mercado
    pe_ratio: Optional[float]  # Relación precio/ganancias
    dividend_yield: Optional[float]  # Rendimiento de dividendos
    beta: Optional[float]  # Beta (volatilidad relativa)
    fifty_two_week_high: Optional[float]  # Máximo de 52 semanas
    fifty_two_week_low: Optional[float]  # Mínimo de 52 semanas
    historical_prices: Optional[list]  # Historial de precios (último mes)

    current_price: Optional[float]  # Precio actual
    volume: Optional[int]  # Volumen de operaciones
    avg_volume: Optional[int]  # Volumen promedio
    price_to_book: Optional[float]  # Ratio precio/valor en libros
    debt_to_equity: Optional[float]  # Ratio deuda/patrimonio
    return_on_equity: Optional[float]  # ROE
    return_on_assets: Optional[float]  # ROA
    profit_margin: Optional[float]  # Margen de beneficio
    operating_margin: Optional[float]  # Margen operativo
    earnings_growth: Optional[float]  # Crecimiento de ganancias
    revenue_growth: Optional[float]  # Crecimiento de ingresos
