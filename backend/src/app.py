import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from livekit import api
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

LIVEKIT_URL = os.getenv("LIVEKIT_URL")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/token")
async def get_token():
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing")

    room_name = "sunrise-salon-room"
    participant_name = f"customer-{os.urandom(2).hex()}"

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return {"url": LIVEKIT_URL, "token": token}