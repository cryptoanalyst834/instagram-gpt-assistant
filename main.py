import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ai24verifytoken")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "secret_if_needed")


@app.get("/")
async def root():
    return {"status": "Webhook server is running."}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Подтверждение Webhook от Meta (GET-запрос)
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=str(challenge), status_code=200)
    else:
        return PlainTextResponse(content="Verification failed", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Получение событий от Instagram (POST-запрос)
    """
    data = await request.json()
    print("📩 Получено сообщение от Meta:", data)

    # Здесь можно добавить логику пересылки сообщений в Telegram, запись в БД и т.д.
    return JSONResponse(content={"status": "received"}, status_code=200)
