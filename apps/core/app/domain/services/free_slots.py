from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo

@dataclass(frozen=True)
class Slot:
    start: str
    end: str

def _parse_iso(dt: str) -> datetime:
    # dt from Google includes timezone offset; datetime.fromisoformat handles it
    return datetime.fromisoformat(dt)

def find_free_slots(
    *,
    events: list[dict],
    tz_name: str,
    date_iso: str,           # "2026-02-08"
    duration_min: int,
    work_start: str = "09:00",
    work_end: str = "18:00",
    buffer_min: int = 10,
    max_slots: int = 3,
) -> list[Slot]:
    tz = ZoneInfo(tz_name)

    ws_h, ws_m = map(int, work_start.split(":"))
    we_h, we_m = map(int, work_end.split(":"))

    day = datetime.fromisoformat(date_iso).date()
    day_start = datetime.combine(day, time(ws_h, ws_m), tzinfo=tz)
    day_end = datetime.combine(day, time(we_h, we_m), tzinfo=tz)

    dur = timedelta(minutes=duration_min)
    buf = timedelta(minutes=buffer_min)

    # Build busy intervals (clipped to workday)
    busy: list[tuple[datetime, datetime]] = []
    for e in events:
        s = e.get("start")
        en = e.get("end")
        if not s or not en:
            continue

        # All-day events come as "YYYY-MM-DD". Skip for now (v0.1).
        if len(s) == 10 or len(en) == 10:
            continue

        a = _parse_iso(s).astimezone(tz)
        b = _parse_iso(en).astimezone(tz)

        # clamp to work window
        a2 = max(a, day_start)
        b2 = min(b, day_end)
        if b2 <= a2:
            continue

        # add buffer around meetings
        busy.append((a2 - buf, b2 + buf))

    busy.sort(key=lambda x: x[0])

    # merge overlaps
    merged: list[tuple[datetime, datetime]] = []
    for a, b in busy:
        if not merged or a > merged[-1][1]:
            merged.append((a, b))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))

    # free intervals
    slots: list[Slot] = []
    cursor = day_start
    for a, b in merged:
        if a > cursor:
            # free block: cursor..a
            start = cursor
            end = a
            # pick earliest slot inside free block
            if end - start >= dur:
                slots.append(Slot(start=start.isoformat(), end=(start + dur).isoformat()))
                if len(slots) >= max_slots:
                    return slots
        cursor = max(cursor, b)

    # tail free block
    if day_end > cursor and day_end - cursor >= dur and len(slots) < max_slots:
        start = cursor
        slots.append(Slot(start=start.isoformat(), end=(start + dur).isoformat()))

    return slots
