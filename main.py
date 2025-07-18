import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ai24verifytoken")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__)

# ✅ Проверка webhook при подключении от Meta
@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return request.args.get("hub.challenge"), 200
    return "Verification token mismatch", 403

# ✅ Обработка входящих сообщений от Instagram
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    print("Получено сообщение:", data)

    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages")
                if messages:
                    for message in messages:
                        sender_id = message["from"]
                        text = message.get("text", {}).get("body")
                        if text:
                            reply = generate_ai_reply(text)
                            send_message(sender_id, reply)
    except Exception as e:
        print("Ошибка обработки входящего запроса:", e)

    return "OK", 200

# ✅ Генерация ответа через OpenRouter API
def generate_ai_reply(message_text):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "openrouter/cinematika-7b",  # можно заменить на другой
            "messages": [
                {"role": "system", "content": "Ты дружелюбный ассистент Instagram-бота."},
                {"role": "user", "content": message_text}
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("Ошибка генерации ответа:", e)
        return "Извините, возникла ошибка при генерации ответа."

# ✅ Отправка сообщения обратно в Instagram Direct
def send_message(recipient_id, text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Ответ отправлен:", response.status_code, response.text)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
