from autogen import UserProxyAgent
from agents.agents import (
    news_api_agent,
    analyze_Sentiment_agent,
    resumidor_sentimientos_agent,
    executor_Agent,
    agente_decisidor,
    azure_llm_config
)
from autogen import GroupChat, GroupChatManager


user_proxy = UserProxyAgent(
    name="user",
    code_execution_config=False,
    human_input_mode="NEVER",
    max_consecutive_auto_reply=0

)
def elegir_speaker(ultimo_hablante, groupchat):
    if ultimo_hablante == user_proxy:
        return news_api_agent
    elif ultimo_hablante == news_api_agent:
        return executor_Agent  
    elif ultimo_hablante == executor_Agent:
        # Verificar qué agente llamó antes del executor
        messages = groupchat.messages
        if len(messages) >= 2:
            previous_caller = messages[-2].get("name", "")
            if previous_caller == "NewsAgent":
                return analyze_Sentiment_agent
            elif previous_caller == "SentimentAgent":
                return resumidor_sentimientos_agent
            elif previous_caller == "SummaryAgent":  
                return agente_decisidor
            elif previous_caller == "Impacto_Mercado":
                last_message = messages[-1].get("content", "")
                if "DATOS PROCESADOS Y ARCHIVO GENERADO" in last_message:
                    return agente_decisidor  # Volver para generar reporte ejecutivo
                else:
                    return None  # Terminar
            else:
                return None
        return analyze_Sentiment_agent
    elif ultimo_hablante == analyze_Sentiment_agent:
        return executor_Agent  
    elif ultimo_hablante == resumidor_sentimientos_agent:
        return executor_Agent  
    elif ultimo_hablante == agente_decisidor:
        
        messages = groupchat.messages
        recent_messages = [msg.get("content", "") for msg in messages[-3:]]
        
        if any("PROMPT PARA REPORTE EJECUTIVO" in msg for msg in recent_messages):
            return None  
        else:
            return executor_Agent  
    else:
        return None
    


groupchat = GroupChat(
    agents=[
    user_proxy,
    news_api_agent,
    executor_Agent,
    analyze_Sentiment_agent,
    resumidor_sentimientos_agent,
    agente_decisidor
    ], 
    messages=[], 
    max_round=18,
    speaker_selection_method=elegir_speaker,
)

manager = GroupChatManager(
    groupchat=groupchat,
    llm_config=azure_llm_config
)

