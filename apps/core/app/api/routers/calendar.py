from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from app.domain.services.free_slots import find_free_slots

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings
from app.infra.db.session import SessionLocal
from app.infra.repos.google_tokens_repo import GoogleTokensRepo
from app.domain.services.google_oauth import refresh_access_token, compute_expiry_utc
from app.domain.services.google_calendar import list_events, create_event

router = APIRouter(prefix="/calendar", tags=["calendar"])

async def get_db() -> AsyncSession:
    async with SessionLocal() as db:
        yield db

def day_range_iso(tz_name: str, date_iso: str | None = None) -> tuple[str, str]:
    tz = ZoneInfo(tz_name)
    if date_iso:
        day = datetime.fromisoformat(date_iso).date()
    else:
        day = datetime.now(tz).date()
    start = datetime.combine(day, time(0, 0), tzinfo=tz)
    end = start + timedelta(days=1)
    # Google API expects RFC3339 timestamps
    return start.isoformat(), end.isoformat()

@router.get("/today")
async def today(db: AsyncSession = Depends(get_db)):
    repo = GoogleTokensRepo()
    tok = await repo.get_latest(db)
    if not tok:
        raise HTTPException(status_code=401, detail="Google Calendar not connected. Visit /oauth/google/start")

    # refresh if expired (with small leeway)
    if tok.expiry_utc and datetime.utcnow() > (tok.expiry_utc - timedelta(seconds=30)):
        if not tok.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token. Reconnect via /oauth/google/start")
        refreshed = await refresh_access_token(tok.refresh_token)
        new_access = refreshed["access_token"]
        new_expiry = compute_expiry_utc(refreshed.get("expires_in"))
        tok = await repo.update_access(db, tok, access_token=new_access, expiry_utc=new_expiry)

    time_min, time_max = day_range_iso(settings.user_timezone)
    data = await list_events(tok.access_token, time_min, time_max)

    items = data.get("items", [])
    # normalize a bit
    events = []
    for it in items:
        start = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
        end = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
        events.append({
            "id": it.get("id"),
            "summary": it.get("summary"),
            "start": start,
            "end": end,
            "status": it.get("status"),
        })

    return {"timezone": settings.user_timezone, "events": events}


@router.get("/day")
async def day(date: str | None = None, db: AsyncSession = Depends(get_db)):
    repo = GoogleTokensRepo()
    tok = await repo.get_latest(db)
    if not tok:
        raise HTTPException(status_code=401, detail="Google Calendar not connected. Visit /oauth/google/start")

    # refresh if expired (with small leeway)
    if tok.expiry_utc and datetime.utcnow() > (tok.expiry_utc - timedelta(seconds=30)):
        if not tok.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token. Reconnect via /oauth/google/start")
        refreshed = await refresh_access_token(tok.refresh_token)
        new_access = refreshed["access_token"]
        new_expiry = compute_expiry_utc(refreshed.get("expires_in"))
        tok = await repo.update_access(db, tok, access_token=new_access, expiry_utc=new_expiry)

    try:
        time_min, time_max = day_range_iso(settings.user_timezone, date)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    data = await list_events(tok.access_token, time_min, time_max)

    items = data.get("items", [])
    events = []
    for it in items:
        start = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
        end = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
        events.append({
            "id": it.get("id"),
            "summary": it.get("summary"),
            "start": start,
            "end": end,
            "status": it.get("status"),
        })

    return {"date": date, "timezone": settings.user_timezone, "events": events}

@router.post("/free-slots")
async def free_slots(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    payload:
      date: "YYYY-MM-DD" (optional; default today in user TZ)
      duration_min: 30
      work_start: "09:00"
      work_end: "18:00"
      buffer_min: 10
      max_slots: 3
    """
    repo = GoogleTokensRepo()
    tok = await repo.get_latest(db)
    if not tok:
        raise HTTPException(status_code=401, detail="Google Calendar not connected. Visit /oauth/google/start")

    # refresh if needed
    if tok.expiry_utc and datetime.utcnow() > (tok.expiry_utc - timedelta(seconds=30)):
        if not tok.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token. Reconnect via /oauth/google/start")
        refreshed = await refresh_access_token(tok.refresh_token)
        new_access = refreshed["access_token"]
        new_expiry = compute_expiry_utc(refreshed.get("expires_in"))
        tok = await repo.update_access(db, tok, access_token=new_access, expiry_utc=new_expiry)

    tz = ZoneInfo(settings.user_timezone)
    today = datetime.now(tz).date().isoformat()

    date_iso = payload.get("date", today)
    duration_min = int(payload.get("duration_min", 30))
    work_start = payload.get("work_start", "09:00")
    work_end = payload.get("work_end", "18:00")
    buffer_min = int(payload.get("buffer_min", 10))
    max_slots = int(payload.get("max_slots", 3))

    # list events for that day
    # reuse today_range_iso but for custom day:
    day_start = datetime.fromisoformat(date_iso).replace(tzinfo=tz).replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    time_min = day_start.isoformat()
    time_max = day_end.isoformat()

    data = await list_events(tok.access_token, time_min, time_max)
    items = data.get("items", [])
    events = []
    for it in items:
        start = (it.get("start") or {}).get("dateTime") or (it.get("start") or {}).get("date")
        end = (it.get("end") or {}).get("dateTime") or (it.get("end") or {}).get("date")
        events.append({"start": start, "end": end})

    slots = find_free_slots(
        events=events,
        tz_name=settings.user_timezone,
        date_iso=date_iso,
        duration_min=duration_min,
        work_start=work_start,
        work_end=work_end,
        buffer_min=buffer_min,
        max_slots=max_slots,
    )

    return {"date": date_iso, "timezone": settings.user_timezone, "slots": [s.__dict__ for s in slots]}


@router.post("/create")
async def create_calendar_event(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    payload:
      date: "YYYY-MM-DD"
      start_time: "HH:MM"
      duration_min: 30
      title: "Meeting title"
    """
    repo = GoogleTokensRepo()
    tok = await repo.get_latest(db)
    if not tok:
        raise HTTPException(status_code=401, detail="Google Calendar not connected. Visit /oauth/google/start")

    if tok.expiry_utc and datetime.utcnow() > (tok.expiry_utc - timedelta(seconds=30)):
        if not tok.refresh_token:
            raise HTTPException(status_code=401, detail="No refresh token. Reconnect via /oauth/google/start")
        refreshed = await refresh_access_token(tok.refresh_token)
        new_access = refreshed["access_token"]
        new_expiry = compute_expiry_utc(refreshed.get("expires_in"))
        tok = await repo.update_access(db, tok, access_token=new_access, expiry_utc=new_expiry)

    date_iso = payload.get("date")
    start_time = payload.get("start_time")
    duration_min = payload.get("duration_min")
    title = payload.get("title")

    if not date_iso or not start_time or not duration_min or not title:
        raise HTTPException(status_code=400, detail="Missing required fields: date, start_time, duration_min, title")

    try:
        duration_min = int(duration_min)
        if duration_min <= 0:
            raise ValueError("duration_min must be > 0")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid duration_min")

    tz = ZoneInfo(settings.user_timezone)
    try:
        day = datetime.fromisoformat(date_iso).date()
        start_hour, start_minute = map(int, start_time.split(":"))
        start_dt = datetime.combine(day, time(start_hour, start_minute), tzinfo=tz)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date or start_time format")

    end_dt = start_dt + timedelta(minutes=duration_min)

    created = await create_event(
        tok.access_token,
        summary=title,
        start_iso=start_dt.isoformat(),
        end_iso=end_dt.isoformat(),
    )

    return {
        "timezone": settings.user_timezone,
        "event": {
            "id": created.get("id"),
            "summary": created.get("summary"),
            "start": (created.get("start") or {}).get("dateTime"),
            "end": (created.get("end") or {}).get("dateTime"),
            "status": created.get("status"),
            "htmlLink": created.get("htmlLink"),
        },
    }
