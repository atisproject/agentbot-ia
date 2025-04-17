
import os
import logging
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler # type: ignore
from database import db, configure_db

# Configuração da Aplicação
APP_NAME = "AgentBot-IA"
APP_VERSION = "1.0.0"

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Correção para trabalhar com proxies (necessário para Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configurar e inicializar banco de dados
configure_db(app)

# Configurar gerenciador de login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Inicializar agendador
scheduler = BackgroundScheduler(daemon=True)

# Necessário tratar importações circulares cuidadosamente
@login_manager.user_loader
def load_user(user_id):
    # Importar aqui para evitar importações circulares
    from models import User
    return User.query.get(int(user_id))

# Inicializar tabelas do banco de dados
def init_db():
    with app.app_context():
        logger.info("Criando tabelas do banco de dados...")
        db.create_all()
        
        # Importar aqui para evitar importações circulares
        from models import User
        
        # Verificar se usuário admin existe, se não criar um
        if not User.query.filter_by(username="admin").first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username="admin",
                email="admin@agentbot-ia.com",
                password_hash=generate_password_hash("admin123")
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Usuário admin criado")

# Iniciar o agendador
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Agendador em segundo plano iniciado")

# --- Registro de Blueprints ---
# Certifique-se de que a pasta 'routes' tem um arquivo __init__.py (mesmo vazio)
# para que o import abaixo funcione corretamente.
def register_blueprints():
    try:
        from routes.admin_formulario import admin_formulario_bp # type: ignore
        app.register_blueprint(admin_formulario_bp)
        logger.info("Blueprint admin_formulario_bp registrado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao registrar blueprint admin_formulario_bp: {e}")
        logger.error(f"Verifique se a pasta 'routes' contém um arquivo __init__.py")

# Inicialização da aplicação
if __name__ == "__main__":
    # Inicializar banco de dados
    init_db()
    
    # Registrar blueprints
    register_blueprints()
    
    # Iniciar agendador
    start_scheduler()
    
    # Iniciar aplicação
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# Obs: Para uso com WSGI (Gunicorn/uWSGI), chame estas funções no arquivo principal:
# - init_db()
# - register_blueprints()
# - start_scheduler()
