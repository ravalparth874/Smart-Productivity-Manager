"""SQLite3 persistence layer for the Smart Productivity Manager.

All database access goes through this module. Every public function opens a
short-lived connection, so the Streamlit UI can call them freely without
worrying about thread-safety or stale connections.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterator, Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "productivity.db"

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Completed"]
DEFAULT_CATEGORIES = ["General", "Work", "Study", "Personal", "Health", "Finance"]

DEFAULT_SETTINGS: dict[str, str] = {
    "pomodoro_focus": "25",
    "pomodoro_short_break": "5",
    "pomodoro_long_break": "15",
    "sessions_before_long_break": "4",
    "daily_task_goal": "5",
    "daily_focus_goal": "120",
}

_DATE_FMT = "%Y-%m-%d"
_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection that is always closed afterwards."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_db() -> None:
    """Create tables and seed default settings. Safe to call repeatedly."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                category TEXT DEFAULT 'General',
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Pending',
                deadline TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS pomodoro_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                mode TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                finished_at TEXT NOT NULL,
                session_date TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                notes TEXT DEFAULT '',
                session_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS daily_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_date TEXT NOT NULL UNIQUE,
                target_tasks INTEGER DEFAULT 0,
                target_minutes INTEGER DEFAULT 0,
                note TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
            CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks (deadline);
            CREATE INDEX IF NOT EXISTS idx_pomodoro_date ON pomodoro_sessions (session_date);
            """
        )
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )


# ---------------------------------------------------------------------------
# Small date helpers
# ---------------------------------------------------------------------------


def today_str() -> str:
    return date.today().strftime(_DATE_FMT)


def now_str() -> str:
    return datetime.now().strftime(_DATETIME_FMT)


def _as_date(value: Any) -> Optional[date]:
    """Best-effort conversion of a stored value to a ``date``."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in (_DATE_FMT, _DATETIME_FMT, "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def get_setting(key: str, default: str | None = None) -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return default if default is not None else DEFAULT_SETTINGS.get(key, "")
    return row["value"]


def get_int_setting(key: str, default: int = 0) -> int:
    try:
        return int(float(get_setting(key, str(default))))
    except (TypeError, ValueError):
        return default


def set_setting(key: str, value: Any) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )


def get_all_settings() -> dict[str, str]:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


# ---------------------------------------------------------------------------
# Task CRUD
# ---------------------------------------------------------------------------


def add_task(
    title: str,
    description: str = "",
    category: str = "General",
    priority: str = "Medium",
    deadline: Any = None,
    status: str = "Pending",
) -> int:
    title = (title or "").strip()
    if not title:
        raise ValueError("Task title cannot be empty.")
    if priority not in PRIORITIES:
        priority = "Medium"
    if status not in STATUSES:
        status = "Pending"

    deadline_str = None
    if deadline is not None and deadline != "":
        if isinstance(deadline, (date, datetime)):
            deadline_str = deadline.strftime(_DATE_FMT)
        else:
            deadline_str = str(deadline)

    completed_at = now_str() if status == "Completed" else None

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, category, priority, status,
                               deadline, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, category or "General", priority, status,
             deadline_str, now_str(), completed_at),
        )
        return int(cursor.lastrowid)


def update_task(task_id: int, **fields: Any) -> None:
    allowed = {"title", "description", "category", "priority", "status", "deadline"}
    updates: list[str] = []
    values: list[Any] = []

    for key, value in fields.items():
        if key not in allowed:
            continue
        if key == "deadline" and isinstance(value, (date, datetime)):
            value = value.strftime(_DATE_FMT)
        if key == "deadline" and value == "":
            value = None
        updates.append(f"{key} = ?")
        values.append(value)

    if not updates:
        return

    with get_connection() as conn:
        current = conn.execute("SELECT status, completed_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if current is None:
            return
        if "status" in fields:
            if fields["status"] == "Completed" and current["status"] != "Completed":
                updates.append("completed_at = ?")
                values.append(now_str())
            elif fields["status"] != "Completed":
                updates.append("completed_at = ?")
                values.append(None)

        values.append(task_id)
        conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", values)


def toggle_task_complete(task_id: int) -> None:
    with get_connection() as conn:
        row = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return
    new_status = "Pending" if row["status"] == "Completed" else "Completed"
    update_task(task_id, status=new_status)


def delete_task(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


def get_task(task_id: int) -> Optional[dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def list_tasks(
    search: str = "",
    category: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    sort_by: str = "created_at",
) -> list[dict[str, Any]]:
    """Return tasks matching the given filters."""
    sort_map = {
        "created_at": "created_at DESC",
        "deadline": "deadline IS NULL, deadline ASC",
        "priority": (
            "CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END ASC"
        ),
        "title": "title COLLATE NOCASE ASC",
        "status": "status ASC",
    }
    order = sort_map.get(sort_by, "created_at DESC")

    query = "SELECT * FROM tasks WHERE 1 = 1"
    params: list[Any] = []

    if search:
        query += " AND (title LIKE ? OR description LIKE ? OR category LIKE ?)"
        like = f"%{search.strip()}%"
        params.extend([like, like, like])
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)
    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    query += f" ORDER BY {order}"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return _rows_to_dicts(rows)


def get_categories() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM tasks WHERE category IS NOT NULL AND category != ''"
        ).fetchall()
    found = {row["category"] for row in rows}
    return sorted(found | set(DEFAULT_CATEGORIES))


def get_deadlines_map() -> dict[int, date]:
    """Return {task_id: deadline_date} for tasks that have a deadline."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, deadline FROM tasks WHERE deadline IS NOT NULL AND deadline != ''"
        ).fetchall()
    result: dict[int, date] = {}
    for row in rows:
        parsed = _as_date(row["deadline"])
        if parsed:
            result[row["id"]] = parsed
    return result


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


def is_overdue(task: dict[str, Any]) -> bool:
    if task.get("status") == "Completed":
        return False
    deadline = _as_date(task.get("deadline"))
    return deadline is not None and deadline < date.today()


def task_stats() -> dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    tasks = _rows_to_dicts(rows)

    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    overdue = sum(1 for t in tasks if is_overdue(t))
    pending = total - completed

    today = date.today()
    completed_today = 0
    due_today_pending = 0
    for task in tasks:
        completed_at = _as_date(task.get("completed_at"))
        if task["status"] == "Completed" and completed_at == today:
            completed_today += 1
        deadline = _as_date(task.get("deadline"))
        if deadline == today and task["status"] != "Completed":
            due_today_pending += 1

    denominator = completed_today + due_today_pending
    daily_progress = 100 if denominator == 0 else round(completed_today / denominator * 100)

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
        "completed_today": completed_today,
        "due_today_pending": due_today_pending,
        "daily_progress": daily_progress,
    }


def tasks_completed_per_day(days: int = 7) -> list[dict[str, Any]]:
    """Return a fixed-length window of daily completed-task counts."""
    start = date.today() - timedelta(days=days - 1)
    buckets = {start + timedelta(days=i): 0 for i in range(days)}

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT completed_at FROM tasks WHERE completed_at IS NOT NULL"
        ).fetchall()
    for row in rows:
        completed = _as_date(row["completed_at"])
        if completed in buckets:
            buckets[completed] += 1

    return [{"date": day, "count": count} for day, count in buckets.items()]


# ---------------------------------------------------------------------------
# Pomodoro + focus sessions
# ---------------------------------------------------------------------------


def log_pomodoro(task_id: Optional[int], mode: str, minutes: int) -> None:
    now = datetime.now()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO pomodoro_sessions (task_id, mode, minutes, finished_at, session_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, mode, int(minutes), now.strftime(_DATETIME_FMT), now.strftime(_DATE_FMT)),
        )


def focus_sessions_today() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM pomodoro_sessions WHERE mode = 'Focus' AND session_date = ?",
            (today_str(),),
        ).fetchone()
    return int(row["c"])


def focus_minutes_today() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(minutes), 0) AS m FROM pomodoro_sessions "
            "WHERE mode = 'Focus' AND session_date = ?",
            (today_str(),),
        ).fetchone()
    return int(row["m"])


def total_focus_sessions() -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM pomodoro_sessions WHERE mode = 'Focus'"
        ).fetchone()
    return int(row["c"])


def focus_minutes_per_day(days: int = 7) -> list[dict[str, Any]]:
    start = date.today() - timedelta(days=days - 1)
    buckets = {start + timedelta(days=i): 0 for i in range(days)}

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT session_date, minutes FROM pomodoro_sessions WHERE mode = 'Focus'"
        ).fetchall()
    for row in rows:
        day = _as_date(row["session_date"])
        if day in buckets:
            buckets[day] += int(row["minutes"])

    return [{"date": day, "minutes": minutes} for day, minutes in buckets.items()]


# ---------------------------------------------------------------------------
# Study sessions
# ---------------------------------------------------------------------------


def add_study_session(subject: str, minutes: int, session_date: Any = None, notes: str = "") -> int:
    subject = (subject or "").strip()
    if not subject:
        raise ValueError("Subject cannot be empty.")
    minutes = max(1, int(minutes))
    if session_date is None or session_date == "":
        date_str = today_str()
    elif isinstance(session_date, (date, datetime)):
        date_str = session_date.strftime(_DATE_FMT)
    else:
        date_str = str(session_date)

    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO study_sessions (subject, minutes, notes, session_date, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (subject, minutes, notes or "", date_str, now_str()),
        )
        return int(cursor.lastrowid)


def list_study_sessions(limit: int = 50) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM study_sessions ORDER BY session_date DESC, id DESC LIMIT ?",
            (int(limit),),
        ).fetchall()
    return _rows_to_dicts(rows)


def delete_study_session(session_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM study_sessions WHERE id = ?", (session_id,))


def total_study_minutes() -> int:
    with get_connection() as conn:
        row = conn.execute("SELECT COALESCE(SUM(minutes), 0) AS m FROM study_sessions").fetchone()
    return int(row["m"])


# ---------------------------------------------------------------------------
# Daily goals
# ---------------------------------------------------------------------------


def set_daily_goal(goal_date: Any, target_tasks: int, target_minutes: int, note: str = "") -> None:
    if isinstance(goal_date, (date, datetime)):
        date_str = goal_date.strftime(_DATE_FMT)
    else:
        date_str = str(goal_date)
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO daily_goals (goal_date, target_tasks, target_minutes, note)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(goal_date) DO UPDATE SET
                target_tasks = excluded.target_tasks,
                target_minutes = excluded.target_minutes,
                note = excluded.note
            """,
            (date_str, int(target_tasks), int(target_minutes), note or ""),
        )


def get_daily_goal(goal_date: Any) -> Optional[dict[str, Any]]:
    if isinstance(goal_date, (date, datetime)):
        date_str = goal_date.strftime(_DATE_FMT)
    else:
        date_str = str(goal_date)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM daily_goals WHERE goal_date = ?", (date_str,)).fetchone()
    return dict(row) if row else None


def list_daily_goals(limit: int = 14) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_goals ORDER BY goal_date DESC LIMIT ?", (int(limit),)
        ).fetchall()
    return _rows_to_dicts(rows)


# ---------------------------------------------------------------------------
# Streak tracking
# ---------------------------------------------------------------------------


def activity_dates() -> set[date]:
    """A day counts as 'active' if a task was completed or focus was logged."""
    days: set[date] = set()
    with get_connection() as conn:
        for row in conn.execute("SELECT completed_at FROM tasks WHERE completed_at IS NOT NULL"):
            day = _as_date(row["completed_at"])
            if day:
                days.add(day)
        for row in conn.execute("SELECT session_date FROM pomodoro_sessions WHERE mode = 'Focus'"):
            day = _as_date(row["session_date"])
            if day:
                days.add(day)
        for row in conn.execute("SELECT session_date FROM study_sessions"):
            day = _as_date(row["session_date"])
            if day:
                days.add(day)
    return days


def current_streak() -> int:
    """Number of consecutive active days ending today (or yesterday)."""
    days = activity_dates()
    if not days:
        return 0

    today = date.today()
    if today in days:
        cursor = today
    elif (today - timedelta(days=1)) in days:
        cursor = today - timedelta(days=1)
    else:
        return 0

    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def longest_streak() -> int:
    days = sorted(activity_dates())
    if not days:
        return 0
    best = 1
    run = 1
    for previous, current in zip(days, days[1:]):
        if current - previous == timedelta(days=1):
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


def upcoming_deadlines(within_days: int = 3) -> list[dict[str, Any]]:
    """Pending tasks whose deadline is today or within ``within_days`` days."""
    limit = date.today() + timedelta(days=within_days)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status != 'Completed' "
            "AND deadline IS NOT NULL AND deadline != '' ORDER BY deadline ASC"
        ).fetchall()
    result = []
    for row in rows:
        task = dict(row)
        deadline = _as_date(task["deadline"])
        if deadline is not None and deadline <= limit:
            task["days_left"] = (deadline - date.today()).days
            result.append(task)
    return result
