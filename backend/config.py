from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "FastAPI Project"
    app_env: str = "development"
    api_v1_str: str = "/api/v1"
    gemini_api_key: str
    groq_api_key: str
    cooldown_seconds: int = 60

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
