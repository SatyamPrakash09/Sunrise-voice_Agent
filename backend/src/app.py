import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from livekit import api
from src.config import get_settings
settings = get_settings()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIVEKIT_URL =settings.LIVEKIT_URL
LIVEKIT_API_KEY = settings.LIVEKIT_API_KEY
LIVEKIT_API_SECRET = settings.LIVEKIT_API_SECRET

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"message": "Hello World"}

@app.get("/token")
async def get_token(room: str | None = None):
    if not LIVEKIT_URL or not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise HTTPException(status_code=500, detail="LiveKit credentials missing")

    # Generate a unique room name for each call session so LiveKit Cloud
    # dispatches a new agent job every time a user connects.
    room_name = room or f"sunrise-salon-{os.urandom(4).hex()}"
    participant_name = f"customer-{os.urandom(2).hex()}"

    token = (
        api.AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return {"url": LIVEKIT_URL, "token": token, "room": room_name}