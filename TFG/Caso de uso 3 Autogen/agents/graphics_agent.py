import json

from agents.mcp_agent import MCPAssistantAgent


class GraphicsAgent(MCPAssistantAgent):
    def __init__(self, llm_config):
        system_message = """Eres un experto en crear reportes financieros profesionales en PDF.

Tu trabajo es:
1. RECIBIR un análisis financiero completo
2. CREAR un reporte PDF limpio y profesional
3. ESTRUCTURAR solo la información relevante:
   - Nombre de la empresa y símbolo
   - Puntuación de salud financiera
   - Análisis detallado
   - Justificación de la puntuación
   - Métricas financieras clave

REGLAS:
- Enfócate en crear un PDF ejecutivo limpio
- No incluyas datos innecesarios o técnicos
- Mantén el formato profesional y legible
- Organiza la información de manera clara

Respondes únicamente para confirmar que has recibido los datos."""

        super().__init__(
            name="GraphicsAgent",
            system_message=system_message,
            mcp_server_command="python",
            mcp_server_args=["-m", "server"],
            llm_config=llm_config,
            human_input_mode="NEVER"
        )

    def genera_pdf(self, datos_financieros: dict):
        """Genera únicamente el PDF con los datos financieros"""
        try:
            print("Generando PDF con datos financieros...")
            
            return self.crear_pdf(datos_financieros)

        except Exception as e:
            print(f"Error generando PDF: {str(e)}")
            return {
                "status": "error",
                "message": f"Error: {str(e)}"
            }

    def crear_pdf(self, datos):
        """Crea el PDF usando la herramienta MCP"""
        try:
            # Preparar datos para el PDF
            pdf_data = {
                **datos,
                "tipo_reporte": "solo_texto"
            }
            
            print("Llamando a la herramienta MCP para crear PDF...")
            
            resultado_pdf = self.call_tool(
                "transform_data_to_pdf_tool", {"data": pdf_data})
            
            if resultado_pdf and resultado_pdf.content:
                info = json.loads(resultado_pdf.content[0].text)
                return {
                    "status": "success",
                    "pdf_filename": info.get("pdf_filename", ""),
                    "message": "PDF creado exitosamente (solo texto)"
                }
            else:
                return {
                    "status": "error",
                    "message": "No se pudo crear el PDF"
                }
                
        except Exception as e:
            print(f"Error en creación de PDF: {str(e)}")
            return {
                "status": "error",
                "message": f"Error en PDF: {str(e)}"
            }