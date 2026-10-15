"""Daily goals, study sessions and streak tracking."""

from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from src import charts, database as db, styles
from src.utils import flash


def _streak_activity_strip(days: int = 14) -> str:
    active = db.activity_dates()
    cells = []
    for offset in range(days - 1, -1, -1):
        day = date.today() - timedelta(days=offset)
        is_active = day in active
        color = styles.SUCCESS if is_active else "rgba(255,255,255,0.08)"
        border = styles.PRIMARY if day == date.today() else "transparent"
        cells.append(
            f'<div title="{day.strftime("%b %d")}" style="flex:1;height:34px;border-radius:8px;'
            f'background:{color};border:2px solid {border};"></div>'
        )
    return f'<div style="display:flex;gap:5px;">{"".join(cells)}</div>'


def _render_streak() -> None:
    current = db.current_streak()
    longest = db.longest_streak()
    active_days = len(db.activity_dates())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="streak-hero"><div class="num">{current}</div>'
            f'<div class="cap">Current streak (days)</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="streak-hero"><div class="num">{longest}</div>'
            f'<div class="cap">Longest streak (days)</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="streak-hero"><div class="num">{active_days}</div>'
            f'<div class="cap">Total active days</div></div>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.markdown('<div class="panel"><h3>Last 14 days</h3>', unsafe_allow_html=True)
    st.markdown(_streak_activity_strip(), unsafe_allow_html=True)
    st.markdown(
        '<div class="muted" style="margin-top:0.6rem;">A day turns green when you complete a task '
        'or log a focus / study session.</div></div>',
        unsafe_allow_html=True,
    )


def _render_daily_goal() -> None:
    today = date.today()
    goal = db.get_daily_goal(today)
    target_tasks = goal["target_tasks"] if goal else db.get_int_setting("daily_task_goal", 5)
    target_minutes = goal["target_minutes"] if goal else db.get_int_setting("daily_focus_goal", 120)
    note = goal["note"] if goal else ""

    stats = db.task_stats()
    done_tasks = stats["completed_today"]
    focus_minutes = db.focus_minutes_today()

    st.markdown('<div class="panel"><h3>Today\'s goal</h3>', unsafe_allow_html=True)
    with st.form("daily_goal_form"):
        col1, col2 = st.columns(2)
        new_tasks = col1.number_input("Target tasks completed", min_value=0, max_value=50, value=int(target_tasks))
        new_minutes = col2.number_input("Target focus minutes", min_value=0, max_value=1440, step=15, value=int(target_minutes))
        new_note = st.text_input("Focus note", value=note, placeholder="What matters most today?")
        if st.form_submit_button("Save today's goal", type="primary"):
            db.set_daily_goal(today, int(new_tasks), int(new_minutes), new_note)
            flash("Daily goal saved.")
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.plotly_chart(
        charts.goal_progress([done_tasks, focus_minutes], [int(target_tasks) or 1, int(target_minutes) or 1]),
        width="stretch",
        config={"displayModeBar": False},
    )


def _render_goal_history() -> None:
    goals = db.list_daily_goals(14)
    st.markdown('<div class="panel"><h3>Goal history</h3>', unsafe_allow_html=True)
    if not goals:
        st.markdown('<div class="muted">No goals saved yet.</div>', unsafe_allow_html=True)
    else:
        for goal in goals:
            note = f" - {goal['note']}" if goal.get("note") else ""
            st.markdown(
                f'<div class="task-row" style="--accent:{styles.CYAN};">'
                f'<div style="flex:1;"><div class="task-title">{goal["goal_date"]}</div>'
                f'<div class="task-desc">{goal["target_tasks"]} tasks / '
                f'{goal["target_minutes"]} min{note}</div></div></div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def _render_study_sessions() -> None:
    st.markdown('<div class="panel"><h3>Log a study session</h3>', unsafe_allow_html=True)
    with st.form("study_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        subject = col1.text_input("Subject", placeholder="e.g. Python, Algebra")
        minutes = col2.number_input("Minutes", min_value=1, max_value=600, value=30, step=5)
        session_date = col3.date_input("Date", value=date.today())
        notes = st.text_input("Notes (optional)")
        if st.form_submit_button("Add study session", type="primary"):
            try:
                db.add_study_session(subject, int(minutes), session_date, notes)
                flash("Study session logged.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)

    sessions = db.list_study_sessions(20)
    st.markdown('<div class="panel"><h3>Recent study sessions</h3>', unsafe_allow_html=True)
    if not sessions:
        st.markdown('<div class="muted">Nothing logged yet.</div>', unsafe_allow_html=True)
    else:
        header = st.columns([3, 1.4, 1.6, 0.9])
        header[0].caption("Subject")
        header[1].caption("Minutes")
        header[2].caption("Date")
        header[3].caption("")
        for session in sessions:
            row = st.columns([3, 1.4, 1.6, 0.9])
            row[0].write(session["subject"])
            row[1].write(f'{session["minutes"]} min')
            row[2].write(session["session_date"])
            if row[3].button("Del", key=f"del_study_{session['id']}", width="stretch"):
                st.session_state["delete_study_id"] = session["id"]
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    delete_id = st.session_state.get("delete_study_id")
    if delete_id:
        with st.container(border=True):
            st.warning("Delete this study session? This cannot be undone.")
            c1, c2 = st.columns(2)
            if c1.button("Yes, delete", key="confirm_del_study", type="primary", width="stretch"):
                db.delete_study_session(delete_id)
                st.session_state.pop("delete_study_id", None)
                st.rerun()
            if c2.button("Keep", key="cancel_del_study", width="stretch"):
                st.session_state.pop("delete_study_id", None)
                st.rerun()


def render() -> None:
    styles.page_header("Goals & Streaks", "Build momentum with daily targets and study tracking.")
    _render_streak()
    st.write("")

    left, right = st.columns([1, 1], gap="large")
    with left:
        _render_daily_goal()
    with right:
        _render_goal_history()

    _render_study_sessions()
