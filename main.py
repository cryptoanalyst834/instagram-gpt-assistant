import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ai24verifytoken")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "your-instagram-token")


@app.get("/")
async def verify_webhook(request: Request):
    """
    Верификация webhook от Meta (Instagram)
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Верификация Meta Webhook пройдена")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        print("❌ Ошибка верификации webhook:", params)
        return PlainTextResponse(content="Verification failed", status_code=403)


@app.post("/")
async def receive_webhook(request: Request):
    """
    Приём POST-сообщений от Instagram API
    """
    body = await request.json()
    print("📩 Получено событие от Instagram API:", body)

    # Здесь можно добавить пересылку в Telegram, запись в лог и т.п.
    return JSONResponse(content={"status": "received"}, status_code=200)
