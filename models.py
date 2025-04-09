from datetime import datetime
from flask_login import UserMixin
from database import db

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Lead(db.Model):
    """Lead model for potential clients"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    telefone = db.Column(db.String(20), nullable=False)
    fonte = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='novo')  # novo, em_contato, convertido, perdido
    observacoes = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, default=0.0)  # Score de probabilidade de conversão
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interacoes = db.relationship('Interacao', backref='lead', lazy=True)
    formularios = db.relationship('Formulario', backref='lead', lazy=True)

class Interacao(db.Model):
    """Interaction model for communication with leads"""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    origem = db.Column(db.String(20), nullable=False)  # usuario, ia, sistema
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    sentimento = db.Column(db.Float, nullable=True)  # Sentimento da mensagem (-1 a 1)

class Formulario(db.Model):
    """Form model for client data collection"""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # avaliacao_fisica, anamnese_nutricional, etc.
    link = db.Column(db.String(255), nullable=False)
    data_envio = db.Column(db.DateTime, default=datetime.utcnow)
    data_resposta = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='pendente')  # pendente, respondido, expirado
    lembrete_enviado = db.Column(db.Boolean, default=False)
    numero_lembretes = db.Column(db.Integer, default=0)

class BaseConhecimento(db.Model):
    """Knowledge base for AI responses"""
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(50), nullable=False)
    pergunta = db.Column(db.Text, nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    palavras_chave = db.Column(db.String(255), nullable=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Configuracao(db.Model):
    """System configuration settings"""
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Text, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    categoria = db.Column(db.String(50), nullable=True)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
