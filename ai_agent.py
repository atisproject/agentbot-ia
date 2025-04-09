import os
import logging
import json
import sys
from app import db
from models import Interacao, Lead, BaseConhecimento

# Setup logging
logger = logging.getLogger(__name__)

# Configuração do cliente OpenAI com tratamento de versões diferentes
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
USE_LEGACY_API = False  # Flag para indicar qual versão da API usar

try:
    logger.info("Tentando importar OpenAI SDK novo (v1+)")
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    logger.info("OpenAI client v1+ inicializado com sucesso")
except (ImportError, TypeError) as e:
    logger.warning(f"Erro ao inicializar OpenAI novo: {str(e)}")
    try:
        logger.info("Tentando importar SDK antigo do OpenAI")
        # Fallback para versões antigas
        import openai as client
        client.api_key = OPENAI_API_KEY
        USE_LEGACY_API = True
        logger.info("OpenAI client (legacy) inicializado com sucesso") 
    except Exception as e:
        logger.error(f"Erro crítico ao inicializar OpenAI: {str(e)}")
        sys.stderr.write(f"ERRO FATAL: Não foi possível inicializar OpenAI: {str(e)}")

def agente_boas_vindas(nome):
    """
    Gera mensagem de boas-vindas personalizada para um novo contato
    
    Args:
        nome (str): Nome do cliente para personalização da mensagem
    
    Returns:
        str: Mensagem de boas-vindas formatada
    """
    from whatsapp_flows import get_mensagem_boas_vindas
    
    try:
        # Usar o fluxo padrão de boas-vindas
        mensagem = get_mensagem_boas_vindas(nome)
        return mensagem
    except Exception as e:
        logger.error(f"Erro ao gerar mensagem de boas-vindas: {str(e)}")
        # Mensagem de fallback caso ocorra algum erro
        return f"Olá {nome}, bem-vindo(a) à NutriAI! Como podemos ajudar você hoje?"

def processar_mensagem(lead_id, mensagem_texto):
    """
    Processa mensagem recebida e gera resposta usando IA
    
    Args:
        lead_id (int): ID do lead no banco de dados
        mensagem_texto (str): Texto da mensagem a ser processada
    
    Returns:
        str: Resposta gerada pelo sistema
    """
    try:
        # Buscar o lead para personalização
        lead = Lead.query.get(lead_id)
        if not lead:
            logger.error(f"Lead ID {lead_id} não encontrado")
            return "Desculpe, houve um problema ao processar sua mensagem."
        
        # Buscar histórico de conversas para contexto
        historico = Interacao.query.filter_by(lead_id=lead_id).order_by(Interacao.data_hora.desc()).limit(10).all()
        historico.reverse()  # Ordenar do mais antigo para o mais recente
        
        # Preparar mensagens para o OpenAI
        mensagens = [
            {"role": "system", "content": f"""Você é um assistente virtual especializado em nutrição esportiva. 
             Seu nome é NutriAI e você está aqui para ajudar {lead.nome}. 
             Seja amigável, profissional e conciso em suas respostas.
             Seu objetivo é dar orientações gerais sobre nutrição esportiva e 
             encaminhar o cliente para nutricionistas humanos para orientações específicas.
             Mantenha suas respostas entre 2 e 4 parágrafos, a menos que seja uma resposta muito simples."""}
        ]
        
        # Adicionar histórico recente à conversa
        for interacao in historico:
            if interacao.origem == "usuario":
                mensagens.append({"role": "user", "content": interacao.mensagem})
            elif interacao.origem == "ia":
                mensagens.append({"role": "assistant", "content": interacao.mensagem})
        
        # Adicionar a mensagem atual
        mensagens.append({"role": "user", "content": mensagem_texto})
        
        # Gerar resposta usando o modelo gpt-4o (o mais recente)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        if USE_LEGACY_API:
            # Usar API antiga para versões anteriores da biblioteca
            logger.info("Usando API legada (v0) para processar mensagem")
            resposta = client.ChatCompletion.create(
                model="gpt-4-turbo",  # Modelo mais compatível com versão antiga
                messages=mensagens,
                temperature=0.7,
                max_tokens=500,
            )
        else:
            # Usar API nova (v1+)
            logger.info("Usando API moderna (v1+) para processar mensagem")  
            resposta = client.chat.completions.create(
                model="gpt-4o",
                messages=mensagens,
                temperature=0.7,
                max_tokens=500,
            )
        
        return resposta.choices[0].message.content
    
    except Exception as e:
        logger.error(f"Erro ao processar mensagem com IA: {str(e)}")
        return "Desculpe, estamos com um problema técnico no momento. Tente novamente mais tarde."

def analisar_sentimento_cliente(texto):
    """
    Analisa o sentimento do cliente e probabilidade de conversão
    
    Args:
        texto (str): Texto a ser analisado
    
    Returns:
        dict: Dicionário com análise de sentimento e probabilidade de conversão
    """
    try:
        # Chamada à API do OpenAI para análise de sentimento
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        mensagens_sentimento = [
            {"role": "system", "content": """Analise o sentimento deste texto de um cliente e retorne 
             um JSON com os seguintes campos:
             - sentimento: um número entre -1 (muito negativo) e 1 (muito positivo)
             - prob_conversao: probabilidade de conversão entre 0 e 1
             - interesse: nível de interesse do cliente entre 0 e 1
             - urgencia: indicação de urgência na resposta entre 0 e 1
             """},
            {"role": "user", "content": texto}
        ]
        
        if USE_LEGACY_API:
            # Usar API antiga para versões anteriores da biblioteca
            logger.info("Usando API legada (v0) para análise de sentimento")
            resposta = client.ChatCompletion.create(
                model="gpt-4-turbo",  # Modelo mais compatível com versão antiga
                messages=mensagens_sentimento,
                temperature=0.3,
            )
        else:
            # Usar API nova (v1+)
            logger.info("Usando API moderna (v1+) para análise de sentimento")  
            resposta = client.chat.completions.create(
                model="gpt-4o",
                messages=mensagens_sentimento,
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        
        # Processar resultado
        resultado = json.loads(resposta.choices[0].message.content)
        return resultado
    
    except Exception as e:
        logger.error(f"Erro ao analisar sentimento: {str(e)}")
        # Retornar valores neutros em caso de erro
        return {
            "sentimento": 0,
            "prob_conversao": 0.5,
            "interesse": 0.5,
            "urgencia": 0
        }
