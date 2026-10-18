from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.config import settings


def now_tw() -> datetime:
    return datetime.now(ZoneInfo(settings.TIMEZONE))


def is_trading_day(d: date | None = None) -> bool:
    d = d or now_tw().date()
    return d.weekday() < 5 and d.isoformat() not in settings.holiday_set


def in_trading_hours() -> bool:
    n = now_tw()
    return is_trading_day(n.date()) and time(9, 0) <= n.time() <= time(13, 30)
