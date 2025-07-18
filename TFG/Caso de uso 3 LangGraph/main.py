import asyncio
from dotenv import load_dotenv
from agents.FinancialAgent import FinancialAgent
import time
from collections import defaultdict
import psutil

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

def crear_multiagente():
    return FinancialAgent()


async def main():
    """Función principal que ejecuta el análisis financiero con MCP"""

    print(" Financial Analyst Company Agent con MCP")

    # Crear analizador
    system = crear_multiagente()

    company = input("Ingrese el nombre de la empresa: ").strip()

    if not company:
        print("Debe ingresar un nombre de empresa válido")
        return

    resultado = await system.empezar_analisis(company)

    if resultado.get("success"):
        print("\n ANÁLISIS FINANCIERO MULTIAGENTE COMPLETADO")

        print(f" Empresa: {resultado['company']}")
        print(resultado)
        print(
            f" Total de pasos ejecutados: {resultado.get('total_steps', 'N/A')}")

        print(f"\nVerificar archivos generados:")
        print("   • financial_report_*.pdf")

    else:
        print("\nERROR EN ANÁLISIS MULTIAGENTE")
        print("=" * 40)
        error_msg = resultado.get('error', 'Error desconocido')
        steps = resultado.get('total_steps', 0)

        print(f"Error: {error_msg}")
        print(f"Pasos ejecutados antes del error: {steps}")

        if 'recursion' in error_msg.lower():
            print("   • Los agentes pueden estar en un bucle infinito")
            print(
                "   • Verificar que las transferencias entre agentes funcionen correctamente")
            print(
                "   • Revivar que cada agente complete su tarea y transfiera apropiadamente")

    print(" Análisis multiagente finalizado")

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
