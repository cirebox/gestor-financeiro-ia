# Exemplos de uso da API com WhatsApp

# 1. Exemplo usando cURL para processar uma mensagem do WhatsApp
# curl -X 'POST' \
#   'http://0.0.0.0:8000/api/v1/nlp/whatsapp/process' \
#   -H 'accept: application/json' \
#   -H 'X-WhatsApp-API-Key: whatsapp-integration-secret-key' \
#   -H 'Content-Type: application/json' \
#   -d '{
#   "command": "Listar despesas",
#   "phone_number": "5511999999999"
# }'

# 2. Exemplo usando Python Requests
import requests
import json

def process_whatsapp_message(phone_number, message):
    """
    Processa uma mensagem do WhatsApp.
    
    Args:
        phone_number: Número de telefone do usuário
        message: Mensagem enviada pelo usuário
        
    Returns:
        Resposta do processamento
    """
    url = "http://0.0.0.0:8000/api/v1/nlp/whatsapp/process"
    
    headers = {
        "X-WhatsApp-API-Key": "whatsapp-integration-secret-key",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "command": message,
        "phone_number": phone_number
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "status": "error",
            "message": f"Erro na API: {response.status_code} - {response.text}"
        }

# Exemplo de uso da função
response = process_whatsapp_message("5511999999999", "Listar despesas")
print(json.dumps(response, indent=2))

# 3. Exemplo usando uma integração com Twilio WhatsApp API
from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

@app.route('/whatsapp-webhook', methods=['POST'])
def whatsapp_webhook():
    """Webhook para receber mensagens do Twilio WhatsApp."""
    # Extrai informações da mensagem do Twilio
    from_number = request.values.get('From', '').replace('whatsapp:', '')
    body = request.values.get('Body', '')
    
    # Processa a mensagem no Financial Tracker
    url = "http://0.0.0.0:8000/api/v1/nlp/whatsapp/process"
    
    headers = {
        "X-WhatsApp-API-Key": "whatsapp-integration-secret-key",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "command": body,
        "phone_number": from_number
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        # Formata a resposta para o WhatsApp
        twilio_response = {
            "response": {
                "message": result["message"]
            }
        }
        
        return jsonify(twilio_response)
    else:
        # Em caso de erro, envia uma mensagem genérica
        return jsonify({
            "response": {
                "message": "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
            }
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)