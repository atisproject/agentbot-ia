import os
import logging
from app import app, db
import models  # Importante importar os modelos aqui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """
    Inicializa o banco de dados, criando as tabelas se necessário
    """
    logger.info("Inicializando banco de dados...")
    
    with app.app_context():
        # Cria todas as tabelas
        db.create_all()
        logger.info("Tabelas criadas com sucesso!")
        
        # Verificar se existe pelo menos um usuário administrador
        admin = models.User.query.filter_by(username='admin').first()
        if not admin:
            from werkzeug.security import generate_password_hash
            # Criar usuário admin padrão se não existir
            admin = models.User(
                username='admin',
                email='admin@agentbot-ia.shop',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Usuário admin criado com sucesso!")

if __name__ == "__main__":
    init_database()