from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI()

# Переменные окружения
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Проверка переменных
if not all([VERIFY_TOKEN, OPENROUTER_KEY, PAGE_ACCESS_TOKEN, GOOGLE_CREDS_JSON]):
    raise Exception("Некоторые переменные окружения не заданы!")

# Подключение к Google Sheets
creds_dict = json.loads(GOOGLE_CREDS_JSON)
credentials = Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/spreadsheets"])
gc = gspread.authorize(credentials)

# ID таблицы
SHEET_ID = "146idlM2cg1mWuccNGCZNLxLZUNsqBTBVue460TZ9_kg"
worksheet = gc.open_by_key(SHEET_ID).sheet1


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
    print("Webhook received:", json.dumps(body, indent=2, ensure_ascii=False))

    try:
        for entry in body.get("entry", []):
            if "messaging" not in entry:
                continue
            for message_event in entry["messaging"]:
                sender_id = message_event["sender"]["id"]
                if "message" in message_event and "text" in message_event["message"]:
                    user_message = message_event["message"]["text"]
                    reply = await ask_gpt(user_message)
                    await send_reply_to_instagram(sender_id, reply)
                    save_to_google_sheet(sender_id, user_message, reply)
    except Exception as e:
        print("Ошибка:", e)

    return {"status": "ok"}


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
                    "Отвечай по теме, заботливо и по делу."
                )
            },
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

    if response.status_code != 200:
        print("Ошибка OpenRouter:", response.status_code, response.text)
        return "Извините, сейчас не могу ответить."

    data = response.json()
    return data["choices"][0]["message"]["content"]


async def send_reply_to_instagram(user_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message_text[:1000]}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            print("Ошибка отправки:", response.status_code, response.text)


def save_to_google_sheet(user_id, message, reply):
    try:
        worksheet.append_row([user_id, message, reply])
    except Exception as e:
        print("Ошибка записи в таблицу:", e)
