import os
import json
import logging
from openai import OpenAI
from models import BaseConhecimento, Interacao, Lead
from app import db

# O modelo mais recente da OpenAI é "gpt-4o", lançado em 13 de maio de 2024.
# Não altere isso a menos que seja explicitamente solicitado pelo usuário
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

logger = logging.getLogger(__name__)

def carregar_base_conhecimento():
    """Carrega toda a base de conhecimento para o contexto do agente"""
    items = BaseConhecimento.query.all()
    base_conhecimento = []
    
    for item in items:
        base_conhecimento.append({
            "tema": item.tema,
            "conteudo": item.conteudo,
            "tipo": item.tipo
        })
    
    return base_conhecimento

def gerar_contexto_sistema():
    """Gera o contexto do sistema para o agente de IA"""
    base_conhecimento = carregar_base_conhecimento()
    
    # Formata a base de conhecimento para o contexto
    conhecimento_formatado = "\n\n".join([
        f"--- {item['tema']} ({item['tipo']}) ---\n{item['conteudo']}"
        for item in base_conhecimento
    ])
    
    contexto = """
    Você é um assistente de nutrição profissional de uma empresa especializada em nutrição.
    Seu papel é ajudar potenciais clientes, esclarecer dúvidas sobre nutrição e serviços oferecidos,
    e converter leads em clientes. Seja cordial, prestativo e profissional em todas as interações.
    
    Diretrizes:
    1. Sempre cumprimente o cliente pelo nome quando disponível
    2. Ofereça respostas claras e baseadas em evidências sobre nutrição
    3. Destaque os benefícios dos serviços da empresa
    4. Identifique oportunidades para agendar consultas ou vender produtos
    5. Nunca forneça conselhos médicos específicos - sempre indique que uma consulta personalizada é necessária
    6. Use linguagem acessível e evite jargões técnicos desnecessários
    7. Mantenha um tom amigável e profissional
    8. Quando necessário, ofereça enviar formulários de avaliação inicial
    
    A seguir está a base de conhecimento da empresa que você deve utilizar:
    
    {conhecimento}
    
    Lembre-se: seu objetivo principal é converter leads em clientes, mas sempre priorizando o bem-estar
    e as necessidades reais do cliente. Seja ético e honesto em todas as interações.
    """
    
    return contexto.format(conhecimento=conhecimento_formatado)

def agente_boas_vindas(nome):
    """Agente de boas-vindas para primeiro contato com o lead"""
    try:
        contexto_sistema = gerar_contexto_sistema()
        
        prompt_usuario = f"Escreva uma mensagem de boas-vindas para {nome}, que acabou de entrar em contato com nossa empresa de nutrição. A mensagem deve ser calorosa, profissional e despertar o interesse pelos nossos serviços de nutrição."
        
        resposta = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_sistema},
                {"role": "user", "content": prompt_usuario}
            ]
        )
        
        return resposta.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Erro ao gerar mensagem de boas-vindas: {str(e)}")
        return "Olá! Bem-vindo(a) à nossa empresa de nutrição. Como podemos ajudar você hoje?"

def processar_mensagem(lead_id, mensagem_cliente):
    """Processa a mensagem do cliente e gera uma resposta adequada"""
    try:
        # Busca o lead no banco de dados
        lead = Lead.query.get(lead_id)
        if not lead:
            return "Erro: Lead não encontrado"
        
        # Carrega o histórico de interações
        historico = Interacao.query.filter_by(lead_id=lead_id).order_by(Interacao.data_hora).all()
        mensagens_formatadas = []
        
        # Prepara o histórico de conversa para o formato da API
        for interacao in historico[-10:]:  # Limita ao histórico recente
            role = "assistant" if interacao.origem == "ia" else "user"
            mensagens_formatadas.append({"role": role, "content": interacao.mensagem})
        
        # Adiciona a mensagem atual
        mensagens_formatadas.append({"role": "user", "content": mensagem_cliente})
        
        # Gera o contexto do sistema
        contexto_sistema = gerar_contexto_sistema()
        
        # Faz a chamada para a API da OpenAI
        resposta = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_sistema},
                *mensagens_formatadas
            ]
        )
        
        conteudo_resposta = resposta.choices[0].message.content
        
        # Salva a interação do cliente
        nova_interacao_cliente = Interacao(
            lead_id=lead_id,
            mensagem=mensagem_cliente,
            origem="usuario"
        )
        db.session.add(nova_interacao_cliente)
        
        # Salva a resposta da IA
        nova_interacao_ia = Interacao(
            lead_id=lead_id,
            mensagem=conteudo_resposta,
            origem="ia"
        )
        db.session.add(nova_interacao_ia)
        db.session.commit()
        
        return conteudo_resposta
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        return "Desculpe, estamos com dificuldades para processar sua mensagem. Por favor, tente novamente mais tarde."

def gerar_lembrete_formulario(lead_id, formulario_tipo):
    """Gera um lembrete personalizado para formulários não respondidos"""
    try:
        lead = Lead.query.get(lead_id)
        if not lead:
            return "Erro: Lead não encontrado"
        
        contexto_sistema = gerar_contexto_sistema()
        
        prompt_usuario = f"""
        Crie uma mensagem de lembrete para {lead.nome} sobre o formulário de {formulario_tipo} 
        que ainda não foi preenchido. A mensagem deve ser educada, mas destacar a importância 
        de preencher o formulário para prosseguir com o atendimento nutricional.
        """
        
        resposta = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": contexto_sistema},
                {"role": "user", "content": prompt_usuario}
            ]
        )
        
        return resposta.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Erro ao gerar lembrete: {str(e)}")
        return f"Olá {lead.nome}, não se esqueça de preencher o formulário de {formulario_tipo} para continuarmos com seu atendimento nutricional."

def analisar_sentimento_cliente(mensagem):
    """Analisa o sentimento do cliente na mensagem"""
    try:
        resposta = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Você é um especialista em análise de sentimento. "
                    + "Analise o sentimento da mensagem do cliente e indique o nível de interesse "
                    + "e satisfação em uma escala de 1 a 5, bem como a probabilidade de conversão "
                    + "entre 0 e 1. Responda com JSON neste formato: "
                    + "{'interesse': número, 'satisfacao': número, 'prob_conversao': número, 'tags': ['tag1', 'tag2']}",
                },
                {"role": "user", "content": mensagem},
            ],
            response_format={"type": "json_object"},
        )
        
        resultado = json.loads(resposta.choices[0].message.content)
        return resultado
        
    except Exception as e:
        logger.error(f"Erro ao analisar sentimento: {str(e)}")
        return {
            "interesse": 3,
            "satisfacao": 3,
            "prob_conversao": 0.5,
            "tags": ["indefinido"]
        }
