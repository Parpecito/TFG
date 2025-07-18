from langgraph.graph import StateGraph,END
from typing import Dict, TypedDict
from agents.agents import Agente_Extractor_Noticias, Agente_Analizador_Sentimientos, Agente_Resumen_Sentimientos, Agente_Generador_Reportes

class EstadoMultiagente(TypedDict):
    company: str
    resultado_noticias: Dict
    resultado_sentimientos: Dict
    resumen_sentimientos: Dict
    generador_reportes: Dict
    error:str


class MultiAgentgraph:
    def __init__(self):
        self.news_agent= Agente_Extractor_Noticias()
        self.sentiment_agent= Agente_Analizador_Sentimientos()
        self.summary_agent= Agente_Resumen_Sentimientos()
        self.report_agent= Agente_Generador_Reportes()

        self.graph = StateGraph(EstadoMultiagente)

        self.graph.add_node("extraer_noticias", self.extraer_noticias)
        self.graph.add_node("analizar_sentimientos", self.analizar_sentimientos)
        self.graph.add_node("resumir_sentimientos", self.resumir_sentimientos)
        self.graph.add_node("generar_reporte", self.generar_reporte)

        self.graph.set_entry_point("extraer_noticias")
        self.graph.add_edge("extraer_noticias", "analizar_sentimientos")
        self.graph.add_edge("analizar_sentimientos", "resumir_sentimientos")
        self.graph.add_edge("resumir_sentimientos", "generar_reporte")
        self.graph.add_edge("generar_reporte", END)

        self.app=self.graph.compile()


    def extraer_noticias(self, state: EstadoMultiagente) ->EstadoMultiagente:
        try:
            resultado_noticias= self.news_agent.process(state["company"])
            state["resultado_noticias"]= resultado_noticias
            return state
        except Exception as e:
            state["error"] = str(e)
            return state


    def analizar_sentimientos(self, state: EstadoMultiagente) -> EstadoMultiagente:
        try:
            print("Empezando el análisis de sentimientos...")
            if state["resultado_noticias"]["status"] == "success":
                data_noticias = state["resultado_noticias"]["data"]  
                sentimientos = self.sentiment_agent.process(data_noticias)
            else:
                sentimientos = {"status": "error", "error": "Error en extracción de noticias"}
            
            state["resultado_sentimientos"] = sentimientos
            return state
        
        except Exception as e:
            state["error"] = str(e)
            return state
        
    def resumir_sentimientos(self, state: EstadoMultiagente) -> EstadoMultiagente:
        try:
            print("Empezando el resumen de sentimientos...")
            if state["resultado_sentimientos"]["status"] == "success":
                datos_analizados = state["resultado_sentimientos"]["datos_sentimientos"]  
                resumen = self.summary_agent.process(datos_analizados)
            else:
                resumen = {"status": "error", "error": "Error en análisis de sentimientos"}
            
            state["resumen_sentimientos"] = resumen
            return state
        
        except Exception as e:
            state["error"] = str(e)
            return state
        
    def generar_reporte(self, state: EstadoMultiagente) -> EstadoMultiagente:
        try:
            print("Empezando la generación del reporte...")
            report = self.report_agent.process(state['resultado_noticias'], state['resumen_sentimientos'])
            state["generador_reportes"] = report
            return state
        except Exception as e:
            state["error"] = str(e)
            return state
        
    def run(self, company: str) -> Dict:
      
        initial_state ={
            "company":company,
            "resultado_noticias":{},
            "resultado_sentimientos":{},
            "resumen_sentimientos":{},
            "generador_reportes":{},
            "error":""
        }
        
        final_state = self.app.invoke(initial_state)        
        if final_state["error"]:
            return {"status": "error", "error": final_state["error"]}
        else:
            print("Flujo de trabajo completado exitosamente.")
            return final_state["generador_reportes"]
        


