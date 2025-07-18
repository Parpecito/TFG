import requests
import os
from dotenv import load_dotenv
from typing import List, Dict
from textblob import TextBlob
from datetime import datetime
from transformers import pipeline
import json

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
            modelo_usado = "FinBert"
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


def generar_reportes(company:str, total_news:int, resumen_sentimientos:str)-> str:
    try:
        contadores={'positivo': 0, 'negativo': 0, 'neutral': 0}

        linea_sentimientos=resumen_sentimientos.split('\n')

        for linea in linea_sentimientos:
            linea=linea.strip()
            if not linea:
                continue

            words=linea.split()
            if len(words) >= 2:
                try:
                    if words[0].isdigit():
                        cantidad=int(words[0])
                        if 'positivo' in linea.lower():
                            contadores['positivo'] = cantidad
                        elif 'negativo' in linea.lower():
                            contadores['negativo'] = cantidad
                        elif 'neutral' in linea.lower():
                            contadores['neutral'] = cantidad
                except ValueError:
                    print(f"Error al convertir '{words[0]}' a entero. Ignorando esta línea.")

    
        porcentaje_positivo = (contadores['positivo'] / total_news * 100) 
        porcentaje_negativo = (contadores['negativo'] / total_news * 100) 
        porcentaje_neutral = (contadores['neutral'] / total_news * 100) 
        
        # 3. Crear prompt para que el agente genere el reporte
        analisis_completo = f"""# Reporte de Análisis de Noticias Financieras sobre {company}

        ## 1. Resumen Ejecutivo
        El análisis de las noticias recientes sobre {company} revela un panorama basado en {total_news} noticias analizadas. La distribución de sentimientos muestra un {porcentaje_neutral:.0f}% de contenido neutral, {porcentaje_positivo:.0f}% positivo y {porcentaje_negativo:.0f}% negativo, lo que indica {"una percepción mayormente neutral" if porcentaje_neutral > 50 else "una percepción mixta"} del mercado hacia la empresa.

        ## 2. Tendencia General del Sentimiento
        - **Positivo:** {contadores['positivo']} noticias ({porcentaje_positivo:.0f}%)
        - **Negativo:** {contadores['negativo']} noticias ({porcentaje_negativo:.0f}%)
        - **Neutral:** {contadores['neutral']} noticias ({porcentaje_neutral:.0f}%)

        {"La alta proporción de noticias neutrales sugiere que el mercado mantiene una posición expectante hacia " + company if porcentaje_neutral > 50 else "La distribución equilibrada entre sentimientos positivos y negativos indica volatilidad en la percepción de " + company}.

        ## 3. Análisis de Impacto en el Mercado
        {"**BAJO IMPACTO**: La mayoría de noticias son neutrales, lo que sugiere estabilidad en la percepción." if porcentaje_neutral >= 60 else "**IMPACTO MODERADO**: Existe equilibrio entre sentimientos, requiere monitoreo." if porcentaje_negativo < 50 else "**ALTO IMPACTO**: Predominan noticias negativas, requiere atención inmediata."}

        ## 4. Recomendaciones Estratégicas
        1. **Comunicación Proactiva**: {"Mantener la estabilidad comunicacional" if porcentaje_neutral >= 60 else "Intensificar estrategia de comunicación positiva"}
        2. **Monitoreo Continuo**: Seguimiento de tendencias de sentimiento para anticipar cambios
        3. **Gestión de Riesgos**: {"Preparar estrategias para abordar potenciales crisis" if porcentaje_negativo > 30 else "Mantener estrategias defensivas"}
        4. **Capitalización de Oportunidades**: {"Aprovechar la estabilidad para impulsar iniciativas" if porcentaje_neutral >= 60 else "Reforzar aspectos positivos identificados"}

        ## 5. Puntos Clave a Monitorear
        - Evolución de la percepción pública
        - Impacto de decisiones corporativas en el sentimiento
        - Respuesta del mercado a anuncios y comunicados
        - Comparación con competidores del sector

        **Fecha de análisis**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        **Total de noticias analizadas**: {total_news}
        **Distribución final**: {contadores['positivo']} pos | {contadores['negativo']} neg | {contadores['neutral']} neu"""
        resultado={
            "agent":"Generador de reportes",
            "company": company,
            "total_news": total_news,
            "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "analisis_sentimientos":{
                "contadores": contadores,
                "total_analizado": sum(contadores.values()),
            },
            "resumen_sentimientos": resumen_sentimientos,
            "analisis_completo": analisis_completo
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_{company}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

        return f""" DATOS PROCESADOS Y ARCHIVO GENERADO

        Archivo guardado: {filename}
        Contadores: {contadores}

        PROMPT PARA REPORTE EJECUTIVO:
        {analisis_completo}

Ahora genera tu análisis completo basándote en estos datos."""
        
    except Exception as e:
        print(f"Error al generar el reporte: {e}")
        return None
