"""Interactive charts and productivity statistics."""

from __future__ import annotations

import streamlit as st

from src import charts, database as db, styles


def render() -> None:
    styles.page_header("Analytics", "Visualise your productivity trends and task mix.")

    stats = db.task_stats()
    completion_rate = 0 if stats["total"] == 0 else round(stats["completed"] / stats["total"] * 100)

    styles.render_stat_grid([
        styles.stat_card("Completion Rate", f"{completion_rate}%", f'{stats["completed"]}/{stats["total"]} tasks', styles.SUCCESS),
        styles.stat_card("Focus Sessions", db.total_focus_sessions(), "Pomodoro sessions", styles.PRIMARY),
        styles.stat_card("Study Minutes", db.total_study_minutes(), "Logged study time", styles.CYAN),
        styles.stat_card("Longest Streak", db.longest_streak(), "Consecutive active days", styles.WARNING),
    ], columns=4)

    st.write("")

    completed = db.tasks_completed_per_day(7)
    focus = db.focus_minutes_per_day(7)

    st.markdown('<div class="panel"><h3>Weekly activity</h3>', unsafe_allow_html=True)
    st.plotly_chart(
        charts.weekly_activity_combo(completed, focus),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="panel"><h3>Tasks by category</h3>', unsafe_allow_html=True)
        all_tasks = db.list_tasks()
        if all_tasks:
            st.plotly_chart(
                charts.category_donut(all_tasks),
                width="stretch",
                config={"displayModeBar": False},
            )
        else:
            st.markdown('<div class="muted">No tasks yet.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><h3>Tasks by priority</h3>', unsafe_allow_html=True)
        if all_tasks:
            st.plotly_chart(
                charts.priority_bar(all_tasks),
                width="stretch",
                config={"displayModeBar": False},
            )
        else:
            st.markdown('<div class="muted">No tasks yet.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel"><h3>Overall completion</h3>', unsafe_allow_html=True)
        st.plotly_chart(
            charts.status_gauge(stats["completed"], stats["total"]),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="panel"><h3>Focus minutes (7 days)</h3>', unsafe_allow_html=True)
        st.plotly_chart(
            charts.focus_minutes_chart(focus),
            width="stretch",
            config={"displayModeBar": False},
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Summary table ------------------------------------------------
    st.markdown('<div class="panel"><h3>Summary</h3>', unsafe_allow_html=True)
    rows = {
        "Total tasks": stats["total"],
        "Completed": stats["completed"],
        "Pending": stats["pending"],
        "Overdue": stats["overdue"],
        "Completed today": stats["completed_today"],
        "Daily progress": f'{stats["daily_progress"]}%',
        "Current streak": f'{db.current_streak()} day(s)',
        "Focus minutes today": db.focus_minutes_today(),
        "Total study minutes": db.total_study_minutes(),
    }
    col_a, col_b = st.columns(2)
    items = list(rows.items())
    for index, (label, value) in enumerate(items):
        target = col_a if index % 2 == 0 else col_b
        target.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:0.35rem 0;'
            f'border-bottom:1px solid {styles.BORDER};"><span class="muted">{label}</span>'
            f'<strong>{value}</strong></div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
