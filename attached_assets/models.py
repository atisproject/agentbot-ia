from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    leads = db.relationship('Lead', backref='atendente', lazy=True)
    
    def __repr__(self):
        return f'<Usuário {self.username}>'

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    telefone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='novo')  # novo, em_contato, convertido, perdido
    fonte = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    interacoes = db.relationship('Interacao', backref='lead', lazy=True)
    formularios = db.relationship('Formulario', backref='lead', lazy=True)
    
    def __repr__(self):
        return f'<Lead {self.nome}>'

class Interacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    origem = db.Column(db.String(20), nullable=False)  # ia, usuario, sistema
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Interação #{self.id} - Lead {self.lead_id}>'

class Formulario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # avaliacao_fisica, anamnese, etc
    status = db.Column(db.String(20), default='pendente')  # pendente, respondido, expirado
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_resposta = db.Column(db.DateTime, nullable=True)
    lembrete_enviado = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Formulário {self.tipo} - Lead {self.lead_id}>'

class ProdutoNutricao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # consulta, plano, suplemento
    ativo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Produto {self.nome}>'

class BaseConhecimento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tema = db.Column(db.String(100), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # faq, produto, nutricional
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Base de Conhecimento {self.tema}>'

class Configuracao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Configuração {self.chave}>'
