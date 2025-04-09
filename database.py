import os
import logging
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

def configure_db(app):
    """
    Configure database settings for the application
    
    Args:
        app: Flask application instance
    """
    # Configure database
    # Render provides DATABASE_URL environment variable
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///agentbot.db")
    
    # Handle potential "postgres://" prefix in Render DATABASE_URL (it needs "postgresql://")
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "connect_args": {
            "sslmode": "require"
        } if DATABASE_URL.startswith("postgresql") else {}
    }
    
    # Initialize database with app
    db.init_app(app)
    
    logger.info("Database configuration completed")