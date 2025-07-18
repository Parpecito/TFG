from dotenv import load_dotenv
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from nameclass import CompanyParams, SymbolResponse, SearchSymbolsResponse, FinancialInformationResponse, SymbolInput, YFinanceData
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

load_dotenv()


async def make_search_to_function_search_symbols(comp: CompanyParams) -> SearchSymbolsResponse:
    url = f"https://finnhub.io/api/v1/search?q={comp.company}&token={os.getenv('FINHUB_API_KEY')}"
    response = requests.get(url)
    # print(response)
    data = response.json()
    return SearchSymbolsResponse(**data)


async def search_symbols_companys(comp: CompanyParams) -> SymbolResponse:

    data = await make_search_to_function_search_symbols(comp)
    if data.count == 0 or data.result == []:
        company_mayus = comp.company.upper()
        data = await make_search_to_function_search_symbols(CompanyParams(company=company_mayus))
        if data['count'] == 0 or data['result'] == []:
            return f"No se encontraron resultados para {comp.company} en la bolsa de valores de USA."

    return SymbolResponse(symbol=data.result[0]['symbol'])


async def extract_information_company_yfinance(symbol: SymbolInput) -> YFinanceData:
    try:

        ticker = yf.Ticker(symbol)
        info = ticker.info

        historical_prices = ticker.history(
            period="1mo").to_dict(orient='records')
        return YFinanceData(
            symbol=symbol,
            company_name=info.get("longName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("marketCap"),
            pe_ratio=info.get("forwardPE"),
            dividend_yield=info.get("dividendYield"),
            beta=info.get("beta"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            historical_prices=historical_prices,

            current_price=info.get("currentPrice"),
            volume=info.get("volume"),
            avg_volume=info.get("averageVolume"),
            price_to_book=info.get("priceToBook"),
            debt_to_equity=info.get("debtToEquity"),
            return_on_equity=info.get("returnOnEquity"),
            return_on_assets=info.get("returnOnAssets"),
            profit_margin=info.get("profitMargins"),
            operating_margin=info.get("operatingMargins"),
            earnings_growth=info.get("earningsGrowth"),
            revenue_growth=info.get("revenueGrowth")


        )
    except Exception as e:
        print(
            f"Error al extraer información de {symbol} desde Yahoo Finance: {str(e)}")
        return YFinanceData(
            symbol=symbol,
            company_name=None,
            sector=None,
            industry=None,
            market_cap=None,
            pe_ratio=None,
            dividend_yield=None,
            beta=None,
            fifty_two_week_high=None,
            fifty_two_week_low=None,
            historical_prices=[],
            current_price=None,
            volume=None,
            avg_volume=None,
            price_to_book=None,
            debt_to_equity=None,
            return_on_equity=None,
            return_on_assets=None,
            profit_margin=None,
            operating_margin=None,
            earnings_growth=None,
            revenue_growth=None

        )


async def transform_data_to_pdf(data: dict) -> str:
    if not isinstance(data, dict):
        return "Los datos proporcionados no son válidos para generar un PDF."

    date = datetime.now().strftime("%d-%m-%Y_%H-%M")
    pdf_filename = f"financial_report_{date}.pdf"
    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter

    # Configuración mejorada
    left_margin = 50
    right_margin = width - 50
    max_width = right_margin - left_margin
    line_height = 18  # Aumentado para más espacio entre líneas
    section_spacing = 25  # Espacio entre secciones

    def wrap_text(text, font_name, font_size, max_width):

        c.setFont(font_name, font_size)
        words = str(text).split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            text_width = c.stringWidth(test_line, font_name, font_size)

            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = word
                else:
                    lines.append(word)
                    current_line = ""

        if current_line:
            lines.append(current_line)

        return lines

    def add_text(text, y_pos, font_name="Helvetica", font_size=10, is_title=False, is_section=False):

        nonlocal c

        if y_pos < 80:  # Nueva página si es necesario
            c.showPage()
            y_pos = height - 80

        # Selección de fuente
        if is_title:
            c.setFont("Helvetica-Bold", font_size)
        elif is_section:
            c.setFont("Helvetica-Bold", font_size)
        else:
            c.setFont(font_name, font_size)

        # Dividir texto en líneas
        font_to_use = "Helvetica-Bold" if (
            is_title or is_section) else font_name
        lines = wrap_text(text, font_to_use, font_size, max_width)

        # Dibujar cada línea
        for line in lines:
            if y_pos < 80:
                c.showPage()
                y_pos = height - 80

            c.drawString(left_margin, y_pos, line)
            y_pos -= line_height

        # Espaciado adicional según el tipo
        if is_title:
            y_pos -= 20  # Más espacio después de títulos
        elif is_section:
            y_pos -= 15  # Espacio después de secciones
        else:
            y_pos -= 5   # Espacio normal

        return y_pos

    def add_separator_line(y_pos):

        if y_pos < 80:
            c.showPage()
            y_pos = height - 80

        c.setStrokeColorRGB(0.7, 0.7, 0.7)  # Color gris
        c.setLineWidth(0.5)
        c.line(left_margin, y_pos, right_margin, y_pos)
        return y_pos - 15

    # Título principal con más espacio
    y_position = height - 80
    y_position = add_text("ANÁLISIS FINANCIERO DETALLADO", y_position,
                          font_size=20, is_title=True)
    y_position = add_separator_line(y_position)

    # Procesar cada campo del análisis con mejor formato
    for key, value in data.items():

        if key.upper() in ["SYMBOL", "SÍMBOLO"]:
            y_position = add_text(f"EMPRESA: {value}", y_position,
                                  font_size=16, is_section=True)
            y_position -= 10  # Espacio extra después del símbolo

        elif key.upper() in ["ANÁLISIS", "ANALYSIS", "RESUMEN", "RESUMEN DEL ANÁLISIS"]:
            y_position = add_text("RESUMEN DEL ANÁLISIS:", y_position,
                                  font_size=14, is_section=True)
            y_position = add_text(str(value), y_position, font_size=11)
            y_position -= section_spacing

        elif key.upper() in ["RECOMENDACIÓN", "RECOMMENDATION"]:
            y_position = add_text("RECOMENDACIÓN DE INVERSIÓN:", y_position,
                                  font_size=14, is_section=True)
            y_position = add_text(str(value), y_position, font_size=11)
            y_position -= section_spacing

        elif key.upper() in ["JUSTIFICATION", "JUSTIFICACIÓN"]:
            y_position = add_text("JUSTIFICACIÓN:", y_position,
                                  font_size=14, is_section=True)
            y_position = add_text(str(value), y_position, font_size=11)
            y_position -= section_spacing

        elif key.upper() in ["PUNTUACIÓN", "SCORE", "RATING", "CALIFICACIÓN"]:
            y_position = add_text(f"PUNTUACIÓN: {value}/10", y_position,
                                  font_size=14, is_section=True)
            y_position -= section_spacing

        else:
            # Para otros campos (datos financieros, etc.)
            section_title = key.replace('_', ' ').upper()
            y_position = add_text(f"{section_title}:", y_position,
                                  font_size=12, is_section=True)

            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    formatted_key = sub_key.replace('_', ' ').title()
                    y_position = add_text(f"  • {formatted_key}: {sub_value}",
                                          y_position, font_size=10)
            elif isinstance(value, list):
                y_position = add_text(f"  {len(value)} elementos disponibles",
                                      y_position, font_size=10)
            else:
                y_position = add_text(f"  {value}", y_position, font_size=10)

            y_position -= 15  # Espacio entre secciones

    # Línea separadora antes del footer
    y_position -= 20
    y_position = add_separator_line(y_position)

    # Footer con timestamp
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    y_position = add_text(f"Informe generado el: {timestamp}", y_position,
                          font_size=9, font_name="Helvetica-Oblique")

    c.save()
    return pdf_filename

def filter_data_10_years(data: dict) -> dict:
    if not isinstance(data, dict):
        return data

    ten_years = datetime.now() - timedelta(days=1825)  # 5 años atrás
    filter_data = {}
    current_date = datetime.now()
    for key, value in data.items():
        if key == 'metric' and isinstance(value, dict):
            filter_data[key] = value
        else:
            continue

    for key, value in data.items():
        if key == 'series' and isinstance(value, dict):
            filter_data[key] = {}
            for series_key, series_value in value.items():
                if isinstance(series_value, dict):
                    filter_data[key][series_key] = {}
                    for third_key, third_value in series_value.items():
                        if isinstance(third_value, list) and len(third_value) > 0:
                            if isinstance(third_value[0], dict) and 'period' in third_value[0]:
                                filter_list = []
                                for item in third_value:
                                    try:
                                        data_period = datetime.strptime(
                                            item['period'], '%Y-%m-%d')
                                        if ten_years <= data_period <= current_date:
                                            filter_list.append(item)
                                    except (ValueError, KeyError):
                                        continue
                                filter_data[key][series_key][third_key] = filter_list
                            else:
                                filter_data[key][series_key][third_key] = third_value
                        else:
                            filter_data[key][series_key][third_key] = third_value
                else:
                    filter_data[key][series_key] = series_value
    return filter_data


async def extract_financial_information_company(symbol: str) -> FinancialInformationResponse:
    url = f"https://finnhub.io/api/v1/stock/metric?symbol={symbol}&metric=all&token={os.getenv('FINHUB_API_KEY')}"
    response = requests.get(url)
    data = response.json()
    filter_data = filter_data_10_years(data)
    return FinancialInformationResponse(data=filter_data)
