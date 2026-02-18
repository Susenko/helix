from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    helix_allowed_origin: str = "http://localhost:3000"

    # Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/helix"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/oauth/google/callback"

    # user context
    user_timezone: str = "Europe/Bucharest"

    # Telegram bot
    telegram_bot_token: str = ""

settings = Settings()
