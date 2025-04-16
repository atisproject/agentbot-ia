from models import Formulario, Lead
from whatsapp_flows import enviar_mensagem_whatsapp

def enviar_formularios_pendentes_para_lead(lead_id):
    lead = Lead.query.get(lead_id)
    if not lead:
        return False
    formularios = Formulario.query.filter_by(lead_id=lead_id, status='pendente').all()
    for f in formularios:
        mensagem = f"Olá {lead.nome}, por favor preencha o formulário de {f.tipo.replace('_', ' ')}: {f.link}"
        enviar_mensagem_whatsapp(lead.telefone, mensagem)
        f.status = 'enviado'
    from database import db
    db.session.commit()
    return True