from agents.groupchat import manager, user_proxy
import time
import psutil
from agents.agents import contador_tokens

def main():
   company= input("Introduceme la compañia: ")
   mensaje= f"Analiza las noticias recientes sobre {company}."

   user_proxy.initiate_chat(manager, message=mensaje)

if __name__ == "__main__":
   process = psutil.Process()
   memoria_inicial = process.memory_info().rss
   precio_usd_1k = 0.00026  # USD por 1,000 tokens
   tipo_cambio = 0.92  # USD a EUR
   precio_eur_1k = precio_usd_1k * tipo_cambio  # EUR por 1,000 tokens

   start_time = time.time()
   main()
   end_time = time.time()
   
   execution_time = end_time - start_time
   prompt_tokens = contador_tokens["prompt"]
   completion_tokens = contador_tokens["completion"]
   memoria_final = process.memory_info().rss

   total_tokens = prompt_tokens + completion_tokens
   memoria_utilizada = (memoria_final - memoria_inicial) / (1024 ** 2)
   coste = total_tokens / 1000 * precio_eur_1k

   print("Recursos utilizados")
   print(f"Tiempo de ejecución: {execution_time:.2f} segundos")
   print(f"Memoria utilizada: {memoria_utilizada} MB")
   print(f"Tokens utilizados: {total_tokens}")
   print(f"Coste total: {coste} €")