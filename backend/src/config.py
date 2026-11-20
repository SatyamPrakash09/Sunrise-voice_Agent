from dotenv import load_dotenv
load_dotenv()
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LIVEKIT_URL:str = "https://www.livekit.com/"
    LIVEKIT_API_KEY:str = "api_key"
    LIVEKIT_API_SECRET:str = "api_secret"
    DATABASE_URL:str = "db_url"
    GROQ_API_KEY:str = "groq_key"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()