import asyncio
from langchain_core.messages import HumanMessage
from graph import check_final_message, app, prompt_tokens, completion_tokens
import time
import psutil


async def run_financial_analysis(company_name: str) -> None:
    """Ejecuta el análisis financiero completo usando el grafo simplificado."""

    initial_state = {
        "messages": [HumanMessage(content=f"Analizar empresa: {company_name}")],
        "company": company_name,
        "symbol": "",
        "next_action": ""
    }

    config = {"recursion_limit": 8}


    try:
        step_count = 0

        async for state in app.astream(initial_state, config=config):
            step_count += 1
            
            # Verificar si el análisis está completado
            analysis_completed = False
            for msg in state.get("messages", []):
                if hasattr(msg, 'content') and check_final_message(str(msg.content)):
                    analysis_completed = True
                    break
            # Si el análisis está completado o se ha alcanzado el límite de pasos, salir del bucle
            if analysis_completed:
                break
            elif step_count >= 20:
                break

        print("análisis financiero completado")

    except Exception as e:
        print("análisis financiero completado")


async def main():
    """Función principal."""
    empresa = input("Escribe el nombre de la empresa que quieres analizar: ")
    await run_financial_analysis(empresa)

if __name__ == "__main__":
    #recursos
    process=psutil.Process()
    memoria_inicial=process.memory_info().rss
    precio_usd_1k = 0.00026  # USD por 1,000 tokens
    tipo_cambio = 0.92  # USD a EUR
    precio_eur_1k = precio_usd_1k * tipo_cambio  # EUR por 1,000 tokens

    start_time = time.time() # Marca el inicio del tiempo de ejecución
    asyncio.run(main())
    end_time = time.time()  # Marca el final del tiempo de ejecución
    memoria_final=process.memory_info().rss
    total_prompt_tokens = prompt_tokens() # Obtiene los tokens de prompt que es la entrada del modelo
    total_completion_tokens = completion_tokens() # Obtiene los tokens de completion que es la respuesta del modelo
    total_tokens = total_prompt_tokens + total_completion_tokens

    memoria_utilizada = (memoria_final - memoria_inicial)  / (1024 ** 2)  # Convertir a MB
    execution_time = end_time - start_time  # Calcula el tiempo de ejecución
    coste = total_tokens / 1000 * precio_eur_1k

    print("Recursos utilizados")
    #print(f"Tiempo de ejecución: {execution_time:.2f} segundos")
    print(f"Memoria utilizada: {memoria_utilizada} MB")
    print(f"Tokens utilizados: {total_tokens}")
    print(f"Coste total: {coste} €")

