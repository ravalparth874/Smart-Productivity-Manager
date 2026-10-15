"""Small UI-independent helpers shared by the pages."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import streamlit as st

DATE_FMT = "%Y-%m-%d"


def flash(message: str, level: str = "success") -> None:
    """Queue a message that survives the next ``st.rerun()``."""
    st.session_state.setdefault("_flash", []).append((level, message))


def render_flashes() -> None:
    """Display and clear any queued flash messages."""
    for level, message in st.session_state.pop("_flash", []):
        getattr(st, level, st.info)(message)


def parse_date(value: Any) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in (DATE_FMT, "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


def pretty_date(value: Any) -> str:
    day = parse_date(value)
    return day.strftime("%b %d, %Y") if day else "-"


def deadline_label(value: Any, completed: bool = False) -> str:
    """Human-friendly deadline text such as 'Today' or '2 days left'."""
    day = parse_date(value)
    if day is None:
        return "No deadline"
    if completed:
        return day.strftime("%b %d")

    delta = (day - date.today()).days
    if delta < 0:
        return f"Overdue by {abs(delta)}d"
    if delta == 0:
        return "Due today"
    if delta == 1:
        return "Due tomorrow"
    return f"{delta} days left"


def collect_notifications() -> list[dict[str, str]]:
    """Return overdue and upcoming-deadline notices for the dashboard."""
    from src import database as db

    notices: list[dict[str, str]] = []
    for task in db.upcoming_deadlines(within_days=3):
        days_left = task.get("days_left", 0)
        if days_left < 0:
            notices.append({
                "level": "error",
                "title": "Overdue task",
                "message": f"'{task['title']}' was due {abs(days_left)} day(s) ago.",
            })
        elif days_left == 0:
            notices.append({
                "level": "warning",
                "title": "Due today",
                "message": f"'{task['title']}' is due today.",
            })
        else:
            notices.append({
                "level": "info",
                "title": "Upcoming deadline",
                "message": f"'{task['title']}' is due in {days_left} day(s).",
            })
    return notices


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))
