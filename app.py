from flask import Flask, request
import os
from ai_logic import process_message
from telegram_notify import send_telegram
from google_sheets import write_to_sheet
from scheduler import save_lead  # сохраняем в SQLite для дожима

app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 🔹 Проверка токена от Meta (GET-запрос)
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if verify_token == os.getenv("VERIFY_TOKEN"):
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    # 🔹 Обработка входящих сообщений (POST-запрос)
    if request.method == 'POST':
        data = request.json

        try:
            entry = data.get("entry", [])[0]
            messaging = entry.get("messaging", [])[0]
            sender_id = messaging["sender"]["id"]
            message_text = messaging["message"]["text"]
        except Exception as e:
            return {"error": str(e)}, 400

        # 🔹 Обрабатываем сообщение через GPT
        reply, log_data = process_message(message_text, sender_id)

        # 🔹 Логируем
        send_telegram(log_data)
        write_to_sheet(log_data)
        save_lead(sender_id, message_text, reply)

        return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
