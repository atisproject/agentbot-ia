import json
import logging
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db
from models import User, Lead, Interacao, Formulario, ProdutoNutricao, BaseConhecimento, Configuracao
from ai_agent import agente_boas_vindas, processar_mensagem, analisar_sentimento_cliente
from notification import enviar_sms, enviar_whatsapp, notificar_administrador, notificar_novo_lead, notificar_potencial_conversao
from scheduler import iniciar_scheduler

# Iniciar o scheduler quando a aplicação iniciar somente em produção
# Usando variável para evitar múltiplas inicializações
_scheduler_iniciado = False

def init_scheduler():
    global _scheduler_iniciado
    if not _scheduler_iniciado:
        try:
            with app.app_context():
                iniciar_scheduler()
                _scheduler_iniciado = True
        except Exception as e:
            logger.error(f"Erro ao iniciar o scheduler: {str(e)}")
            
# Não iniciar o scheduler aqui para evitar conflitos - será iniciado
# quando o servidor estiver completamente carregado

logger = logging.getLogger(__name__)

# Rotas de autenticação
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos', 'danger')
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('login'))

# Rotas principais da aplicação
@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # Formulário de contato inicial
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email', '')
        
        if not nome or not telefone:
            flash('Por favor, preencha os campos obrigatórios', 'danger')
            return redirect(url_for('index'))
        
        # Verifica se o lead já existe
        lead_existente = Lead.query.filter_by(telefone=telefone).first()
        
        if lead_existente:
            lead = lead_existente
            lead.nome = nome  # Atualiza o nome caso tenha mudado
            lead.email = email
            lead.atualizado_em = datetime.utcnow()
        else:
            # Cria um novo lead
            lead = Lead(
                nome=nome,
                telefone=telefone,
                email=email,
                fonte='site',
                status='novo'
            )
            db.session.add(lead)
        
        db.session.commit()
        
        # Gera mensagem de boas-vindas
        mensagem_boas_vindas = agente_boas_vindas(nome)
        
        # Registra a interação
        interacao = Interacao(
            lead_id=lead.id,
            mensagem=mensagem_boas_vindas,
            origem="ia"
        )
        db.session.add(interacao)
        db.session.commit()
        
        # Define a fonte preferencial de contato do lead
        fonte = request.form.get('fonte', 'site')
        
        # Envia a mensagem de boas-vindas pelo canal apropriado
        if fonte == 'whatsapp':
            enviar_whatsapp(telefone, mensagem_boas_vindas)
        else:
            enviar_sms(telefone, mensagem_boas_vindas)
        
        # Notifica o administrador
        notificar_novo_lead(nome, telefone)
        
        flash('Obrigado pelo seu contato! Em breve entraremos em contato.', 'success')
        return redirect(url_for('index'))
    
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    # Estatísticas gerais
    total_leads = Lead.query.count()
    leads_novos = Lead.query.filter_by(status='novo').count()
    leads_convertidos = Lead.query.filter_by(status='convertido').count()
    taxa_conversao = (leads_convertidos / total_leads * 100) if total_leads > 0 else 0
    
    # Interações recentes
    interacoes_recentes = db.session.query(
        Interacao, Lead
    ).join(
        Lead, Interacao.lead_id == Lead.id
    ).order_by(
        Interacao.data_hora.desc()
    ).limit(10).all()
    
    # Formulários pendentes
    formularios_pendentes = db.session.query(
        Formulario, Lead
    ).join(
        Lead, Formulario.lead_id == Lead.id
    ).filter(
        Formulario.status == 'pendente'
    ).order_by(
        Formulario.data_envio.desc()
    ).all()
    
    return render_template(
        'dashboard.html',
        total_leads=total_leads,
        leads_novos=leads_novos,
        leads_convertidos=leads_convertidos,
        taxa_conversao=round(taxa_conversao, 2),
        interacoes_recentes=interacoes_recentes,
        formularios_pendentes=formularios_pendentes
    )

@app.route('/leads')
@login_required
def leads():
    todos_leads = Lead.query.order_by(Lead.criado_em.desc()).all()
    return render_template('leads.html', leads=todos_leads)

@app.route('/lead/<int:lead_id>')
@login_required
def detalhe_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    interacoes = Interacao.query.filter_by(lead_id=lead_id).order_by(Interacao.data_hora).all()
    formularios = Formulario.query.filter_by(lead_id=lead_id).all()
    return render_template('detalhe_lead.html', lead=lead, interacoes=interacoes, formularios=formularios)

@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    if request.method == 'POST':
        # Atualiza as configurações
        for chave, valor in request.form.items():
            if chave.startswith('config_'):
                nome_config = chave[7:]  # Remove o prefixo 'config_'
                config = Configuracao.query.filter_by(chave=nome_config).first()
                
                if config:
                    config.valor = valor
                else:
                    nova_config = Configuracao(
                        chave=nome_config,
                        valor=valor,
                        descricao=f"Configuração {nome_config}"
                    )
                    db.session.add(nova_config)
        
        db.session.commit()
        flash('Configurações atualizadas com sucesso', 'success')
        return redirect(url_for('configuracoes'))
    
    configs = Configuracao.query.all()
    return render_template('configuracoes.html', configuracoes=configs)

@app.route('/base_conhecimento', methods=['GET', 'POST'])
@login_required
def base_conhecimento():
    if request.method == 'POST':
        tema = request.form.get('tema')
        conteudo = request.form.get('conteudo')
        tipo = request.form.get('tipo')
        
        if not tema or not conteudo or not tipo:
            flash('Por favor, preencha todos os campos', 'danger')
            return redirect(url_for('base_conhecimento'))
        
        if 'item_id' in request.form and request.form.get('item_id'):
            # Atualizar item existente
            item_id = int(request.form.get('item_id'))
            item = BaseConhecimento.query.get(item_id)
            
            if item:
                item.tema = tema
                item.conteudo = conteudo
                item.tipo = tipo
                item.atualizado_em = datetime.utcnow()
                flash('Item atualizado com sucesso', 'success')
            else:
                flash('Item não encontrado', 'danger')
        else:
            # Criar novo item
            novo_item = BaseConhecimento(
                tema=tema,
                conteudo=conteudo,
                tipo=tipo
            )
            db.session.add(novo_item)
            flash('Item adicionado com sucesso', 'success')
        
        db.session.commit()
        return redirect(url_for('base_conhecimento'))
    
    items = BaseConhecimento.query.order_by(BaseConhecimento.tema).all()
    return render_template('knowledge_base.html', items=items)

@app.route('/api/enviar_mensagem', methods=['POST'])
def api_enviar_mensagem():
    """API para receber mensagens de clientes e processá-las"""
    data = request.json
    
    if not data or 'telefone' not in data or 'mensagem' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    
    telefone = data['telefone']
    mensagem = data['mensagem']
    canal = data.get('canal', 'sms')  # Padrão é SMS se não especificado
    
    # Busca o lead pelo telefone
    lead = Lead.query.filter_by(telefone=telefone).first()
    
    if not lead:
        return jsonify({'status': 'erro', 'mensagem': 'Lead não encontrado'}), 404
    
    # Processa a mensagem e obtém resposta
    resposta = processar_mensagem(lead.id, mensagem)
    
    # Envia a resposta pelo canal especificado
    if canal.lower() == 'whatsapp':
        envio_sucesso = enviar_whatsapp(telefone, resposta)
    else:
        envio_sucesso = enviar_sms(telefone, resposta)
    
    # Analisa o sentimento da mensagem
    try:
        analise = analisar_sentimento_cliente(mensagem)
        
        # Se a probabilidade de conversão for alta, notifica o administrador
        if analise.get('prob_conversao', 0) > 0.8:
            notificar_potencial_conversao(lead.nome, lead.telefone, analise['prob_conversao'])
    except Exception as e:
        logger.error(f"Erro ao analisar sentimento: {str(e)}")
    
    return jsonify({
        'status': 'sucesso',
        'resposta': resposta,
        'enviado': envio_sucesso,
        'canal': canal
    })

@app.route('/api/atualizar_lead', methods=['POST'])
@login_required
def api_atualizar_lead():
    """API para atualizar dados de um lead"""
    data = request.json
    
    if not data or 'lead_id' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    
    lead_id = data['lead_id']
    lead = Lead.query.get(lead_id)
    
    if not lead:
        return jsonify({'status': 'erro', 'mensagem': 'Lead não encontrado'}), 404
    
    # Atualiza os campos enviados
    if 'nome' in data:
        lead.nome = data['nome']
    if 'email' in data:
        lead.email = data['email']
    if 'telefone' in data:
        lead.telefone = data['telefone']
    if 'status' in data:
        lead.status = data['status']
    
    lead.atualizado_em = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'status': 'sucesso', 'mensagem': 'Lead atualizado com sucesso'})

@app.route('/api/enviar_formulario', methods=['POST'])
@login_required
def api_enviar_formulario():
    """API para enviar um formulário para um lead"""
    data = request.json
    
    if not data or 'lead_id' not in data or 'tipo' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    
    lead_id = data['lead_id']
    tipo = data['tipo']
    canal = data.get('canal', 'sms')  # Padrão é SMS se não especificado
    
    lead = Lead.query.get(lead_id)
    
    if not lead:
        return jsonify({'status': 'erro', 'mensagem': 'Lead não encontrado'}), 404
    
    # Cria o formulário
    formulario = Formulario(
        lead_id=lead_id,
        tipo=tipo,
        status='pendente'
    )
    db.session.add(formulario)
    db.session.commit()
    
    # Envia mensagem para o cliente
    mensagem = (
        f"Olá {lead.nome}, enviamos um formulário de {tipo} para você. "
        f"Por favor, preencha-o para que possamos oferecer um atendimento personalizado. "
        f"Acesse o link: https://nutriai.com.br/formulario/{formulario.id}"
    )
    
    # Enviar pelo canal especificado
    if canal.lower() == 'whatsapp':
        envio_sucesso = enviar_whatsapp(lead.telefone, mensagem)
    else:
        envio_sucesso = enviar_sms(lead.telefone, mensagem)
    
    # Registra a interação
    interacao = Interacao(
        lead_id=lead_id,
        mensagem=mensagem,
        origem="sistema"
    )
    db.session.add(interacao)
    db.session.commit()
    
    return jsonify({
        'status': 'sucesso',
        'formulario_id': formulario.id,
        'mensagem': 'Formulário enviado com sucesso',
        'enviado': envio_sucesso,
        'canal': canal
    })

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def erro_interno(e):
    return render_template('500.html'), 500
