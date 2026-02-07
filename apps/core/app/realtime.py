import httpx
import json
import logging
from .settings import settings

OPENAI_REALTIME_URL = "https://api.openai.com/v1/realtime/calls"
OPENAI_REALTIME_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"
logger = logging.getLogger("helix.realtime")

async def exchange_sdp(offer_sdp: str) -> str:
    session = {
        "type": "realtime",
        "model": "gpt-realtime",
        "audio": {
            "output": { "voice": "alloy" }
        }
    }
    if not offer_sdp or not offer_sdp.startswith("v="):
        logger.error("Invalid SDP offer (len=%s)", 0 if offer_sdp is None else len(offer_sdp))
        raise httpx.HTTPError("Invalid SDP offer")

    async with httpx.AsyncClient(timeout=30) as client:
        files = {
            "sdp": ("offer.sdp", offer_sdp, "application/sdp"),
        }
        data = {
            "session": json.dumps(session),
        }

        r = await client.post(
            OPENAI_REALTIME_URL,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}"
            },
            files=files,
            data=data,
        )
        if r.status_code >= 400:
            logger.error("OpenAI realtime error %s: %s", r.status_code, r.text)
        r.raise_for_status()
        return r.text


async def create_client_secret() -> dict:
    payload = {
        "session": {
            "type": "realtime",
            "model": "gpt-realtime",
        }
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            OPENAI_REALTIME_CLIENT_SECRETS_URL,
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if r.status_code >= 400:
            logger.error("OpenAI client_secret error %s: %s", r.status_code, r.text)
        r.raise_for_status()
        return r.json()
