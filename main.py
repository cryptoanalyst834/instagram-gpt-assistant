import os
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

app = FastAPI()
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "")

@app.get("/webhook")
async def verify(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    print("🔍 VERIFY", mode, token, challenge)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge or "", status_code=200)
    return PlainTextResponse("Verification failed", status_code=403)

@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    print("📩 RECEIVED", data)
    return JSONResponse({"status": "received"}, status_code=200)
