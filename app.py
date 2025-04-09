import os
import logging
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from apscheduler.schedulers.background import BackgroundScheduler
from database import db, configure_db

# Application Configuration
APP_NAME = "AgentBot-IA"
APP_VERSION = "1.0.0"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", os.urandom(24).hex())

# Fix for working behind proxies (needed for Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure and initialize database
configure_db(app)

# Set up login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Initialize scheduler
scheduler = BackgroundScheduler(daemon=True)

# Need to handle circular imports carefully
@login_manager.user_loader
def load_user(user_id):
    # Import here to avoid circular imports
    from models import User
    return User.query.get(int(user_id))

# Initialize database tables
def init_db():
    with app.app_context():
        logger.info("Creating database tables...")
        db.create_all()
        
        # Import here to avoid circular imports
        from models import User
        
        # Check if admin user exists, if not create one
        if not User.query.filter_by(username="admin").first():
            from werkzeug.security import generate_password_hash
            admin = User(
                username="admin",
                email="admin@agentbot-ia.com",
                password_hash=generate_password_hash("admin123")
            )
            db.session.add(admin)
            db.session.commit()
            logger.info("Created admin user")

# Start the scheduler
def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started")

# Note: Routes are imported in main.py to avoid circular dependencies
