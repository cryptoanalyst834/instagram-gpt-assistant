from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")


@app.get("/")
async def root():
    return {"status": "Webhook server is running."}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Подтверждение Webhook от Meta (GET-запрос)
    """
    params = dict(request.query_params)
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params["hub.challenge"])
    return {"status": "Verification token mismatch"}, 403


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Получение событий от Instagram (POST-запрос)
    """
    data = await request.json()
    print("🔔 Новое событие от Instagram:", data)

    # Здесь можно добавить отправку в Telegram, логику обработки и т.п.
    return {"status": "received"}


if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
