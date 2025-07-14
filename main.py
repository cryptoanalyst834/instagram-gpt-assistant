from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import httpx
import os
import json

app = FastAPI()

# Переменные окружения
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

# Проверка переменных
if not VERIFY_TOKEN or not OPENROUTER_KEY or not PAGE_ACCESS_TOKEN or not GOOGLE_CREDS_JSON:
    print("❌ Переменные окружения:")
    print("VERIFY_TOKEN:", bool(VERIFY_TOKEN))
    print("OPENROUTER_KEY:", bool(OPENROUTER_KEY))
    print("PAGE_ACCESS_TOKEN:", bool(PAGE_ACCESS_TOKEN))
    print("GOOGLE_CREDS_JSON:", bool(GOOGLE_CREDS_JSON))
    raise Exception("Некоторые переменные окружения не заданы!")

# Проверка парсинга JSON Google
try:
    google_creds = json.loads(GOOGLE_CREDS_JSON)
    print("✅ GOOGLE_CREDS_JSON успешно загружен")
except Exception as e:
    raise Exception("❌ Ошибка парсинга GOOGLE_CREDS_JSON") from e


@app.get("/")
def root():
    return {"status": "OK"}


@app.get("/webhook")
def verify_webhook(request: Request):
    args = request.query_params
    if args.get("hub.mode") == "subscribe" and args.get("hub.verify_token") == VERIFY_TOKEN:
        print("✅ Webhook подтверждён")
        return PlainTextResponse(content=args.get("hub.challenge"), status_code=200)
    return {"status": "Verification failed"}


@app.post("/webhook")
async def handle_webhook(request: Request):
    body = await request.json()
    print("📩 Получен webhook:", json.dumps(body, indent=2, ensure_ascii=False))

    try:
        for entry in body.get("entry", []):
            if "messaging" not in entry:
                continue
            for message_event in entry["messaging"]:
                sender_id = message_event["sender"]["id"]
                if "message" in message_event and "text" in message_event["message"]:
                    user_message = message_event["message"]["text"]
                    print(f"💬 Сообщение от пользователя {sender_id}: {user_message}")

                    reply = await ask_gpt(user_message)
                    await send_reply_to_instagram(sender_id, reply)

    except Exception as e:
        print("❌ Ошибка при обработке webhook:", e)

    return {"status": "ok"}


async def ask_gpt(user_message: str) -> str:
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
                    "Ты опираешься на лучшие практики мировых топ-фотографов новорождённых. "
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
    reply = data["choices"][0]["message"]["content"]
    print("✅ Ответ от OpenRouter:", reply)
    return reply


async def send_reply_to_instagram(user_id: str, message_text: str):
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message_text[:1000]}
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Ответ отправлен в Instagram пользователю {user_id}")
        else:
            print("❌ Ошибка отправки:", response.status_code, response.text)
