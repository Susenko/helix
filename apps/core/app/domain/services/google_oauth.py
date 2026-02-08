from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx

from app.settings import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.events"

def build_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": CALENDAR_SCOPE,
        "access_type": "offline",      # нужен refresh_token
        "prompt": "consent",           # чтобы refresh_token точно пришёл
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

async def exchange_code_for_tokens(code: str) -> dict:
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
        "code": code,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(GOOGLE_TOKEN_URL, data=data)
        r.raise_for_status()
        return r.json()

async def refresh_access_token(refresh_token: str) -> dict:
    data = {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(GOOGLE_TOKEN_URL, data=data)
        r.raise_for_status()
        return r.json()

def compute_expiry_utc(expires_in: int | None) -> datetime | None:
    if not expires_in:
        return None
    return datetime.utcnow() + timedelta(seconds=int(expires_in))
