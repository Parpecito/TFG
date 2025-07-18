from agents.graph import MultiAgentgraph
import json
import time
import psutil
from agents.agents import contador_tokens

def main():
    graph = MultiAgentgraph()

    compañia = input("Introduce el nombre de la empresa: ")
    if not compañia:
        print("No se ha introducido ninguna empresa. Saliendo del programa.")
        return
    

    try:
        resultado=graph.run(compañia)
        if resultado["status"]== "success":
            print(f"Empresa: {resultado['company']}")
            print(f"Total noticias: {resultado['total_news']}")
            print("Resumen ejecutivo")
            print(resultado['reporte_ejecutivo'])

            filename = f"reporte_{resultado['company'].replace(' ','_')}.json"
            with open(filename, 'w', encoding='utf-8') as file:
                json.dump(resultado, file, ensure_ascii=False, indent=2)
        else:
            mensaje_error = resultado.get("error", "Error desconocido")
            print(f"Error: {mensaje_error}")
            return
    except Exception as e:
        print(f"Error al ejecutar el flujo de trabajo: {e}")
        return

if __name__ == "__main__":
    process = psutil.Process()
    memoria_inicial = process.memory_info().rss
    precio_usd_1k = 0.00026  # USD por 1,000 tokens
    tipo_cambio = 0.92  # USD a EUR
    usd_to_eur = 0.92  # Exchange rate
    precio_eur_1k = precio_usd_1k * tipo_cambio  # EUR por 1,000 tokens
    start_time = time.time()
    main()
    end_time = time.time()
    tiempo_total = end_time - start_time
    prompt_tokens= contador_tokens["prompt"] # Los tokens del mensaje del usuario
    completion_tokens = contador_tokens["completion"] #Los tokens de la respuesta del modelo
    memoria_final = process.memory_info().rss
 

    total_tokens = prompt_tokens + completion_tokens

    memoria_utilizada = (memoria_final - memoria_inicial) / (1024 ** 2)  # Convertir a MB
    execution_time = end_time - start_time
    coste = total_tokens / 1000 * precio_eur_1k

    print("Recursos utilizados")
    print(f"Memoria utilizada: {memoria_utilizada} MB")
    print(f"Tokens utilizados: {total_tokens}")
    print(f"Coste total: {coste} €")
    print(f"Tiempo total de ejecución: {tiempo_total:.2f} segundos")