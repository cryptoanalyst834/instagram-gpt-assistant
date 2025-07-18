import os
import requests
from flask import Flask, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/", methods=["GET"])
def home():
    return "Server is running", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            return "Verification failed", 403

    elif request.method == "POST":
        data = request.get_json()
        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for message in value["messages"]:
                            sender_id = message["from"]
                            if "text" in message:
                                user_message = message["text"]["body"]
                                response = generate_openrouter_response(user_message)
                                send_instagram_message(sender_id, response)
        return "EVENT_RECEIVED", 200

    return "Not allowed", 405


def generate_openrouter_response(user_message):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "openai/gpt-4",
        "messages": [
            {"role": "system", "content": "Ты Instagram-ассистент, общайся дружелюбно и кратко."},
            {"role": "user", "content": user_message}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    if response.ok:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("OpenRouter Error:", response.text)
        return "Извините, возникла ошибка при генерации ответа."


def send_instagram_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v19.0/me/messages"
    params = {"access_token": ACCESS_TOKEN}
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }

    response = requests.post(url, params=params, json=payload)
    if not response.ok:
        print("Send message error:", response.text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
