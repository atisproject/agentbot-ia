from models import Formulario, Lead
from whatsapp_flows import enviar_mensagem_whatsapp
from database import db

def enviar_formularios_pendentes_para_lead(lead_id):
    """
    Busca e envia formulários pendentes para um lead específico.
    
    Args:
        lead_id: ID do lead para enviar os formulários
        
    Returns:
        bool: True se o envio foi bem-sucedido, False caso contrário
    """
    lead = Lead.query.get(lead_id)
    if not lead:
        return False
        
    formularios = Formulario.query.filter_by(lead_id=lead_id, status='pendente').all()
    if not formularios:
        return True  # Não há formulários pendentes
        
    for formulario in formularios:
        mensagem = f"Olá {lead.nome}, por favor preencha o formulário de {formulario.tipo.replace('_', ' ')}: {formulario.link}"
        resultado = enviar_mensagem_whatsapp(lead.telefone, mensagem)
        
        if resultado:
            formulario.status = 'enviado'
        
    db.session.commit()
    return True
