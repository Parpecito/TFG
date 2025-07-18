from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
from datetime import datetime
from typing import Dict, List
from tools import extract_information_company_newsapi, analizar_sentimiento_finbert, resumen_sentimientos
from collections import defaultdict

contador_tokens = defaultdict(int)  # Contador de tokens para prompt y completion
 
load_dotenv()
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

class Agente_Especializado:
    def __init__(self, name: str, role: str, system_prompt: str):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = AzureChatOpenAI(
            model= "gpt-4o-mini",
            api_version= "2024-02-01",
            api_key= os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint= os.getenv("AZURE_OPENAI_ENDPOINT"),
            temperature= 0.7
        )

        self.memory = [] #Implementamos memoria para almacenar resultados de procesamiento

    def process(self):
        raise NotImplementedError("Cada agente especializado debe implementar su propio método de procesamiento.")
    


class Agente_Extractor_Noticias(Agente_Especializado):
    def __init__(self):
        super().__init__(
            name="Extractor de Noticias",
            role="Agente especializado en la extracción de noticias financieras",
            system_prompt="""Eres un agente especializado en la extracción de noticias
            Tu tarea es buscar y extraer noticias financieras relevantes de las diferentes empresas
            Siempre proporciona información estructurada y relevante
            """
        )

    def process(self, company:str)-> Dict:
        try:
            print("Extraemos noticias de la empresa: ", company)
            noticias= extract_information_company_newsapi(company)
            resultado={
                "agent":self.name,
                "company": company,
                "contador":len(noticias),
                "data": noticias,
                "status": "success"
            }
            self.memory.append(resultado)
            return resultado
    

        
        except Exception as e:
            error={
                "agent": self.name,
                "company": company,
                "error": str(e),
                "status": "error"
            }
            return error
        

class Agente_Analizador_Sentimientos(Agente_Especializado):
    def __init__(self):
        super().__init__(
            name="Analizador de Sentimientos",
            role="Agente especializado en el análisis de sentimientos de noticias financieras",
            system_prompt="""Eres un agente especializado en el análisis de sentimientos
            Tu tarea es analizar el sentimiento de las noticias financieras extraídas utilizando modelos de lenguaje avanzados como FinBERT y TextBlob.
            Siempre proporciona un sentimiento estructurado y relevante, incluyendo la confianza y el modelo utilizado."""
        )
    def process(self, data_noticias: List[Dict]) -> Dict:
        try:
            print("Empezando el análisis de sentimientos...")
            sentimientos= analizar_sentimiento_finbert(data_noticias)

            resultado={
                "agent": self.name,
                "datos_sentimientos": sentimientos,
                "status": "success"
            }
            self.memory.append(resultado)
            return resultado
        
        except Exception as e:
            error={
                "agent": self.name,
                "error": str(e),
                "status": "error"
            }
            return error
        
class Agente_Resumen_Sentimientos(Agente_Especializado):
    def __init__(self):
        super().__init__(
            name="Resumen de Sentimientos",
            role="Agente especializado en resumir los sentimientos de las noticias financieras",
            system_prompt="""Eres un agente especializado en resumir sentimientos
            Tu tarea es resumir los sentimientos de las noticias financieras analizadas, proporcionando un resumen claro y conciso."""
        )

    def process(self, datos_analizados: List[Dict]) -> Dict:
        try:
            print("Empezando el resumen de sentimientos...")
            resumen= resumen_sentimientos(datos_analizados)



            resultado={
                "agent": self.name,
                "resumen": resumen,
                "status": "success"
            }
            self.memory.append(resultado)
            return resultado
        
        except Exception as e:
            error={
                "agent": self.name,
                "error": str(e),
                "status": "error"
            }
            return error

class Agente_Generador_Reportes(Agente_Especializado):
    def __init__(self):
        super().__init__(
            name="Generador de Reportes",
            role="Agente especializado en generar reportes a partir de los datos analizados",
            system_prompt="""Eres un agente especializado en generar reportes
            Tu tarea es generar un reporte claro y conciso a partir de los datos analizados y resumidos."""
        )

    def process(self, resultado_noticias: Dict, resumen_sentimientos: Dict) -> Dict:        
        try:
            print("Generando el reporte...")
       

            if resultado_noticias["status"]!="success" or resumen_sentimientos["status"]!="success":
                return {
                    "agent": self.name,
                    "error": "Error en los datos de entrada",
                    "status": "error"
                }
            summary_prompt = f"""
            Genera un reporte detallado de las noticias financieras analizadas y sus sentimientos.
            Empresa: {resultado_noticias['company']}
            Total de noticias: {resultado_noticias['contador']}
            Datos de noticias: {resultado_noticias['data']}
            Resumen de sentimientos: {resumen_sentimientos['resumen']}


            Proporciona:
            1. Resumen ejecutivo
            2. Tendencia general del sentimiento
            3. Recomendaciones basadas en el análisis
            4. Puntos clave a considerar
            """
            mensajes=[
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=summary_prompt)
            ]
            response = self.llm.invoke(mensajes)

            linea_sentimientos= resumen_sentimientos["resumen"].split('\n')
            contador_sentimientos = {'positivo': 0, 'negativo': 0, 'neutral': 0}

            for linea in linea_sentimientos:
                linea= linea.strip()
                if not linea:
                    continue
                
                words= linea.split()
                if len(words)>=2:
                    try:
                        if words[0].isdigit():
                            numero = int(words[0])
                            if 'positivo' in linea.lower():
                                contador_sentimientos['positivo'] = numero
                            elif 'negativo' in linea.lower():
                                contador_sentimientos['negativo'] = numero
                            elif 'neutral' in linea.lower():
                                contador_sentimientos['neutral'] = numero
                    except ValueError:
                        print(f"Error al convertir '{words[0]}' a número. Ignorando esta línea.")
            result={
                "agent": self.name,
                "company": resultado_noticias["company"],
                "total_news": resultado_noticias["contador"],
                "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "analisis_sentimientos":{
                    "contadores": contador_sentimientos,
                    "total_analizado": sum(contador_sentimientos.values()),
                },
                "reporte_ejecutivo": response.content,
                "status": "success"
            }
            self.memory.append(result)
            return result
            
        
        except Exception as e:
            error={
                "agent": self.name,
                "error": str(e),
                "status": "error"
            }
            return error
