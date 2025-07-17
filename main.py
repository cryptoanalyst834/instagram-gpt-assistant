import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ai24verifytoken")


@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("🔍 Проверка webhook:", params)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        return PlainTextResponse(content="Verification failed", status_code=403)


@app.post("/webhook")
async def receive_webhook(request: Request):
    body = await request.json()
    print("📩 Событие от Instagram:", body)
    return JSONResponse(content={"status": "received"}, status_code=200)
