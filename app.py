"""Smart Productivity Manager - Streamlit entry point.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src import database as db, styles
from src.pages import analytics, dashboard, goals, pomodoro, tasks
from src.utils import render_flashes

st.set_page_config(
    page_title="Smart Productivity Manager",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "Dashboard": dashboard.render,
    "Tasks": tasks.render,
    "Pomodoro": pomodoro.render,
    "Goals & Streaks": goals.render,
    "Analytics": analytics.render,
}


def _sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">'
            '<div class="logo">SP</div>'
            '<div><div class="name">Productivity</div>'
            '<div class="sub">SMART MANAGER</div></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        choice = st.radio(
            "Navigation",
            list(PAGES.keys()),
            label_visibility="collapsed",
            key="nav",
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        stats = db.task_stats()
        st.markdown(
            f'<div class="panel" style="padding:0.85rem 0.95rem;">'
            f'<div class="muted" style="font-size:0.76rem;text-transform:uppercase;'
            f'letter-spacing:0.07em;">Quick stats</div>'
            f'<div style="margin-top:0.5rem;font-size:0.86rem;line-height:1.7;">'
            f'Pending: <strong>{stats["pending"]}</strong><br>'
            f'Overdue: <strong style="color:{styles.DANGER};">{stats["overdue"]}</strong><br>'
            f'Streak: <strong>{db.current_streak()} day(s)</strong><br>'
            f'Focus today: <strong>{db.focus_minutes_today()} min</strong>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        st.caption("Data stored locally in data/productivity.db")

    return choice


def main() -> None:
    db.init_db()
    styles.inject_css()

    choice = _sidebar()
    render_flashes()
    PAGES[choice]()


if __name__ == "__main__":
    main()
