import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")

@app.route("/", methods=["GET"])
def home():
    return "AI24 Instagram Assistant Webhook is running!"

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("WEBHOOK_VERIFIED")
        return challenge, 200
    else:
        return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    data = request.get_json()
    print("Received webhook event:", data)

    # Здесь можно добавить свою логику обработки входящих сообщений
    return "EVENT_RECEIVED", 200

@app.route("/access-token", methods=["GET"])
def get_access_token():
    url = f"https://graph.facebook.com/oauth/access_token" \
          f"?client_id={APP_ID}&client_secret={APP_SECRET}&grant_type=client_credentials"
    response = requests.get(url)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
