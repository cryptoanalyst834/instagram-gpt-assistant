from flask import Flask, request
import requests
import os

app = Flask(__name__)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/", methods=["GET"])
def index():
    return "Instagram GPT Assistant is running", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return request.args.get("hub.challenge"), 200
        return "Verification token mismatch", 403

    elif request.method == "POST":
        data = request.get_json()
        print("Received:", data)

        if data["object"] == "instagram":
            for entry in data["entry"]:
                for message in entry["messaging"]:
                    if "message" in message:
                        sender_id = message["sender"]["id"]
                        user_message = message["message"]["text"]

                        reply = generate_openrouter_reply(user_message)
                        send_instagram_reply(sender_id, reply)

        return "OK", 200


def generate_openrouter_reply(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openchat/openchat-7b",
        "messages": [
            {"role": "system", "content": "Ты доброжелательный Instagram-ассистент, говоришь на русском."},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    try:
        return response.json()["choices"][0]["message"]["content"]
    except:
        return "Извини, произошла ошибка. Попробуй ещё раз."


def send_instagram_reply(recipient_id, message_text):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    res = requests.post(url, json=payload, headers=headers)
    print("Sent reply:", res.text)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
