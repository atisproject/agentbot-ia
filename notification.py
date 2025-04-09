import os
import logging
import re
from twilio.rest import Client

# Setup logging
logger = logging.getLogger(__name__)

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

def formatar_numero_internacional(numero):
    """
    Formata um número de telefone para o padrão internacional
    
    Args:
        numero (str): Número de telefone em formato local
    
    Returns:
        str: Número formatado para padrão internacional
    """
    # Remover caracteres não numéricos
    apenas_numeros = re.sub(r'\D', '', numero)
    
    # Se o número já começar com o código do país '+55', retorna como está
    if numero.startswith('+55'):
        return numero
    
    # Se começar com '55', adiciona o '+'
    if apenas_numeros.startswith('55') and len(apenas_numeros) >= 12:
        return f"+{apenas_numeros}"
    
    # Se for um número brasileiro sem o código do país, adiciona +55
    if len(apenas_numeros) >= 10:  # DDD + número (pelo menos 10 dígitos)
        return f"+55{apenas_numeros}"
    
    # Retornar o número como está se não for possível formatar
    return numero

def enviar_notificacao_whatsapp(numero_destino, mensagem):
    """
    Envia uma notificação via WhatsApp
    
    Args:
        numero_destino (str): Número do destinatário
        mensagem (str): Conteúdo da mensagem
    
    Returns:
        bool: True se a mensagem foi enviada com sucesso, False caso contrário
    """
    try:
        # Verificar se as credenciais do Twilio estão configuradas
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
            logger.error("Credenciais do Twilio não configuradas corretamente")
            return False
        
        # Formatar o número para o padrão internacional
        numero_formatado = formatar_numero_internacional(numero_destino)
        
        # Inicializar o cliente Twilio
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Número da sandbox do WhatsApp da Twilio
        from_whatsapp = f"whatsapp:{TWILIO_PHONE_NUMBER}"
        to_whatsapp = f"whatsapp:{numero_formatado}"
        
        # Enviar mensagem
        message = client.messages.create(
            body=mensagem,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        
        logger.info(f"Notificação WhatsApp enviada: {message.sid}")
        return True
    
    except Exception as e:
        logger.error(f"Erro ao enviar notificação WhatsApp: {str(e)}")
        return False

def notificar_potencial_conversao(nome_cliente, telefone_cliente, probabilidade):
    """
    Notifica o administrador sobre um lead com alta probabilidade de conversão
    
    Args:
        nome_cliente (str): Nome do cliente
        telefone_cliente (str): Telefone do cliente
        probabilidade (float): Probabilidade de conversão (0-1)
    
    Returns:
        bool: True se a notificação foi enviada com sucesso, False caso contrário
    """
    # Número do administrador (poderia ser obtido da tabela de configurações)
    numero_admin = os.environ.get("ADMIN_PHONE_NUMBER", "+5561985870944")
    
    # Formatar mensagem
    mensagem = f"""🔔 *Lead com alta probabilidade de conversão!*
    
*Cliente:* {nome_cliente}
*Telefone:* {telefone_cliente}
*Probabilidade:* {int(probabilidade * 100)}%

Recomendamos que entre em contato rapidamente com este cliente."""
    
    # Enviar notificação
    return enviar_notificacao_whatsapp(numero_admin, mensagem)

def enviar_lembrete_formulario(lead_id, tipo_formulario):
    """
    Envia um lembrete para preenchimento de formulário
    
    Args:
        lead_id (int): ID do lead
        tipo_formulario (str): Tipo do formulário pendente
    
    Returns:
        bool: True se o lembrete foi enviado com sucesso, False caso contrário
    """
    from app import db
    from models import Lead, Formulario, Interacao
    
    try:
        # Buscar informações do lead
        lead = Lead.query.get(lead_id)
        if not lead:
            logger.error(f"Lead ID {lead_id} não encontrado para envio de lembrete")
            return False
        
        # Buscar formulário
        formulario = Formulario.query.filter_by(lead_id=lead_id, tipo=tipo_formulario, status='pendente').first()
        if not formulario:
            logger.error(f"Formulário {tipo_formulario} não encontrado para o lead {lead_id}")
            return False
        
        # Formatar mensagem de lembrete
        mensagem = f"""Olá {lead.nome}, 

Notamos que você ainda não preencheu o formulário de {tipo_formulario.replace('_', ' ').title()} que enviamos.

Preencher este formulário é essencial para podermos personalizar nosso atendimento às suas necessidades.

Acesse o formulário aqui: {formulario.link}

Estamos à disposição para qualquer dúvida!"""
        
        # Enviar lembrete via WhatsApp
        enviado = enviar_notificacao_whatsapp(lead.telefone, mensagem)
        
        if enviado:
            # Atualizar contagem de lembretes
            formulario.lembrete_enviado = True
            formulario.numero_lembretes += 1
            
            # Registrar a interação no histórico
            interacao = Interacao(
                lead_id=lead_id,
                mensagem=mensagem,
                origem="sistema"
            )
            
            db.session.add(interacao)
            db.session.commit()
            
            logger.info(f"Lembrete de formulário enviado com sucesso para o lead {lead_id}")
        
        return enviado
    
    except Exception as e:
        logger.error(f"Erro ao enviar lembrete de formulário: {str(e)}")
        return False
