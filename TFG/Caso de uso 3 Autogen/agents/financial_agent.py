from agents.mcp_agent import MCPAssistantAgent
import json


class FinancialAgent(MCPAssistantAgent):
    def __init__(self, llm_config):
        system_message = """Eres un agente especializado en la extracción de datos financieros usando herramientas MCP.

        Tu única responsabilidad es:
        1. Recibir el nombre de una empresa
        2. Usar search_symbols_companys_USA_tool para encontrar el símbolo
        3. Usar extract_financial_information_company_tool para obtener datos de Finnhub
        4. Si falla, usar extract_information_company_yfinance_tool como respaldo
        5. Validar que los datos sean completos y estructurados
        6. Pasar SOLO los datos al Summary Agent

        IMPORTANTE:
        - NO realizas análisis, SOLO extraes datos
        - Valida que el símbolo sea correcto
        - Asegúrate de que los datos estén completos
        - Responde con JSON estructurado para el siguiente agente

        Formato de respuesta:
        {
            "status": "success/error",
            "symbol": "---",
            "company_name": "Nombre",
            "data": {...datos financieros...},
            "next_agent": "summary"
        }
    """
        super().__init__(
            name="FinancialExtractDataAgent",
            system_message=system_message,
            mcp_server_command="python",
            mcp_server_args=["-m", "server"],
            llm_config=llm_config,
            human_input_mode="NEVER"
        )

    async def procesar_datos_compañia(self, compañia: str):
        try:
            # Extraer el simbolo de la compañía usando la herramienta MCP
            print(f" Procesando datos de la compañía: {compañia}")
            respuesta_simbolo = self.call_tool(
                "search_symbols_companys_tool", {"company": compañia})
            if not respuesta_simbolo:
                return {
                    "status": "error",
                    "message": "No se encontró el símbolo de la compañía."
                }

            symbol = None
            if respuesta_simbolo:
                texto = respuesta_simbolo.content[0].text
                datos_simbolo = json.loads(texto)
                symbol = datos_simbolo.get("symbol")

            if not symbol:
                return {
                    "status": "error",
                    "message": "Símbolo de la compañía no encontrado.",
                    "data": None
                }

            print(f" Símbolo encontrado: {symbol}")

            # Extraer información financiera de Finnhub
            respuesta_financiera = self.call_tool(
                "extract_financial_information_company_tool", {"symbol": symbol})
            datos_Validos = False
            if respuesta_financiera:
                try:
                    contenido = respuesta_financiera.content[0].text
                    datos_parseados = json.loads(contenido)

                    contenido_datos = datos_parseados.get("data")
                    if contenido_datos and isinstance(contenido_datos, dict):
                        if any(value for value in contenido_datos.values() if value is not None):
                            datos_Validos = True
                            print(" Datos financieros obtenidos correctamente de Finnhub.")
                        else:
                            print(" Datos financieros de Finnhub están vacíos o incompletos.")

                    else:
                        print(" Datos financieros de Finnhub no están en el formato esperado.")

                except (json.JSONDecodeError, KeyError) as e:
                    print(f" Error al parsear la respuesta de Finnhub: {e}")
            else:
                print(" No se obtuvo respuesta de Finnhub, intentando con YFinance.")

            if not datos_Validos:
                print(" Intentando obtener datos financieros de YFinance como respaldo.")
                respuesta_financiera = self.call_tool(
                    "extract_information_company_yfinance_tool", {"symbol": symbol})
                print(f"[DEBUG] Respuesta de YFinance: {respuesta_financiera}")

                if not respuesta_financiera:
                    return {
                        "status": "error",
                        "message": "No se pudo obtener información financiera de YFinance.",
                        "data": None
                    }

            return {
                "status": "success",
                "symbol": symbol,
                "company_name": compañia,
                "data": respuesta_financiera,
                "next_agent": "FinancialSummaryAgent",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error procesando datos de la compañía: {str(e)}",
                "data": None
            }
