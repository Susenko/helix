from datetime import datetime
import httpx

GOOGLE_CAL_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"

async def list_events(access_token: str, time_min_iso: str, time_max_iso: str) -> dict:
    params = {
        "timeMin": time_min_iso,
        "timeMax": time_max_iso,
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "50",
    }
    headers = {"Authorization": f"Bearer {access_token}"}

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(GOOGLE_CAL_EVENTS_URL, params=params, headers=headers)
        r.raise_for_status()
        return r.json()


async def create_event(access_token: str, summary: str, start_iso: str, end_iso: str) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(GOOGLE_CAL_EVENTS_URL, json=payload, headers=headers)
        r.raise_for_status()
        return r.json()
