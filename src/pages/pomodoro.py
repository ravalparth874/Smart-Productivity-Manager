"""Pomodoro focus timer with customisable sessions and logging."""

from __future__ import annotations

import time

import streamlit as st
import streamlit.components.v1 as components

from src import database as db, styles
from src.utils import flash

MODE_FOCUS = "Focus"
MODE_SHORT = "Short Break"
MODE_LONG = "Long Break"
MODES = [MODE_FOCUS, MODE_SHORT, MODE_LONG]


def _format_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _mode_minutes(mode: str) -> int:
    if mode == MODE_SHORT:
        return db.get_int_setting("pomodoro_short_break", 5)
    if mode == MODE_LONG:
        return db.get_int_setting("pomodoro_long_break", 15)
    return db.get_int_setting("pomodoro_focus", 25)


def _ensure_state() -> None:
    defaults = {
        "pomo_running": False,
        "pomo_end": 0.0,
        "pomo_paused": 0.0,
        "pomo_logged": True,
        "pomo_mode": MODE_FOCUS,
        "pomo_duration": db.get_int_setting("pomodoro_focus", 25),
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _start(mode: str) -> None:
    minutes = _mode_minutes(mode)
    st.session_state.pomo_mode = mode
    st.session_state.pomo_duration = minutes
    st.session_state.pomo_end = time.time() + minutes * 60
    st.session_state.pomo_running = True
    st.session_state.pomo_paused = 0.0
    st.session_state.pomo_logged = False


def _pause() -> None:
    remaining = max(0.0, st.session_state.pomo_end - time.time())
    st.session_state.pomo_paused = remaining
    st.session_state.pomo_running = False


def _resume() -> None:
    st.session_state.pomo_end = time.time() + st.session_state.pomo_paused
    st.session_state.pomo_paused = 0.0
    st.session_state.pomo_running = True


def _reset() -> None:
    st.session_state.pomo_running = False
    st.session_state.pomo_end = 0.0
    st.session_state.pomo_paused = 0.0
    st.session_state.pomo_logged = True


def _beep() -> None:
    components.html(
        """
        <script>
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain); gain.connect(ctx.destination);
            osc.type = "sine"; osc.frequency.value = 880;
            gain.gain.setValueAtTime(0.001, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 1.1);
            osc.start(); osc.stop(ctx.currentTime + 1.2);
        } catch (e) {}
        </script>
        """,
        height=0,
    )


def _complete_session() -> None:
    """Log the finished session and prepare the next one."""
    mode = st.session_state.pomo_mode
    minutes = st.session_state.pomo_duration
    task_id = st.session_state.get("pomo_task_id")

    try:
        db.log_pomodoro(task_id if task_id else None, mode, minutes)
    except Exception as exc:  # pragma: no cover - defensive
        st.error(f"Could not log session: {exc}")

    _beep()
    st.session_state.pomo_logged = True
    st.session_state.pomo_running = False
    st.session_state.pomo_end = 0.0

    if mode == MODE_FOCUS:
        done_today = db.focus_sessions_today()
        every = max(1, db.get_int_setting("sessions_before_long_break", 4))
        next_mode = MODE_LONG if done_today % every == 0 else MODE_SHORT
        st.session_state.pomo_mode = next_mode
        st.session_state.pomo_duration = _mode_minutes(next_mode)
        st.toast(f"Focus session complete. Time for a {next_mode.lower()}.")
        st.balloons()
    else:
        st.session_state.pomo_mode = MODE_FOCUS
        st.session_state.pomo_duration = _mode_minutes(MODE_FOCUS)
        st.toast("Break finished. Ready for the next focus block?")


@st.fragment(run_every=1.0)
def _live_timer() -> None:
    """Auto-refreshing countdown that logs the session when it hits zero."""
    remaining = max(0.0, st.session_state.pomo_end - time.time())
    total = max(1, st.session_state.pomo_duration * 60)
    elapsed = total - remaining

    st.markdown(
        f'<div class="pomo-wrap">'
        f'<div class="pomo-clock">{_format_time(remaining)}</div>'
        f'<div class="pomo-mode">{st.session_state.pomo_mode}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(styles.progress_bar(elapsed / total * 100), unsafe_allow_html=True)

    if remaining <= 0 and not st.session_state.pomo_logged:
        _complete_session()
        st.rerun(scope="app")


def _render_settings() -> None:
    with st.expander("Timer settings", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        focus = col1.number_input("Focus (min)", min_value=1, max_value=180,
                                  value=db.get_int_setting("pomodoro_focus", 25))
        short = col2.number_input("Short break (min)", min_value=1, max_value=60,
                                  value=db.get_int_setting("pomodoro_short_break", 5))
        long_break = col3.number_input("Long break (min)", min_value=1, max_value=90,
                                       value=db.get_int_setting("pomodoro_long_break", 15))
        every = col4.number_input("Sessions before long break", min_value=1, max_value=12,
                                  value=db.get_int_setting("sessions_before_long_break", 4))
        if st.button("Save settings", type="primary"):
            db.set_setting("pomodoro_focus", int(focus))
            db.set_setting("pomodoro_short_break", int(short))
            db.set_setting("pomodoro_long_break", int(long_break))
            db.set_setting("sessions_before_long_break", int(every))
            if not st.session_state.pomo_running:
                st.session_state.pomo_duration = _mode_minutes(st.session_state.pomo_mode)
            flash("Settings saved.")
            st.rerun()


def render() -> None:
    _ensure_state()
    styles.page_header("Pomodoro", "Focus in deep-work sprints and track every minute.")

    _render_settings()

    pending_tasks = db.list_tasks(status="Pending", sort_by="priority")
    task_options = {0: "- No task linked -", **{t["id"]: t["title"] for t in pending_tasks}}
    st.selectbox(
        "Link this session to a task (optional)",
        options=list(task_options.keys()),
        format_func=lambda key: task_options[key],
        key="pomo_task_id",
        help="Time spent is logged as a focus session; the task stays on your board.",
    )

    st.write("Session type")
    mode_cols = st.columns(3)
    for column, name in zip(mode_cols, MODES):
        is_active = st.session_state.pomo_mode == name
        if column.button(
            name,
            key=f"mode_select_{name}",
            type="primary" if is_active else "secondary",
            disabled=st.session_state.pomo_running,
            width="stretch",
        ):
            st.session_state.pomo_mode = name
            st.session_state.pomo_duration = _mode_minutes(name)
            st.session_state.pomo_end = 0.0
            st.session_state.pomo_paused = 0.0
            st.rerun()

    if st.session_state.pomo_running:
        _live_timer()
    else:
        preview_seconds = st.session_state.pomo_paused or st.session_state.pomo_duration * 60
        st.markdown(
            f'<div class="pomo-wrap">'
            f'<div class="pomo-clock">{_format_time(preview_seconds)}</div>'
            f'<div class="pomo-mode">{st.session_state.pomo_mode} - ready</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(styles.progress_bar(0), unsafe_allow_html=True)

    # ---- Controls -----------------------------------------------------
    col1, col2, col3 = st.columns(3)
    if st.session_state.pomo_running:
        if col1.button("Pause", width="stretch", type="primary"):
            _pause()
            st.rerun()
    elif st.session_state.pomo_paused > 0:
        if col1.button("Resume", width="stretch", type="primary"):
            _resume()
            st.rerun()
    else:
        if col1.button("Start session", width="stretch", type="primary"):
            _start(st.session_state.pomo_mode)
            st.rerun()

    if col2.button("Reset", width="stretch"):
        _reset()
        st.rerun()

    if col3.button("Skip / mark done", width="stretch"):
        if not st.session_state.pomo_logged:
            _complete_session()
        else:
            _reset()
        st.rerun()

    st.write("")
    # ---- Session stats ------------------------------------------------
    sessions_today = db.focus_sessions_today()
    minutes_today = db.focus_minutes_today()
    total_sessions = db.total_focus_sessions()

    styles.render_stat_grid([
        styles.stat_card("Focus Sessions Today", sessions_today, "Completed pomodoros", styles.PRIMARY),
        styles.stat_card("Focus Minutes Today", minutes_today, "Deep work logged", styles.CYAN),
        styles.stat_card("Total Sessions", total_sessions, "All time", styles.SUCCESS),
        styles.stat_card("Current Streak", db.current_streak(), "Active days", styles.WARNING),
    ], columns=4)
