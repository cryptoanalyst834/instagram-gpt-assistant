import sqlite3
import os
from datetime import datetime, timedelta
import time
import requests

DB_PATH = "leads.db"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@sidarenkas")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        user_id TEXT,
        message TEXT,
        reply TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()

def save_lead(user_id, message, reply):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO leads (user_id, message, reply) VALUES (?, ?, ?)", (user_id, message, reply))
    conn.commit()
    conn.close()

def get_inactive_leads(hours=24):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    threshold = datetime.now() - timedelta(hours=hours)
    c.execute("SELECT user_id FROM leads WHERE timestamp <= ? GROUP BY user_id", (threshold,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

def send_followup(user_id):
    text = (
        "Привет! 👋 Напоминаю, что ты можешь пройти бесплатный ИИ-аудит бизнеса на нашем сайте.\n"
        "👉 https://ai24solutions.ru/#quiz\n\n"
        "Если хочешь пример кейса — просто напиши: «Хочу пример» 📄"
    )
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", params={
        "chat_id": CHAT_ID,
        "text": f"⏰ Follow-up для {user_id}:\n\n{text}"
    })

def run_scheduler():
    init_db()
    while True:
        inactive_users = get_inactive_leads()
        for user in inactive_users:
            send_followup(user)
        time.sleep(3600)  # Проверка раз в час

if __name__ == "__main__":
    run_scheduler()
