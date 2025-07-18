import os
import openai
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCES_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")


@app.route("/", methods=["GET"])
def home():
    return "Сервер работает"


# Валидация Webhook от Meta (Instagram / Facebook)
@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Вебхук верифицирован.")
            return challenge, 200
        else:
            return "Ошибка верификации", 403
    return "Неверный запрос", 400


# Обработка входящих сообщений
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("📩 Получен запрос:", data)

    try:
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if "message" in messaging_event:
                    sender_id = messaging_event["sender"]["id"]
                    user_message = messaging_event["message"]["text"]

                    # Получить ответ от OpenRouter
                    reply = get_openrouter_reply(user_message)

                    # Отправить ответ пользователю
                    send_message(sender_id, reply)

    except Exception as e:
        print("❌ Ошибка обработки:", e)

    return "OK", 200


# Функция: получить ответ от OpenRouter
def get_openrouter_reply(user_input):
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": user_input}]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        return reply.strip()

    except Exception as e:
        print("Ошибка OpenRouter:", e)
        return "Извините, я временно не могу ответить."


# Функция: отправить сообщение пользователю через Graph API
def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    response = requests.post(url, json=payload)
    print("➡️ Ответ Meta:", response.text)
