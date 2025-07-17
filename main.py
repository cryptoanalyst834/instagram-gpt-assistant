import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "ai24verifytoken")  # запасной fallback

@app.get("/")
async def root():
    return {"status": "ok"}

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print(f"👁️‍🗨️ VERIFY MODE={mode}, TOKEN={token}, CHALLENGE={challenge}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 EVENT RECEIVED:", data)
    return JSONResponse(content={"status": "received"}, status_code=200)
