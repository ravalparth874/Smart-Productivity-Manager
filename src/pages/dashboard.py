"""Dashboard: at-a-glance productivity overview."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from src import charts, database as db, styles
from src.utils import collect_notifications, deadline_label


def _greeting() -> str:
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


def _render_notifications() -> None:
    notices = collect_notifications()
    if not notices:
        return
    with st.expander(f"Notifications ({len(notices)})", expanded=True):
        for notice in notices:
            text = f"**{notice['title']}** - {notice['message']}"
            if notice["level"] == "error":
                st.error(text)
            elif notice["level"] == "warning":
                st.warning(text)
            else:
                st.info(text)


def _task_row(task: dict) -> str:
    completed = task.get("status") == "Completed"
    priority = task.get("priority", "Medium")
    accent = styles.PRIORITY_COLORS.get(priority, styles.PRIMARY)
    status_color = styles.STATUS_COLORS.get(task.get("status", "Pending"), styles.MUTED)

    badges = [
        styles.badge(f"{priority} priority", accent),
        styles.badge(task.get("status", "Pending"), status_color),
    ]
    if task.get("deadline"):
        dl_color = styles.DANGER if db.is_overdue(task) else styles.MUTED
        badges.append(styles.badge(deadline_label(task["deadline"], completed), dl_color))

    return (
        f'<div class="task-row {"done" if completed else ""}" style="--accent:{accent};">'
        f'<div style="flex:1;">'
        f'<div class="task-title">{task["title"]}</div>'
        f'<div class="task-meta">{"".join(badges)}</div>'
        f"</div></div>"
    )


def render() -> None:
    stats = db.task_stats()
    streak = db.current_streak()
    focus_today = db.focus_minutes_today()
    sessions_today = db.focus_sessions_today()

    st.markdown(
        f'<div class="page-title">{_greeting()}</div>'
        f'<div class="page-subtitle">{date.today().strftime("%A, %B %d, %Y")}'
        f' &nbsp;|&nbsp; current streak: {streak} day(s)</div>',
        unsafe_allow_html=True,
    )

    _render_notifications()

    # ---- Metric cards -------------------------------------------------
    cards = [
        styles.stat_card("Total Tasks", stats["total"], "All tasks in workspace", styles.PRIMARY),
        styles.stat_card("Completed", stats["completed"], f'{stats["completed_today"]} finished today', styles.SUCCESS),
        styles.stat_card("Pending", stats["pending"], "Still to do", styles.CYAN),
        styles.stat_card("Overdue", stats["overdue"], "Past deadline", styles.DANGER),
        styles.stat_card("Daily Progress", f'{stats["daily_progress"]}%', f'{stats["completed_today"]} of {stats["completed_today"] + stats["due_today_pending"]} due', styles.WARNING),
    ]
    styles.render_stat_grid(cards, columns=5)

    st.write("")

    # ---- Progress + goals --------------------------------------------
    left, right = st.columns([1, 1.15], gap="large")

    with left:
        st.markdown('<div class="panel"><h3>Today\'s Progress</h3>', unsafe_allow_html=True)
        st.markdown(styles.progress_bar(stats["daily_progress"]), unsafe_allow_html=True)
        st.markdown(
            f'<div class="muted" style="margin-top:0.6rem;">'
            f'{stats["completed_today"]} task(s) completed today, '
            f'{stats["due_today_pending"]} still due today.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        goal = db.get_daily_goal(date.today())
        target_tasks = goal["target_tasks"] if goal else db.get_int_setting("daily_task_goal", 5)
        target_minutes = goal["target_minutes"] if goal else db.get_int_setting("daily_focus_goal", 120)

        st.markdown('<div class="panel"><h3>Daily Goals</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="muted">{stats["completed_today"]} / {target_tasks} tasks &nbsp;&nbsp; '
            f'{focus_today} / {target_minutes} focus minutes</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.goal_progress(
                [stats["completed_today"], focus_today],
                [target_tasks, target_minutes],
            ),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><h3>Focus Today</h3>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="muted">{sessions_today} focus session(s) - '
            f'{focus_today} minutes of deep work.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel"><h3>Weekly Productivity</h3>', unsafe_allow_html=True)
        completed = db.tasks_completed_per_day(7)
        st.plotly_chart(
            charts.weekly_completion_chart(completed),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><h3>Deadline Radar</h3>', unsafe_allow_html=True)
        upcoming = db.upcoming_deadlines(within_days=5)
        if not upcoming:
            st.markdown('<div class="muted">No deadlines in the next 5 days. Clear sky.</div>', unsafe_allow_html=True)
        else:
            for task in upcoming[:5]:
                st.markdown(_task_row(task), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Recent tasks -------------------------------------------------
    st.markdown('<div class="panel"><h3>Recent Tasks</h3>', unsafe_allow_html=True)
    tasks = db.list_tasks(status="Pending", sort_by="created_at")[:5]
    if not tasks:
        st.markdown('<div class="muted">No pending tasks. Add one from the Tasks page.</div>', unsafe_allow_html=True)
    else:
        for task in tasks:
            st.markdown(_task_row(task), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
