from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application configuration
    app_name: str = "FastAPI Project"
    api_v1_str: str = "/api/v1"
    debug: bool = False

    # External API Keys
    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    openrouter_api_key: str | None = None

    # Execution and request logic
    request_timeout: int = 30
    max_retries: int = 3
    cooldown_seconds: int = 5

    # Pydantic V2 model configuration
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()
