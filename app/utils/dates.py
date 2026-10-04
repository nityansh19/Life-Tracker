from __future__ import annotations

from datetime import date, datetime, timedelta


def today_iso() -> str:
    return date.today().isoformat()


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def format_short(value: str) -> str:
    return parse_date(value).strftime("%d %b")


def previous_days(days: int, include_today: bool = True) -> list[date]:
    start = date.today() if include_today else date.today() - timedelta(days=1)
    return [start - timedelta(days=offset) for offset in range(days)]
