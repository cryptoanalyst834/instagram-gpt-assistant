from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# --- Настройка FastAPI ---
app = FastAPI()

# --- Переменные окружения ---
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

if not VERIFY_TOKEN or not OPENROUTER_KEY or not PAGE_ACCESS_TOKEN:
    raise Exception("Не установлены переменные окружения: VERIFY_TOKEN, OPENROUTER_KEY или PAGE_ACCESS_TOKEN")

# --- Google Sheets подключение ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '146idlM2cg1mWuccNGCZNLxLZUNsqBTBVue460TZ9_kg'

def get_gsheet():
    creds = Credentials.from_service_account_file('creds.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.sheet1

def save_message_to_sheet(user_id, user_message, bot_reply):
    try:
        ws = get_gsheet()
        ws.append_row([user_id, user_message, bot_reply])
        print("✅ Сохранено в Google Таблицу")
    except Exception as e:
        print("❌ Ошибка записи в таблицу:", e)

# --- Роуты ---
@app.get("/")
def root():
    return {"status": "OK"}

@app.get("/webhook")
def verify_webhook(request: Request):
    args = request.query_params
    if args.get("hub.mode") == "subscribe" and args.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=args.get("hub.challenge"), status_code=200)
    return {"status": "Verification failed"}

@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.json()
    print("📩 Получен Webhook:", json.dumps(body, indent=2, ensure_ascii=False))

    try:
        for entry in body.get("entry", []):
            for message_event in entry.get("messaging", []):
                sender_id = message_event["sender"]["id"]
                if "message" in message_event and "text" in message_event["message"]:
                    user_message = message_event["message"]["text"]

                    # Получить ответ от GPT
                    reply = await ask_gpt(user_message)

                    # Отправить ответ в Instagram
                    await send_reply_to_instagram(sender_id, reply)

                    # Сохранить в Google Таблицу
                    save_message_to_sheet(sender_id, user_message, reply)
    except Exception as e:
        print("❌ Ошибка при обработке:", e)

    return {"status": "ok"}

# --- ИИ-ответ через OpenRouter ---
async def ask_gpt(user_message):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://photonewborn.taplink.ws",
        "X-Title": "Newborn Assistant"
    }

    payload = {
        "model": "openrouter/openai/gpt-4o",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты — профессиональный ИИ-ассистент фотографа новорождённых. "
                    "У тебя успешный опыт работы маркетологом более 10 лет. "
                    "Ты ведёшь клиента по цепочке продаж: интерес → прогрев → действие → дожим. "
                    "Ты закрываешь страхи и возражения клиентов (безопасность, опыт, стоимость, результат). "
                    "Ты отвечаешь только на вопросы по теме съёмки новорождённых. "
                    "Ты не обсуждаешь темы политики, медицины, религии. "
                    "Отвечай по делу, тёплым и заботливым тоном."
                )
            },
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code != 200:
        print("❌ Ошибка OpenRouter:", response.status_code, response.text)
        return "Извините, возникла ошибка. Попробуйте позже."

    data = response.json()
    return data["choices"][0]["message"]["content"]

# --- Отправка сообщения в Instagram ---
async def send_reply_to_instagram(user_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message_text[:1000]}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            print("❌ Ошибка отправки:", response.status_code, response.text)

# --- Запуск на Railway ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
