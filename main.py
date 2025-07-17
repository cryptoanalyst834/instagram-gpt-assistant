import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")  # токен подтверждения Instagram webhook

@app.get("/")
async def root():
    return {"status": "AI24assistantBot is running ✅"}

# Instagram webhook verification
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        raise HTTPException(status_code=403, detail="Forbidden: Verification failed.")

# Instagram webhook POST handler
@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        print("📩 Incoming Webhook:", data)
        return JSONResponse(content={"status": "received"}, status_code=200)
    except Exception as e:
        print("❌ Error handling webhook:", e)
        raise HTTPException(status_code=400, detail="Invalid payload")
