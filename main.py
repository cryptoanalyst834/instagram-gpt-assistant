# main.py

from fastapi import FastAPI, Request
import httpx
import os
import json

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")


@app.get("/")
def root():
    return {"status": "OK"}


@app.get("/webhook")
def verify_webhook(request: Request):
    """Подтверждение webhook при подключении в Meta Developer"""
    args = request.query_params
    if args.get("hub.mode") == "subscribe" and args.get("hub.verify_token") == VERIFY_TOKEN:
        return int(args.get("hub.challenge"))
    return {"status": "Verification failed"}


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Обработка входящих сообщений от Instagram"""
    body = await request.json()

    try:
        for entry in body["entry"]:
            for message_event in entry["messaging"]:
                sender_id = message_event["sender"]["id"]
                if "message" in message_event and "text" in message_event["message"]:
                    user_message = message_event["message"]["text"]

                    reply = await ask_gpt(user_message)
                    await send_reply_to_instagram(sender_id, reply)
    except Exception as e:
        print("Ошибка при обработке сообщения:", e)

    return {"status": "ok"}


async def ask_gpt(user_message):
    """Отправка запроса к OpenRouter GPT-4o"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "HTTP-Referer": "https://yourdomain.com",
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
                    "Ты не обсуждаешь темы политики, медицины, религии, и любые темы вне съёмок. "
                    "Ты опираешься на лучшие практики мировых топ-фотографов новорождённых. "
                    "Отвечай кратко, по делу, тёплым и заботливым тоном, как опытный менеджер-фотограф."
                )
            },
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
    data = response.json()
    return data["choices"][0]["message"]["content"]


async def send_reply_to_instagram(user_id, message_text):
    """Отправка ответа обратно в Instagram Direct"""
    url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": user_id},
        "message": {"text": message_text}
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)
