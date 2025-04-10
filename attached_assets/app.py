import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# cria a aplicação
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nutriai_secret_key")

# configura o banco de dados
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///nutriai.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# inicializa o app com a extensão
db.init_app(app)

# Configuração do login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Importa as rotas
from routes import *
# Importa as rotas do WhatsApp
from whatsapp_routes import *

with app.app_context():
    # Importa os modelos para a criação de tabelas
    import models
    db.create_all()

    # Verifica se já existe um usuário administrador
    from models import User
    from werkzeug.security import generate_password_hash
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@nutriai.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        app.logger.info("Usuário administrador padrão criado")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))
