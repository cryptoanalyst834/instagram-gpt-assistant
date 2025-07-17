from flask import Flask, request
from ai_logic import process_message
from telegram_notify import send_telegram
from google_sheets import write_to_sheet

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    user_id = data.get('sender', {}).get('id')
    message = data.get('message', {}).get('text')

    if not user_id or not message:
        return {'status': 'no data'}, 400

    reply, log_data = process_message(message, user_id)
    
    # log to Telegram & Google Sheets
    send_telegram(log_data)
    write_to_sheet(log_data)

    return {'reply': reply}, 200

if __name__ == '__main__':
    app.run(debug=True)
