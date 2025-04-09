import os
import logging
from twilio.rest import Client
from database import db
from models import Lead, Interacao
from ai_agent import processar_mensagem, agente_boas_vindas, analisar_sentimento_cliente
from notification import formatar_numero_internacional, notificar_potencial_conversao

# Configurações do Twilio para WhatsApp
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

logger = logging.getLogger(__name__)

def enviar_mensagem_whatsapp(numero_destino, mensagem):
    """
    Envia uma mensagem para o WhatsApp utilizando a API do Twilio
    
    Args:
        numero_destino (str): Número de telefone de destino (formato internacional)
        mensagem (str): Conteúdo da mensagem a ser enviada
    
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    try:
        # Verificar se as credenciais do Twilio estão configuradas
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            logger.error("Credenciais do Twilio não configuradas")
            return False
        
        # Formatar o número para o padrão internacional
        numero_destino = formatar_numero_internacional(numero_destino)
        
        # Inicializar o cliente Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Para a Sandbox do Twilio WhatsApp - número configurado
        from_whatsapp_number = f'whatsapp:{TWILIO_PHONE_NUMBER}'
        
        # Enviar mensagem via WhatsApp
        message = client.messages.create(
            body=mensagem,
            from_=from_whatsapp_number,
            to=f'whatsapp:{numero_destino}'
        )
        
        logger.info(f"Mensagem WhatsApp enviada com sucesso. SID: {message.sid}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
        return False

def processar_mensagem_whatsapp(mensagem_de, mensagem_texto):
    """
    Processa uma mensagem recebida via WhatsApp
    
    Args:
        mensagem_de (str): Número do remetente
        mensagem_texto (str): Conteúdo da mensagem
    
    Returns:
        str: Resposta gerada pelo sistema
    """
    try:
        # Remover o prefixo 'whatsapp:' se existir
        if mensagem_de.startswith('whatsapp:'):
            mensagem_de = mensagem_de[9:]
        
        # Normalizar o número para consulta no banco
        telefone_normalizado = formatar_numero_internacional(mensagem_de)
        
        # Verificar se o lead já existe
        lead = Lead.query.filter_by(telefone=telefone_normalizado).first()
        
        if not lead:
            # Extrair possível nome da mensagem
            nome_extraido = extrair_nome_da_mensagem(mensagem_texto)
            nome = nome_extraido if nome_extraido else "Cliente"
            
            # Criar novo lead
            lead = Lead(
                nome=nome,
                telefone=telefone_normalizado,
                fonte='whatsapp',
                status='novo'
            )
            db.session.add(lead)
            db.session.commit()
            
            # Gerar mensagem de boas-vindas
            resposta = agente_boas_vindas(nome)
            
            # Registrar a interação
            interacao_cliente = Interacao(
                lead_id=lead.id,
                mensagem=mensagem_texto,
                origem="usuario"
            )
            db.session.add(interacao_cliente)
            
            interacao_resposta = Interacao(
                lead_id=lead.id,
                mensagem=resposta,
                origem="ia"
            )
            db.session.add(interacao_resposta)
            
        else:
            # Registrar a interação do cliente
            interacao_cliente = Interacao(
                lead_id=lead.id,
                mensagem=mensagem_texto,
                origem="usuario"
            )
            db.session.add(interacao_cliente)
            db.session.commit()
            
            # Processar a mensagem com IA
            resposta = processar_mensagem(lead.id, mensagem_texto)
            
            # Registrar a resposta
            interacao_resposta = Interacao(
                lead_id=lead.id,
                mensagem=resposta,
                origem="ia"
            )
            db.session.add(interacao_resposta)
            
            # Analisar sentimento para possível conversão
            try:
                analise = analisar_sentimento_cliente(mensagem_texto)
                # Se a probabilidade de conversão for alta, notificar administrador
                if analise.get('prob_conversao', 0) > 0.8:
                    notificar_potencial_conversao(lead.nome, lead.telefone, analise['prob_conversao'])
            except Exception as e:
                logger.error(f"Erro ao analisar sentimento: {str(e)}")
        
        db.session.commit()
        return resposta
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem WhatsApp: {str(e)}")
        return "Desculpe, estamos com problemas técnicos. Por favor, tente novamente mais tarde."

def extrair_nome_da_mensagem(mensagem):
    """
    Tenta extrair o nome do cliente da mensagem
    
    Args:
        mensagem (str): Mensagem a ser analisada
    
    Returns:
        str: Nome extraído ou None se não for encontrado
    """
    # Implementação básica, buscando por padrões comuns
    mensagem_lower = mensagem.lower()
    
    # Verificar se a mensagem começa com "olá" ou "oi" seguido por um nome
    if mensagem_lower.startswith("olá ") and len(mensagem) > 4:
        return mensagem[4:].split(" ")[0].capitalize()
    
    if mensagem_lower.startswith("oi ") and len(mensagem) > 3:
        return mensagem[3:].split(" ")[0].capitalize()
    
    # Verificar se há uma apresentação clara
    if "meu nome é " in mensagem_lower:
        idx = mensagem_lower.find("meu nome é ") + 12
        return mensagem[idx:].split(" ")[0].capitalize()
    
    if "me chamo " in mensagem_lower:
        idx = mensagem_lower.find("me chamo ") + 9
        return mensagem[idx:].split(" ")[0].capitalize()
    
    # Retornar None se não for possível extrair um nome
    return None
