from autogen import ConversableAgent, register_function, UserProxyAgent
from agents.wrappers import (
    get_news_wrapper,
    analizar_sentimientos_wrapper,
    resumen_sentimientos_wrapper,
    generar_reportes_wrapper
                            
)
from dotenv import load_dotenv
import os
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

azure_llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",  
            "api_type": "azure",     
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "api_version": "2024-02-01",
            "base_url": os.getenv("AZURE_OPENAI_ENDPOINT")
        }
    ],
 
}
function_config = {
    "execution_timeout": 300,
    "use_docker": False
}
news_api_agent= ConversableAgent(
    name="NewsAgent",
    system_message="""Eres un agente especializado en buscar noticias financieras. 
    Cuando te pidan analizar noticias de una empresa:
    1. Extrae el nombre de la empresa del mensaje del usuario
    2. Llama a get_news_wrapper con el nombre de la empresa
    3. Solo responde con los resultados de la función
    
    Ejemplo: Si el usuario dice "Analiza las noticias recientes sobre Tesla", debes llamar get_news_wrapper con "Tesla".""",
    llm_config=azure_llm_config,
    human_input_mode="NEVER"

)

analyze_Sentiment_agent= ConversableAgent(
    name="SentimentAgent",
    system_message="""Eres un agente especializado en analizar sentimientos de noticias.

    Cuando veas que el agente anterior (Executor) ha devuelto una lista de noticias, debes:

    1. EXAMINAR el mensaje anterior que contiene la respuesta de la función get_news_wrapper
    2. EXTRAER la lista completa de noticias de esa respuesta
    3. LLAMAR a analizar_sentimientos_wrapper pasando esa lista como parámetro "news"

    FORMATO REQUERIDO:
    - El parámetro debe llamarse "news" 
    - Debe ser la lista completa de diccionarios de noticias que recibiste

    EJEMPLO:
    Si ves: [{'title': 'Noticia 1', 'description': '...', 'url': '...'}]
    Entonces llama: analizar_sentimientos_wrapper con news=[{'title': 'Noticia 1', 'description': '...', 'url': '...'}]
    Si recibes 88 noticias, HACES LAS 88
    SI RECIBES 100 NOTICIAS, HACES LAS 100
    NO llames la función con argumentos vacíos {}.""",
    llm_config=azure_llm_config,
    human_input_mode="NEVER"

)

resumidor_sentimientos_agent = ConversableAgent(
    name="SummaryAgent",

    system_message="""Eres un agente especializado en resumir análisis de sentimientos de noticias financieras.

    Cuando recibas los resultados del análisis de sentimientos del agente anterior:

    1. EXAMINAR la respuesta del Executor que contiene los resultados de analizar_sentimientos_wrapper
    2. EXTRAER la lista completa de noticias con sus sentimientos analizados
    3. LLAMAR a resumen_sentimientos_wrapper pasando esa lista como parámetro "noticias_sentimientos"

    FORMATO REQUERIDO:
    - El parámetro debe llamarse "noticias_sentimientos"
    - Debe ser la lista completa de diccionarios que incluye título, sentimiento, confianza, etc.

    EJEMPLO:
    Si ves: [{'title': 'Noticia 1', 'sentiment': 'Positivo', 'confidence': 0.8, ...}]
    Entonces llama: resumen_sentimientos_wrapper con noticias_sentimientos=[{'title': 'Noticia 1', 'sentiment': 'Positivo', 'confidence': 0.8, ...}]

    Tu función es únicamente hacer el resumen estadístico de los sentimientos.""",
    llm_config=azure_llm_config,
    human_input_mode="NEVER"
)
agente_decisidor=ConversableAgent(
    name="Impacto_Mercado",
    system_message="""Eres un agente especializado en análisis de impacto financiero y generación de reportes.

    Cuando recibas el RESUMEN DE SENTIMIENTOS del agente anterior, debes:

    **PASO 1: ANÁLISIS DE IMPACTO**
    Analiza el resumen de sentimientos y evalúa el impacto en el mercado.

    **PASO 2: GENERAR REPORTE JSON**
    Llama ÚNICAMENTE a generar_reportes_wrapper con los siguientes parámetros:
    - **company**: Extrae el nombre de la empresa del contexto de la conversación
    - **total_news**: Extrae el número total del resumen (ej: "Resumen de 68 noticias analizadas")
    - **resumen_sentimientos**: El texto completo del resumen que recibiste

    EJEMPLO DE EXTRACCIÓN:
    Si recibes: "Resumen de 68 noticias analizadas\n15 positivo\n8 negativo\n45 neutral\n..."
    Entonces debes llamar: generar_reportes_wrapper(company="Tesla", total_news=68, resumen_sentimientos="Resumen de 68...")

    NO llames ninguna otra función. Solo generar_reportes_wrapper.

    CRITERIOS DE IMPACTO:
    - **ALTO IMPACTO**: ≥50% noticias negativas
    - **IMPACTO MODERADO**: 30-50% noticias negativas
    - **BAJO IMPACTO**: ≥60% noticias neutrales

    Después de generar el reporte, proporciona un breve análisis de impacto basado en los resultados.""",
    llm_config=azure_llm_config,
    human_input_mode="NEVER"
)


executor_Agent = UserProxyAgent(
    name="Executor",
    llm_config=False,
    human_input_mode="NEVER",
    code_execution_config={
        "work_dir": ".",
        "use_docker": False
    }

)

#https://microsoft.github.io/autogen/0.2/docs/tutorial/tool-use/
register_function(
    get_news_wrapper,
    caller=news_api_agent,
    executor=executor_Agent,
    name="get_news_wrapper",
    description="Obtiene noticias financieras de una empresa específica utilizando la API de NewsAPI.",
)
register_function(
    analizar_sentimientos_wrapper,
    caller=analyze_Sentiment_agent,
    executor=executor_Agent,
    name="analizar_sentimientos_wrapper",
    description="Analiza el sentimiento de las noticias financieras utilizando el modelo FinBERT y TextBlob.",
)
register_function(
    resumen_sentimientos_wrapper,
    caller=resumidor_sentimientos_agent,
    executor=executor_Agent,
    name="resumen_sentimientos_wrapper",
    description="Resume el sentimiento de las noticias financieras.",
)

register_function(
    generar_reportes_wrapper,
    caller=agente_decisidor,
    executor=executor_Agent,
    name="generar_reportes_wrapper",
    description="Genera un reporte detallado de las noticias financieras analizadas, sus sentimientos y genera un reporte.",
)