import os
import openai
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # токен для валидации вебхука
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")  # long-lived Instagram page token
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # токен OpenRouter

# Хранилище переписки (в проде использовать БД)
user_sessions = {}

# Ограниченные темы
BLOCKED_TOPICS = ["религия", "политика", "медицина", "здоровье"]

@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Ошибка валидации", 403


@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()
    try:
        for entry in data.get("entry", []):
            for msg_event in entry.get("messaging", []):
                sender_id = msg_event["sender"]["id"]
                if "message" in msg_event and "text" in msg_event["message"]:
                    user_message = msg_event["message"]["text"]

                    # Проверка на запрещённые темы
                    if any(topic in user_message.lower() for topic in BLOCKED_TOPICS):
                        send_message(sender_id, "К сожалению, я не могу обсуждать эту тему. Задайте, пожалуйста, другой вопрос.")
                        return "ok", 200

                    # Поддержка истории (simple)
                    if sender_id not in user_sessions:
                        user_sessions[sender_id] = []

                    user_sessions[sender_id].append({"role": "user", "content": user_message})

                    # Ответ через OpenRouter
                    ai_reply = ask_openrouter(user_sessions[sender_id])
                    user_sessions[sender_id].append({"role": "assistant", "content": ai_reply})

                    send_message(sender_id, ai_reply)
        return "ok", 200
    except Exception as e:
        print("Ошибка:", e)
        return "Ошибка", 500


def ask_openrouter(history):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    prompt_system = {
        "role": "system",
        "content": (
            "Ты AI-консультант по внедрению искусственного интеллекта в бизнес. "
            "Объясняй простым и дружелюбным языком, выявляй боли клиента, консультируй, закрывай возражения "
            "и подводи к покупке AI-решения. Не обсуждай религию, здоровье, медицину и политику."
        )
    }

    messages = [prompt_system] + history[-10:]  # не больше 10 сообщений

    data = {
        "model": "openrouter/openai/gpt-4",  # или gpt-3.5
        "messages": messages,
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    res_json = response.json()
    return res_json["choices"][0]["message"]["content"]


def send_message(recipient_id, message_text):
    url = "https://graph.facebook.com/v18.0/me/messages"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    response = requests.post(url, params=params, headers=headers, json=data)
    if response.status_code != 200:
        print("Ошибка отправки:", response.text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
