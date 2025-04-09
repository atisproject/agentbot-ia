import os
from app import app, init_db, start_scheduler

# Import models - must happen before routes to avoid circular dependencies
import models

# Import routes after models and app are initialized
import routes
import whatsapp_routes

if __name__ == "__main__":
    # Initialize database tables
    init_db()
    
    # Start background scheduler
    start_scheduler()
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 5000))
    
    # Run the app
    app.run(host="0.0.0.0", port=port, debug=True)
