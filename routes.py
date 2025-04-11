import logging
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import app
from database import db
from models import User, Lead, Interacao, Formulario, Configuracao, BaseConhecimento

# Setup logging
logger = logging.getLogger(__name__)

# Página inicial
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Processar formulário de contato na página inicial
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email', '')
        
        if not nome or not telefone:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('index'))
        
        # Verificar se o lead já existe
        lead_existente = Lead.query.filter_by(telefone=telefone).first()
        if lead_existente:
            lead_existente.nome = nome
            lead_existente.email = email
            lead_existente.fonte = 'site'
            db.session.commit()
            flash('Seus dados foram atualizados. Um de nossos especialistas entrará em contato.', 'success')
        else:
            # Criar novo lead
            novo_lead = Lead(
                nome=nome,
                telefone=telefone,
                email=email,
                fonte='site',
                status='novo'
            )
            db.session.add(novo_lead)
            db.session.commit()
            flash('Seu contato foi recebido. Um de nossos especialistas entrará em contato em breve.', 'success')
        
        return redirect(url_for('index'))
    
    return render_template('index.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Nome de usuário ou senha incorretos.', 'danger')
    
    return render_template('index.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('index'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Estatísticas para o dashboard
    total_leads = Lead.query.count()
    leads_novos = Lead.query.filter_by(status='novo').count()
    leads_convertidos = Lead.query.filter_by(status='convertido').count()
    
    # Calcular taxa de conversão
    taxa_conversao = 0
    if total_leads > 0:
        taxa_conversao = round((leads_convertidos / total_leads) * 100, 1)
    
    # Formulários pendentes
    formularios_pendentes = []
    for formulario in Formulario.query.filter_by(status='pendente').order_by(Formulario.data_envio.desc()).all():
        lead = Lead.query.get(formulario.lead_id)
        if lead:
            formularios_pendentes.append((formulario, lead))
    
    # Interações recentes
    interacoes_recentes = []
    for interacao in Interacao.query.order_by(Interacao.data_hora.desc()).limit(20).all():
        lead = Lead.query.get(interacao.lead_id)
        if lead:
            interacoes_recentes.append((interacao, lead))
    
    return render_template('dashboard.html',
                          total_leads=total_leads,
                          leads_novos=leads_novos,
                          leads_convertidos=leads_convertidos,
                          taxa_conversao=taxa_conversao,
                          formularios_pendentes=formularios_pendentes,
                          interacoes_recentes=interacoes_recentes)

# Gestão de leads
@app.route('/leads')
@login_required
def leads():
    # Buscar todos os leads, ordenados por data de criação (mais recentes primeiro)
    todos_leads = Lead.query.order_by(Lead.criado_em.desc()).all()
    return render_template('leads.html', leads=todos_leads)

# Detalhes do lead
@app.route('/lead/<int:lead_id>')
@login_required
def detalhe_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    interacoes = Interacao.query.filter_by(lead_id=lead_id).order_by(Interacao.data_hora).all()
    formularios = Formulario.query.filter_by(lead_id=lead_id).all()
    
    return render_template('detalhe_lead.html', 
                          lead=lead, 
                          interacoes=interacoes,
                          formularios=formularios)

# API para gerenciar leads
@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
@login_required
def atualizar_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    data = request.json
    
    if 'nome' in data:
        lead.nome = data['nome']
    if 'email' in data:
        lead.email = data['email']
    if 'telefone' in data:
        lead.telefone = data['telefone']
    if 'status' in data:
        lead.status = data['status']
    if 'fonte' in data:
        lead.fonte = data['fonte']
    if 'observacoes' in data:
        lead.observacoes = data['observacoes']
    
    db.session.commit()
    
    return jsonify({'status': 'sucesso', 'mensagem': 'Lead atualizado com sucesso'})

# API para criar novo lead
@app.route('/api/formulario/enviar', methods=['POST'])
def enviar_formulario():
    data = request.json
    if not data or 'nome' not in data or 'telefone' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    
    novo_formulario = Formulario(
        lead_id=data.get('lead_id'),
        tipo='contato',
        link='',
        status='pendente'
    )
    db.session.add(novo_formulario)
    db.session.commit()
    
    return jsonify({'status': 'sucesso', 'mensagem': 'Formulário enviado com sucesso'})

@app.route('/api/leads', methods=['POST'])
@login_required
def criar_lead():
    data = request.json
    
    if not data or 'nome' not in data or 'telefone' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400
    
    # Verificar se o lead já existe
    lead_existente = Lead.query.filter_by(telefone=data['telefone']).first()
    if lead_existente:
        return jsonify({'status': 'erro', 'mensagem': 'Lead com este telefone já existe'}), 400
    
    novo_lead = Lead(
        nome=data['nome'],
        telefone=data['telefone'],
        email=data.get('email', ''),
        fonte=data.get('fonte', 'manual'),
        status=data.get('status', 'novo'),
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(novo_lead)
    db.session.commit()
    
    return jsonify({
        'status': 'sucesso', 
        'mensagem': 'Lead criado com sucesso',
        'lead_id': novo_lead.id
    }), 201

# Base de conhecimento
@app.route('/base-conhecimento', methods=['GET', 'POST'])
@login_required
def base_conhecimento():
    if request.method == 'POST':
        categoria = request.form.get('categoria')
        pergunta = request.form.get('pergunta')
        resposta = request.form.get('resposta')
        palavras_chave = request.form.get('palavras_chave', '')
        
        if not categoria or not pergunta or not resposta:
            flash('Por favor, preencha todos os campos obrigatórios.', 'danger')
            return redirect(url_for('base_conhecimento'))
        
        novo_conhecimento = BaseConhecimento(
            categoria=categoria,
            pergunta=pergunta,
            resposta=resposta,
            palavras_chave=palavras_chave
        )
        
        db.session.add(novo_conhecimento)
        db.session.commit()
        
        flash('Conhecimento adicionado com sucesso!', 'success')
        return redirect(url_for('base_conhecimento'))
    
    # Buscar todos os itens da base de conhecimento
    conhecimentos = BaseConhecimento.query.order_by(BaseConhecimento.categoria, BaseConhecimento.pergunta).all()
    
    return render_template('base_conhecimento.html', conhecimentos=conhecimentos)

# Configurações
@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    if request.method == 'POST':
        # Processar atualizações de configuração
        for chave, valor in request.form.items():
            if chave.startswith('config_'):
                chave_real = chave[7:]  # Remover o prefixo 'config_'
                
                # Verificar se a configuração já existe
                config = Configuracao.query.filter_by(chave=chave_real).first()
                if config:
                    config.valor = valor
                else:
                    nova_config = Configuracao(chave=chave_real, valor=valor)
                    db.session.add(nova_config)
        
        db.session.commit()
        flash('Configurações atualizadas com sucesso.', 'success')
        return redirect(url_for('configuracoes'))
    
    # Buscar todas as configurações
    configuracoes = Configuracao.query.all()
    
    return render_template('configuracoes.html', configuracoes=configuracoes)

# Rota para manipular erros 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Rota para manipular erros 500
@app.errorhandler(500)
def server_error(e):
    logger.error(f"Erro 500: {str(e)}")
    return render_template('500.html'), 500
