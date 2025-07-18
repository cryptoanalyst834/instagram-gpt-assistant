import os
import json
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)

# Память диалогов: user_id -> list of messages
conversations = {}

SYSTEM_PROMPT = (
    "Ты профессиональный AI-консультант, который помогает бизнесу внедрить искусственный интеллект. "
    "Выясни потребности клиента, предложи релевантные решения, объясни выгоды. "
    "Отвечай дружелюбно, с примерами, как ИИ поможет сэкономить или увеличить прибыль. "
    "Сохраняй профессиональный, вдохновляющий стиль. "
    "Избегай обсуждения религии, политики, медицины и здоровья. "
    "Веди диалог к заказу консультации или аудита. "
)

@app.route('/', methods=['GET'])
def index():
    return "Webhook is running."

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification token mismatch", 403

    if request.method == 'POST':
        data = request.get_json()
        if data.get("object") == "instagram":
            for entry in data.get("entry", []):
                messaging = entry.get("messaging", [])
                for event in messaging:
                    sender_id = event["sender"]["id"]
                    if "message" in event and "text" in event["message"]:
                        message_text = event["message"]["text"]
                        handle_user_message(sender_id, message_text)
        return "ok", 200

def handle_user_message(sender_id, message_text):
    # Инициализация истории
    if sender_id not in conversations:
        conversations[sender_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Добавление запроса пользователя
    conversations[sender_id].append({"role": "user", "content": message_text})

    # Отправка запроса к OpenRouter
    reply = ask_openrouter(conversations[sender_id])

    # Добавление ответа ассистента
    conversations[sender_id].append({"role": "assistant", "content": reply})

    # Ответ пользователю
    send_message(sender_id, reply)

def ask_openrouter(history):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openai/gpt-4o",  # можно заменить на claude-3-opus или др.
            "messages": history,
            "temperature": 0.7
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return "Извините, возникла техническая ошибка. Попробуйте позже."

def send_message(recipient_id, text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE"
    }
    params = {"access_token": ACCESS_TOKEN}
    requests.post(url, headers=headers, params=params, json=payload)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
