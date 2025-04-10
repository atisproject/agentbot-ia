import os
from flask import request, jsonify, render_template
from twilio.twiml.messaging_response import MessagingResponse
from app import app
from database import db
from models import Lead, Interacao
from whatsapp_integration import processar_mensagem_whatsapp, enviar_mensagem_whatsapp
import logging

logger = logging.getLogger(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Webhook para receber mensagens do WhatsApp via Twilio

    Essa rota recebe as notificações da Twilio quando uma nova mensagem é enviada
    para o número do WhatsApp. A mensagem é processada e uma resposta é enviada.
    """
    try:
        # Extrair informações da requisição
        mensagem_de = request.values.get('From', '')
        mensagem_texto = request.values.get('Body', '')

        logger.info(f"Mensagem recebida via WhatsApp de {mensagem_de}: {mensagem_texto}")

        # Processar a mensagem e gerar resposta
        resposta = processar_mensagem_whatsapp(mensagem_de, mensagem_texto)

        # Preparar resposta para o Twilio
        resp = MessagingResponse()
        resp.message(resposta)

        return str(resp)

    except Exception as e:
        logger.error(f"Erro no webhook do WhatsApp: {str(e)}")
        # Mesmo em caso de erro, precisamos retornar uma resposta válida para o Twilio
        resp = MessagingResponse()
        resp.message("Estamos com dificuldades técnicas. Por favor, tente novamente mais tarde.")
        return str(resp)

@app.route('/api/whatsapp/enviar', methods=['POST'])
def enviar_whatsapp():
    """
    API para enviar mensagens do WhatsApp manualmente

    Esta rota permite que os administradores do sistema enviem mensagens
    para os clientes via WhatsApp a partir da interface web.
    """
    # Verificar autenticação (isso será aprimorado com login_required depois)
    # Esta API é apenas para ser usada pela interface de administração

    data = request.json

    if not data or 'numero' not in data or 'mensagem' not in data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados incompletos'}), 400

    numero = data['numero']
    mensagem = data['mensagem']
    lead_id = data.get('lead_id')

    # Enviar a mensagem
    sucesso = enviar_mensagem_whatsapp(numero, mensagem)

    # Se temos o lead_id, registrar a interação
    if lead_id and sucesso:
        try:
            lead_id = int(lead_id)
            interacao = Interacao(
                lead_id=lead_id,
                mensagem=mensagem,
                origem="sistema"  # ou "usuario" dependendo do contexto
            )
            db.session.add(interacao)
            db.session.commit()
        except Exception as e:
            logger.error(f"Erro ao registrar interação: {str(e)}")

    if sucesso:
        return jsonify({'status': 'sucesso', 'mensagem': 'Mensagem enviada com sucesso'})
    else:
        return jsonify({'status': 'erro', 'mensagem': 'Falha ao enviar mensagem'}), 500

@app.route('/configuracao/whatsapp', methods=['GET', 'POST'])
def whatsapp_configuracao():
    """
    Página para configuração do WhatsApp

    Esta rota permite configurar as mensagens padrões e outras
    configurações relacionadas ao WhatsApp.
    """
    if request.method == 'POST':
        # Implementar salvamento das configurações
        pass

    # Por enquanto, apenas redireciona para a página principal de configurações
    return render_template('configuracoes.html')

@app.route('/instrucoes-whatsapp', methods=['GET'])
def instrucoes_whatsapp():
    """
    Página com instruções para uso do WhatsApp Sandbox

    Esta rota exibe instruções para que os usuários possam se inscrever
    no sandbox do WhatsApp da Twilio e começar a usar o sistema.
    """
    # Número do WhatsApp da Sandbox (obtido da variável de ambiente)
    whatsapp_numero = os.environ.get('TWILIO_PHONE_NUMBER')

    # Código de opt-in (normalmente "join <palavra>" para o sandbox da Twilio)
    codigo_optin = 'join solution-plenty'

    return render_template('instrucoes_whatsapp.html', 
                          whatsapp_numero=whatsapp_numero,
                          codigo_optin=codigo_optin)