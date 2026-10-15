"""Centralised dark-theme styling and reusable HTML card helpers."""

from __future__ import annotations

import streamlit as st

# Colours used by both CSS and the Python card helpers.
BG = "#0b0e14"
SURFACE = "#141925"
SURFACE_2 = "#1b2233"
BORDER = "rgba(124, 92, 255, 0.18)"
TEXT = "#e6e9ef"
MUTED = "#93a0b4"
PRIMARY = "#7c5cff"
CYAN = "#22d3ee"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#ef4444"

PRIORITY_COLORS = {"High": DANGER, "Medium": WARNING, "Low": CYAN}
STATUS_COLORS = {"Completed": SUCCESS, "In Progress": WARNING, "Pending": MUTED}

_CSS = """
<style>
:root {
    --bg: #0b0e14;
    --surface: #141925;
    --surface-2: #1b2233;
    --border: rgba(124, 92, 255, 0.18);
    --text: #e6e9ef;
    --muted: #93a0b4;
    --primary: #7c5cff;
    --cyan: #22d3ee;
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
}

.stApp {
    background:
        radial-gradient(1200px 600px at 8% -5%, rgba(124, 92, 255, 0.16), transparent 55%),
        radial-gradient(900px 500px at 100% 0%, rgba(34, 211, 238, 0.10), transparent 50%),
        var(--bg);
    color: var(--text);
    font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
    padding-top: 1.6rem;
    padding-bottom: 3rem;
    max-width: 1180px;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #10141f 0%, #0c0f18 100%);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }

.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.35rem 0.2rem 1rem 0.2rem;
}
.sidebar-brand .logo {
    width: 42px; height: 42px;
    display: grid; place-items: center;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--primary), var(--cyan));
    font-size: 1.2rem;
    box-shadow: 0 8px 22px rgba(124, 92, 255, 0.35);
}
.sidebar-brand .name { font-weight: 700; font-size: 1.02rem; line-height: 1.1; }
.sidebar-brand .sub { color: var(--muted); font-size: 0.74rem; letter-spacing: 0.04em; }

/* Sidebar nav radio styled as menu items */
section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.25rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] > label {
    border-radius: 11px;
    padding: 0.5rem 0.7rem;
    transition: background 0.18s ease, transform 0.18s ease;
    border: 1px solid transparent;
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
    background: rgba(124, 92, 255, 0.10);
    transform: translateX(2px);
}
section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(135deg, rgba(124, 92, 255, 0.22), rgba(34, 211, 238, 0.12));
    border: 1px solid var(--border);
    box-shadow: inset 3px 0 0 var(--primary);
}

/* ---------- Headings ---------- */
.page-title {
    font-size: 1.72rem;
    font-weight: 800;
    letter-spacing: -0.01em;
    margin: 0 0 0.1rem 0;
}
.page-subtitle { color: var(--muted); font-size: 0.92rem; margin-bottom: 1.1rem; }

/* ---------- Metric cards ---------- */
.stat-grid { display: grid; gap: 1rem; margin-bottom: 0.4rem; }
.stat-card {
    position: relative;
    background: linear-gradient(160deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.05rem 1.15rem;
    overflow: hidden;
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.stat-card::after {
    content: "";
    position: absolute; inset: 0 auto 0 0;
    width: 4px;
    background: var(--accent, var(--primary));
}
.stat-card:hover {
    transform: translateY(-3px);
    border-color: rgba(124, 92, 255, 0.45);
    box-shadow: 0 14px 30px rgba(0, 0, 0, 0.45);
}
.stat-card .label {
    color: var(--muted);
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    font-weight: 600;
}
.stat-card .value {
    font-size: 1.95rem;
    font-weight: 800;
    line-height: 1.2;
    margin-top: 0.25rem;
    color: var(--text);
}
.stat-card .foot { color: var(--muted); font-size: 0.78rem; margin-top: 0.15rem; }

/* ---------- Generic panel ---------- */
.panel {
    background: linear-gradient(160deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 1rem;
}
.panel h3 { margin: 0 0 0.6rem 0; font-size: 1.02rem; }
.panel .muted { color: var(--muted); font-size: 0.86rem; }

/* ---------- Task rows ---------- */
.task-row {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    background: linear-gradient(160deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent, var(--primary));
    border-radius: 14px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.6rem;
    transition: transform 0.16s ease, border-color 0.16s ease;
}
.task-row:hover { transform: translateX(3px); border-color: rgba(124,92,255,0.42); }
.task-row.done { opacity: 0.62; }
.task-row.done .task-title { text-decoration: line-through; }
.task-title { font-weight: 650; font-size: 0.98rem; }
.task-desc { color: var(--muted); font-size: 0.84rem; margin-top: 0.15rem; }
.task-meta { margin-top: 0.4rem; display: flex; flex-wrap: wrap; gap: 0.4rem; }

.badge {
    display: inline-block;
    font-size: 0.72rem;
    font-weight: 600;
    padding: 0.16rem 0.6rem;
    border-radius: 999px;
    border: 1px solid transparent;
    white-space: nowrap;
}

/* ---------- Progress ---------- */
.progress-track {
    width: 100%;
    height: 12px;
    background: rgba(255, 255, 255, 0.07);
    border-radius: 999px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--primary), var(--cyan));
    transition: width 0.5s ease;
}

/* ---------- Pomodoro ---------- */
.pomo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1.6rem 1rem 1.2rem 1rem;
    border-radius: 20px;
    background: radial-gradient(circle at 50% 0%, rgba(124, 92, 255, 0.22), transparent 62%),
                linear-gradient(160deg, var(--surface-2), var(--surface));
    border: 1px solid var(--border);
    margin-bottom: 1rem;
}
.pomo-clock {
    font-size: 4.6rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, #ffffff, var(--cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
}
.pomo-mode {
    margin-top: 0.6rem;
    font-size: 0.86rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    font-weight: 600;
}
.pomo-round { margin-top: 0.2rem; color: var(--muted); font-size: 0.8rem; }

/* ---------- Streak flame ---------- */
.streak-hero {
    text-align: center;
    padding: 1.4rem;
    border-radius: 18px;
    background: radial-gradient(circle at 50% 10%, rgba(245, 158, 11, 0.22), transparent 60%),
                linear-gradient(160deg, var(--surface-2), var(--surface));
    border: 1px solid rgba(245, 158, 11, 0.25);
}
.streak-hero .num {
    font-size: 3rem; font-weight: 800; line-height: 1;
    background: linear-gradient(135deg, var(--warning), var(--danger));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.streak-hero .cap { color: var(--muted); margin-top: 0.35rem; font-size: 0.88rem; }

/* ---------- Buttons / inputs ---------- */
.stButton > button {
    border-radius: 11px;
    border: 1px solid var(--border);
    background: linear-gradient(160deg, var(--surface-2), var(--surface));
    color: var(--text);
    font-weight: 600;
    transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    transform: translateY(-1px);
    border-color: rgba(124, 92, 255, 0.6);
    box-shadow: 0 8px 18px rgba(124, 92, 255, 0.22);
    color: #fff;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--primary), #5b7cfa);
    border: none;
}
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] > div {
    background-color: var(--surface-2) !important;
    border-color: var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
.stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
.stTabs [data-baseweb="tab"] {
    border-radius: 10px 10px 0 0;
    padding: 0.45rem 0.95rem;
    background: transparent;
    color: var(--muted);
}
.stTabs [aria-selected="true"] {
    color: var(--text) !important;
    background: rgba(124, 92, 255, 0.12);
}
div[data-testid="stExpander"] {
    border: 1px solid var(--border);
    border-radius: 12px;
    background: rgba(20, 25, 37, 0.6);
    overflow: hidden;
}
hr { border-color: var(--border); }
</style>
"""


def inject_css() -> None:
    """Inject the global stylesheet exactly once per rerun."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, foot: str = "", accent: str = PRIMARY) -> str:
    """Return the HTML for a single metric card."""
    return (
        f'<div class="stat-card" style="--accent:{accent};">'
        f'<div class="label">{label}</div>'
        f'<div class="value">{value}</div>'
        f'<div class="foot">{foot}</div>'
        f"</div>"
    )


def render_stat_grid(cards: list[str], columns: int = 5) -> None:
    st.markdown(
        f'<div class="stat-grid" style="grid-template-columns: repeat({columns}, minmax(0, 1fr));">'
        + "".join(cards)
        + "</div>",
        unsafe_allow_html=True,
    )


def badge(text: str, color: str, subtle: bool = True) -> str:
    """Return an inline badge span."""
    if subtle:
        return (
            f'<span class="badge" style="color:{color};'
            f'background:{color}22;border-color:{color}55;">{text}</span>'
        )
    return f'<span class="badge" style="color:#0b0e14;background:{color};">{text}</span>'


def progress_bar(percent: float) -> str:
    percent = max(0.0, min(100.0, float(percent)))
    return (
        '<div class="progress-track">'
        f'<div class="progress-fill" style="width:{percent:.1f}%;"></div>'
        "</div>"
    )
