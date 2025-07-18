import os
import asyncio
from dotenv import load_dotenv
from agents.financial_agent import FinancialAgent
from agents.summary_agent import SummaryAgent
from agents.graphics_agent import GraphicsAgent
import time
import psutil
from collections import defaultdict

load_dotenv()
contador_tokens = defaultdict(int)
def track_tokens(response):
    """Extrae y cuenta tokens de la respuesta de OpenAI"""
    if hasattr(response, 'usage') and response.usage:
        usage = response.usage
        contador_tokens["prompt"] += getattr(usage, 'prompt_tokens', 0)
        contador_tokens["completion"] += getattr(usage, 'completion_tokens', 0)
    elif hasattr(response, 'response_metadata') and 'token_usage' in response.response_metadata:
        usage = response.response_metadata['token_usage']
        contador_tokens["prompt"] += usage.get("prompt_tokens", 0)
        contador_tokens["completion"] += usage.get("completion_tokens", 0)

#Intercepta automaticamente las llamadas a OpenAI para contar los tokens utilizados.
try:
    import openai
    original_create=openai.resources.chat.completions.Completions.create

    def create(self, **kwargs):
        response = original_create(self, **kwargs)
        track_tokens(response)
        return response
    
    openai.resources.chat.completions.Completions.create = create
except ImportError:
    pass

async def main():
    # Configuración del modelo
    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o-mini",
                "api_key": os.getenv("AZURE_API_KEY"),
                "base_url": os.getenv("azure_endpoint"),
                "api_type": "azure",
                "api_version": "2024-12-01-preview",
            }
        ]
    }

    # Instanciar agentes
    financial_agent = FinancialAgent(llm_config=llm_config)
    summary_agent = SummaryAgent(llm_config=llm_config)
    graphics_agent = GraphicsAgent(llm_config=llm_config)

    # Pedir empresa al usuario
    company = input("Introduce el nombre de la empresa a analizar: ").strip()
    if not company:
        print(" Debes introducir un nombre de empresa.")
        return

    # 1. Obtener datos financieros
    print("\n[1] Extrayendo datos financieros...")
    datos_financieros = await financial_agent.procesar_datos_compañia(company)
    if datos_financieros["status"] != "success":
        print(" Error obteniendo datos:", datos_financieros.get("message"))
        return

    print("Datos financieros obtenidos para:", datos_financieros.get("symbol"))

    # 2. Generar resumen/análisis
    print("\n[2] Generando análisis/resumen...")
    resumen = summary_agent.analyze_financial_data(datos_financieros)
    if resumen.get("status") == "error":
        print("Error en análisis:", resumen.get("message"))
        return

    print("Análisis generado. Puntuación:", resumen.get("puntuación"))

    # 3. Crear  y PDF
    print("\n[3] Generando  PDF...")
    resultado = graphics_agent.genera_pdf(resumen)
    if resultado["status"] == "success":
        print("PDF generado:", resultado.get("pdf_filename"))
    else:
        print("Error generando PDF:",
              resultado.get("message"))

if __name__ == "__main__":
    process=psutil.Process()
    memoria_inicial=process.memory_info().rss
    precio_usd_1k = 0.00026  # USD por 1,000 tokens
    tipo_cambio = 0.92  # USD a EUR
    precio_eur_1k = precio_usd_1k * tipo_cambio  # EUR por 1,000 tokens

    start_time = time.time() # Marca el inicio del tiempo de ejecución
    asyncio.run(main())
    end_time = time.time()  # Marca el final del tiempo de ejecución
    memoria_final=process.memory_info().rss
    total_prompt_tokens = contador_tokens["prompt"]  # Obtiene los tokens de prompt que es la entrada al modelo
    total_completion_tokens = contador_tokens["completion"]  # Obtiene los tokens de completion que es la salida del modelo
    total_tokens = total_prompt_tokens + total_completion_tokens

    memoria_utilizada = (memoria_final - memoria_inicial)  / (1024 ** 2)  # Convertir a MB
    execution_time = end_time - start_time  # Calcula el tiempo de ejecución
    coste = total_tokens / 1000 * precio_eur_1k

    print("Recursos utilizados")
    print(f"Tiempo de ejecución: {execution_time:.2f} segundos")
    print(f"Memoria utilizada: {memoria_utilizada} MB")
    print(f"Tokens utilizados: {total_tokens}")
    print(f"Coste total: {coste} €")