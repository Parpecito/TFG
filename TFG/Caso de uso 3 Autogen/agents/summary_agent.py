from autogen import ConversableAgent
import json


class SummaryAgent(ConversableAgent):
    def __init__(self, llm_config):
        system_message = """Eres un analista financiero experto.

Recibes datos financieros de una empresa y debes crear un análisis completo.

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{
    "nombre_empresa": "nombre de la empresa",
    "symbol": "símbolo bursátil", 
    "análisis": "análisis detallado de las métricas financieras que has recibido. El análisis me gustaría que fuera muy deetallado",
    "puntuación": "número del 1 al 10 que hablará de la salud financiera de la empresa, siendo 1 muy mala y 10 excelente" Si no hay datos suficientes, usa 0,
    "justificación": "explicación de por qué esa puntuación basada en los datoss",
    "métricas_clave": {datos financieros organizados},
}

IMPORTANTE: 
- Tu análisis debe ser objetivo y basado únicamente en los datos proporcionados.
- La puntuación debe reflejar la salud financiera de la empresa.
- No debes hacer recomendaciones de compra/venta, solo análisis y que sea muy detallado.
- Las métricas clave deben ser organizadas y fáciles de entender, para que el siguiente agente pueda generar gráficos mucho más facilmente basandose en ellas.
Responde SOLO con JSON válido, sin texto adicional ni markdown.
Solo analiza los números, NO des recomendaciones de compra/venta."""

        super().__init__(
            name="FinancialSummaryAgent",
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode="NEVER"
        )

    def analyze_financial_data(self, financial_data):
        """Envía los datos al LLM y recibe el análisis en JSON"""
        try:
            datos_analizar = {}
            datos_analizar["symbol"] = financial_data.get("symbol")
            print(f"Símbolo a analizar: {datos_analizar['symbol']}")
            datos_analizar["company_name"] = financial_data.get("company_name")
            print(
                f"Nombre de la empresa a analizar: {datos_analizar['company_name']}")
            datos = datos_analizar["data"] = financial_data.get("data")
            print(f"Datos financieros a analizar: {datos}")

            if datos and hasattr(datos, 'content'):
                print(
                    f"Datos financieros encontrados: {datos.content}")
                contenido = datos.content[0].text

                try:
                    contenido_parseado = json.loads(contenido)
                    print("JSON parseado correctamente.")
                    datos_analizar["data"] = contenido_parseado
                    print(f"Datos financieros parseados: {datos_analizar['data']}")
                except json.JSONDecodeError:
                    datos_analizar["data"] = contenido
            else:
                datos_analizar["data"] = "No se encontraron datos financieros válidos."
            # Convertir datos a string para enviar
            data_text = f"Analiza estos datos financieros y responde SOLO con JSON:\n\n{json.dumps(datos_analizar, indent=2)}"

            messages = [{"role": "user", "content": data_text}]
            print(f"Mensajes enviados al LLM: {messages}")

            # Generar respuesta
            response = self.generate_reply(messages)

            # Limpiar la respuesta
            if isinstance(response, dict):
                # Si ya es un dict, devolverlo
                return response

            # Si es string, intentar parsear JSON
            response_text = str(response).strip()

            # Parsear JSON
            result = json.loads(response_text)
            print(
                f" Análisis completado para {result.get('symbol', 'empresa')}")
            return result

        except json.JSONDecodeError as e:
            print(f" Error parseando JSON: {e}")
            print(f"Respuesta recibida: {response_text[:200]}...")
            return {
                "status": "error",
                "message": f"Error parsing JSON: {str(e)}"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error en análisis: {str(e)}"
            }
