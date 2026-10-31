from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from dateutil import parser as dateparser

from egnooz import TIMEZONE_NAME

MELBOURNE = ZoneInfo(TIMEZONE_NAME)


def now_melbourne() -> datetime:
    return datetime.now(MELBOURNE)


def today_melbourne(now: datetime | None = None) -> date:
    return (now or now_melbourne()).astimezone(MELBOURNE).date()


def parse_datetime(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = dateparser.parse(str(value))
        except (OverflowError, ValueError, TypeError):
            return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MELBOURNE)
    return dt.astimezone(MELBOURNE)


def isoformat(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(MELBOURNE).isoformat(timespec="seconds")


def format_long_date(value: date | datetime | str) -> str:
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    if isinstance(value, datetime):
        value = value.astimezone(MELBOURNE).date()
    return f"{value.strftime('%A')} {value.day} {value.strftime('%B')} {value.year}"


def format_clock(dt: datetime) -> str:
    local = dt.astimezone(MELBOURNE)
    hour = local.strftime("%I").lstrip("0") or "12"
    return f"{hour}:{local.strftime('%M')} {local.strftime('%p').lower()}"


def format_item_time(value: str | None) -> str:
    dt = parse_datetime(value)
    if dt is None:
        return "Time not given"
    return f"{format_long_date(dt)}, {format_clock(dt)}"


def start_of_day(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=MELBOURNE)
