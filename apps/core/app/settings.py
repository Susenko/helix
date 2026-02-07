from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    helix_allowed_origin: str = "http://localhost:3000"

settings = Settings()
