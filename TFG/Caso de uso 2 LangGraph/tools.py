import requests
import os
from dotenv import load_dotenv
from typing import List, Dict
from textblob import TextBlob
from datetime import datetime,timedelta
from transformers import pipeline

load_dotenv()

def extract_information_company_newsapi(company:str)-> List[Dict]:
    """fecha_hoy = datetime.now()
    fecha_inicio = fecha_hoy - timedelta(days=15)
    fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
    fecha_hoy_str = fecha_hoy.strftime("%Y-%m-%d")"""

    headers = {"Authorization": f"Bearer {os.getenv('NEWSAPI_API_KEY')}"}
    url=f"https://newsapi.org/v2/everything?q={company}"
    if not os.getenv('NEWSAPI_API_KEY'):
        raise ValueError("NEWSAPI_API_KEY environment variable is not set.")
    response=requests.get(url,headers=headers)
    print(response.status_code)
    data=response.json()
    print(f" Total artículos disponibles: {data.get('totalResults', 'N/A')}")
    print(f" Artículos recibidos: {len(data.get('articles', []))}")
    datos =filter_newsapi_Data(data)
    
    
    return datos

def filter_newsapi_Data(data: dict)->List[Dict]:
    datos_filtrados = []
    articulos= data.get("articles", [])

    for articulo in articulos:
        source = articulo.get("source", {})
        source_name = source.get("name", "") if source else ""

        datos_newsapi = {
            "title": articulo.get("title", ""),
            "description": articulo.get("description", ""),
            "url": articulo.get("url", ""),
            "sourcename": source_name,
            "publishedAt": articulo.get("publishedAt", ""),
            "content": articulo.get("content", "")
        }
        datos_filtrados.append(datos_newsapi)

    return datos_filtrados

def analizar_sentimiento_finbert(items: List[Dict]) -> List[Dict]:
    resultado= []
    try:
        if not hasattr(analizar_sentimiento_finbert, 'classifier'):
            print("Cargando modelo FinBERT especializado en finanzas...")
            analizar_sentimiento_finbert.classifier = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                top_k=None
            )
            print("Modelo FinBERT cargado correctamente")
        neutral_analizada = 0
        print(f"Analizando {len(items)} noticias con FinBERT...")
        for item in items:
            try:

                texto = f"{item['title']}. {item.get('description', '')}"
                resultados = analizar_sentimiento_finbert.classifier(texto)[0]
                scores = {item['label'].lower(): item['score'] for item in resultados}

                prediccion_sentimiento = max(scores, key=scores.get)
                confianza= scores[prediccion_sentimiento]

                mapear_sentimientos={
                    "positive": "Positivo",
                    "negative": "Negativo",
                    "neutral": "Neutral"
                }
                sentimiento_final = mapear_sentimientos.get(prediccion_sentimiento, 'Neutral')
                if sentimiento_final =="Neutral":
                    # Si el sentimiento es neutral, usamos TextBlob para obtener la polaridad
                    polaritud = TextBlob(texto).sentiment.polarity
                    if polaritud > 0.2:
                        sentimiento_final = "Positivo"
                        confianza= abs(polaritud)
                        neutral_analizada+=1
                        modelo_usado= "TextBlob"
                    elif polaritud < -0.2:
                        sentimiento_final = "Negativo"
                        confianza= abs(polaritud)
                        neutral_analizada+=1
                        modelo_usado= "TextBlob"
                    else:
                        sentimiento_final = "Neutral"
                        modelo_usado= "FinBert + TextBlob"
                else:
                    modelo_usado= "FinBert"
                resultado.append({
                    "title": item["title"],
                    "sentiment": sentimiento_final,
                    "confidence": round(confianza,3),
                    "model": modelo_usado,
                    "url": item["url"],
                    "sourcename": item["sourcename"],
                    "publishedAt": item["publishedAt"],
                    "content": item["content"],
                })
            except Exception as e:
                print(f"Error al analizar el sentimiento: {e}")
                resultado.append({
                    "title": item["title"],
                    "sentiment": "Neutral",
                    "model":modelo_usado,
                    "confidence": 0.0,
                    "url": item["url"],
                    "sourcename": item["sourcename"],
                    "publishedAt": item["publishedAt"],
                    "content": item["content"],
                })

        return resultado

    except Exception as e:
        print(f"Error al cargar el modelo FinBERT: {e}")
        return None
    

def resumen_sentimientos(noticias_con_sentimientos: List[Dict]) -> str:
    resumen={"Positivo": [], "Negativo": [], "Neutral": []}

    for item in noticias_con_sentimientos:
        sentimiento= item['sentiment']
        if sentimiento in resumen:
            resumen[sentimiento].append(item['title'])

    
    total= sum(len(valor) for valor in resumen.values())
    resultado=f"Resumen de {total} noticias analizadas\n"
    for sentimiento, titulos in resumen.items():
        resultado+= f"{len(titulos)} {sentimiento.lower()}\n"

    if resumen["Positivo"]:
        resultado+=f"Ejemplo Positivo: {resumen['Positivo'][0]}\n"
    if resumen["Negativo"]:
        resultado+=f"Ejemplo Negativo: {resumen['Negativo'][0]}\n"
    if resumen["Neutral"]:
        resultado+=f"Ejemplo Neutral: {resumen['Neutral'][0]}\n"
    
    return resultado


    
