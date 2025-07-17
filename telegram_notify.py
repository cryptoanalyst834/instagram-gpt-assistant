import requests
import os

def send_telegram(data):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '@sidarenkas')
    text = f"💬 Новый запрос:\n👤 {data['user_id']}\n📩 {data['message']}\n🤖 {data['reply']}"
    requests.get(f'https://api.telegram.org/bot{token}/sendMessage', params={'chat_id': chat_id, 'text': text})
