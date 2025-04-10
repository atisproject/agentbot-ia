from app import app
from routes import init_scheduler
import routes  # Importa as rotas principais
import whatsapp_routes  # Importa as rotas do WhatsApp

if __name__ == "__main__":
    # Iniciar o agendador de tarefas
    init_scheduler()
    
    # Iniciar a aplicação
    app.run(host="0.0.0.0", port=5000, debug=True)
