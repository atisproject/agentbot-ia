import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from app import app, db
from models import Formulario, Lead, Interacao
from ai_agent import gerar_lembrete_formulario
from notification import enviar_sms, enviar_whatsapp, notificar_administrador, notificar_formulario_pendente
from models import Configuracao

logger = logging.getLogger(__name__)

# Configuração do scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
}
executors = {
    'default': ThreadPoolExecutor(20)
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3
}

scheduler = BackgroundScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults,
    timezone='America/Sao_Paulo'
)

def verificar_formularios_pendentes():
    """
    Verifica formulários pendentes há mais de 2 dias e envia lembretes
    """
    try:
        logger.info("Iniciando verificação de formulários pendentes")
        
        data_limite = datetime.utcnow() - timedelta(days=2)
        formularios = Formulario.query.filter_by(
            status='pendente', 
            lembrete_enviado=False
        ).filter(
            Formulario.data_envio <= data_limite
        ).all()
        
        # Verificar se há uma configuração para canal preferido
        config_canal = Configuracao.query.filter_by(chave='canal_notificacao_padrao').first()
        canal_padrao = config_canal.valor if config_canal else 'sms'
        
        for formulario in formularios:
            try:
                lead = Lead.query.get(formulario.lead_id)
                if not lead:
                    continue
                
                # Determinar o canal de comunicação para este lead
                canal = 'whatsapp' if lead.fonte == 'whatsapp' else canal_padrao
                
                # Gerar mensagem de lembrete personalizada
                mensagem = gerar_lembrete_formulario(lead.id, formulario.tipo)
                
                # Enviar mensagem pelo canal apropriado
                if canal == 'whatsapp':
                    envio_sucesso = enviar_whatsapp(lead.telefone, mensagem)
                else:
                    envio_sucesso = enviar_sms(lead.telefone, mensagem)
                
                if envio_sucesso:
                    # Registrar a interação
                    nova_interacao = Interacao(
                        lead_id=lead.id,
                        mensagem=mensagem,
                        origem="sistema"
                    )
                    db.session.add(nova_interacao)
                    
                    # Atualizar o status do formulário
                    formulario.lembrete_enviado = True
                    db.session.commit()
                    
                    # Notificar administrador
                    dias_pendente = (datetime.utcnow() - formulario.data_envio).days
                    notificar_formulario_pendente(lead.nome, lead.telefone, formulario.tipo, dias_pendente)
                    
                    logger.info(f"Lembrete enviado para {lead.nome} via {canal} sobre formulário {formulario.tipo}")
            
            except Exception as e:
                logger.error(f"Erro ao processar formulário {formulario.id}: {str(e)}")
                continue
        
        logger.info(f"Verificação concluída. {len(formularios)} formulários processados.")
        
    except Exception as e:
        logger.error(f"Erro ao verificar formulários pendentes: {str(e)}")

def verificar_leads_inativos():
    """
    Verifica leads inativos há mais de 5 dias e envia mensagem de reativação
    """
    try:
        logger.info("Iniciando verificação de leads inativos")
        
        data_limite = datetime.utcnow() - timedelta(days=5)
        
        # Busca leads com última interação antes da data limite
        leads_inativos = db.session.query(Lead).join(
            Interacao, Lead.id == Interacao.lead_id
        ).filter(
            Lead.status.in_(['novo', 'em_contato']),
            Interacao.data_hora <= data_limite
        ).group_by(Lead.id).all()
        
        # Verificar se há uma configuração para canal preferido
        config_canal = Configuracao.query.filter_by(chave='canal_notificacao_padrao').first()
        canal_padrao = config_canal.valor if config_canal else 'sms'
        
        for lead in leads_inativos:
            try:
                # Verificar se já tem uma interação de reativação recente
                interacao_recente = Interacao.query.filter_by(
                    lead_id=lead.id, 
                    origem="sistema"
                ).filter(
                    Interacao.data_hora >= (datetime.utcnow() - timedelta(days=3))
                ).first()
                
                if interacao_recente:
                    continue
                
                # Determinar o canal de comunicação para este lead
                canal = 'whatsapp' if lead.fonte == 'whatsapp' else canal_padrao
                
                # Gerar mensagem de reativação
                mensagem = (
                    f"Olá {lead.nome}, sentimos sua falta! Gostaríamos de continuar "
                    f"ajudando você a alcançar seus objetivos nutricionais. "
                    f"Podemos esclarecer qualquer dúvida ou agendar uma consulta para você. "
                    f"Como podemos ajudar?"
                )
                
                # Enviar pelo canal apropriado
                if canal == 'whatsapp':
                    envio_sucesso = enviar_whatsapp(lead.telefone, mensagem)
                else:
                    envio_sucesso = enviar_sms(lead.telefone, mensagem)
                
                if envio_sucesso:
                    # Registrar a interação
                    nova_interacao = Interacao(
                        lead_id=lead.id,
                        mensagem=mensagem,
                        origem="sistema"
                    )
                    db.session.add(nova_interacao)
                    db.session.commit()
                    
                    logger.info(f"Mensagem de reativação enviada para {lead.nome} via {canal}")
            
            except Exception as e:
                logger.error(f"Erro ao processar lead inativo {lead.id}: {str(e)}")
                continue
        
        logger.info(f"Verificação concluída. {len(leads_inativos)} leads inativos processados.")
        
    except Exception as e:
        logger.error(f"Erro ao verificar leads inativos: {str(e)}")

_scheduler_iniciado = False

def iniciar_scheduler():
    """Inicia o agendador de tarefas"""
    global _scheduler_iniciado
    
    if _scheduler_iniciado:
        logger.info("Agendador de tarefas já estava iniciado")
        return
    
    try:
        # Verificar se já existem jobs com esses IDs e removê-los
        for job_id in ['verificar_formularios_pendentes', 'verificar_leads_inativos']:
            try:
                scheduler.remove_job(job_id)
                logger.info(f"Job existente removido: {job_id}")
            except:
                pass  # Job não existia
        
        scheduler.add_job(
            verificar_formularios_pendentes, 
            'interval', 
            hours=24, 
            id='verificar_formularios_pendentes',
            replace_existing=True
        )
        
        scheduler.add_job(
            verificar_leads_inativos, 
            'interval', 
            hours=24, 
            id='verificar_leads_inativos',
            replace_existing=True
        )
        
        scheduler.start()
        _scheduler_iniciado = True
        logger.info("Agendador de tarefas iniciado")
    except Exception as e:
        logger.error(f"Erro ao iniciar agendador: {str(e)}")
        # Se o erro for porque o scheduler já está rodando, apenas marcamos como iniciado
        if "already running" in str(e):
            _scheduler_iniciado = True

def parar_scheduler():
    """Para o agendador de tarefas"""
    scheduler.shutdown()
    logger.info("Agendador de tarefas parado")
