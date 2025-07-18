from tools import (
    extract_information_company_newsapi,
    analizar_sentimiento_finbert,
    resumen_sentimientos,
    generar_reportes
)
from typing import List, Dict

def get_news_wrapper(company: str)->List[Dict]:
    return extract_information_company_newsapi(company)

def analizar_sentimientos_wrapper(news: List[dict]) -> List[Dict]:
    return analizar_sentimiento_finbert(news)


def resumen_sentimientos_wrapper(noticias_sentimientos: List[Dict]) -> str:
    return resumen_sentimientos(noticias_sentimientos)

def generar_reportes_wrapper(company:str, total_news:int, resumen_sentimientos:str)->str:
    return generar_reportes(company, total_news, resumen_sentimientos)

