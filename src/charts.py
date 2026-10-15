"""Plotly chart builders with a consistent premium dark look."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Any

import plotly.graph_objects as go

TEXT = "#e6e9ef"
MUTED = "#93a0b4"
PRIMARY = "#7c5cff"
CYAN = "#22d3ee"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#ef4444"
GRID = "rgba(255,255,255,0.06)"

PRIORITY_COLORS = {"High": DANGER, "Medium": WARNING, "Low": CYAN}


def _base_layout(**overrides: Any) -> dict[str, Any]:
    layout: dict[str, Any] = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter, Segoe UI, sans-serif", size=13),
        margin=dict(l=10, r=10, t=34, b=10),
        height=320,
        showlegend=False,
        hoverlabel=dict(bgcolor="#1b2233", font=dict(color=TEXT)),
    )
    layout.update(overrides)
    return layout


def _axis(title: str = "") -> dict[str, Any]:
    return dict(
        title=title,
        gridcolor=GRID,
        zeroline=False,
        color=MUTED,
        tickfont=dict(color=MUTED),
    )


def weekly_completion_chart(data: list[dict[str, Any]]) -> go.Figure:
    """Bar chart of tasks completed per day."""
    labels = [row["date"].strftime("%a\n%b %d") for row in data]
    values = [row["count"] for row in data]
    colors = [SUCCESS if value > 0 else "rgba(255,255,255,0.08)" for value in values]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(width=0)),
            text=values,
            textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate="%{x}<br>Completed: %{y}<extra></extra>",
            width=0.55,
        )
    )
    fig.update_layout(**_base_layout(
        xaxis=_axis(),
        yaxis=dict(**_axis(), dtick=1, rangemode="tozero"),
        bargap=0.35,
    ))
    return fig


def focus_minutes_chart(data: list[dict[str, Any]]) -> go.Figure:
    """Area chart of focus minutes per day."""
    labels = [row["date"].strftime("%a") for row in data]
    values = [row["minutes"] for row in data]

    fig = go.Figure(
        go.Scatter(
            x=labels,
            y=values,
            mode="lines+markers",
            line=dict(color=PRIMARY, width=3, shape="spline"),
            marker=dict(size=8, color=CYAN, line=dict(color=PRIMARY, width=2)),
            fill="tozeroy",
            fillcolor="rgba(124, 92, 255, 0.18)",
            hovertemplate="%{x}<br>Focus: %{y} min<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(
        xaxis=_axis(),
        yaxis=dict(**_axis(), rangemode="tozero"),
    ))
    return fig


def weekly_activity_combo(completed: list[dict[str, Any]], focus: list[dict[str, Any]]) -> go.Figure:
    """Combined view: completed tasks (bars) + focus minutes (line)."""
    labels = [row["date"].strftime("%a") for row in completed]
    tasks = [row["count"] for row in completed]
    minutes = [row["minutes"] for row in focus]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=tasks,
            name="Tasks completed",
            marker=dict(color="rgba(124, 92, 255, 0.75)"),
            hovertemplate="%{x}<br>Tasks: %{y}<extra></extra>",
            width=0.5,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=labels,
            y=minutes,
            name="Focus minutes",
            mode="lines+markers",
            yaxis="y2",
            line=dict(color=CYAN, width=3, shape="spline"),
            marker=dict(size=7, color=CYAN),
            hovertemplate="%{x}<br>Focus: %{y} min<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(color=MUTED)),
        xaxis=_axis(),
        yaxis=dict(**_axis("Tasks"), dtick=1, rangemode="tozero"),
        yaxis2=dict(
            overlaying="y",
            side="right",
            showgrid=False,
            color=MUTED,
            tickfont=dict(color=MUTED),
            rangemode="tozero",
            title="Focus (min)",
        ),
        margin=dict(l=10, r=10, t=50, b=10),
    ))
    return fig


def category_donut(tasks: list[dict[str, Any]]) -> go.Figure:
    counts = Counter(task.get("category") or "General" for task in tasks)
    labels = list(counts.keys())
    values = list(counts.values())
    palette = [PRIMARY, CYAN, SUCCESS, WARNING, DANGER, "#a78bfa", "#f472b6", "#34d399"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.58,
            marker=dict(colors=palette, line=dict(color="#0b0e14", width=2)),
            textinfo="percent",
            textfont=dict(color=TEXT),
            hovertemplate="%{label}<br>%{value} tasks (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(height=320, margin=dict(l=10, r=10, t=20, b=10)))
    return fig


def priority_bar(tasks: list[dict[str, Any]]) -> go.Figure:
    order = ["High", "Medium", "Low"]
    counts = Counter(task.get("priority") for task in tasks)
    values = [counts.get(level, 0) for level in order]
    colors = [PRIORITY_COLORS[level] for level in order]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=order,
            orientation="h",
            marker=dict(color=colors, line=dict(width=0)),
            text=values,
            textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate="%{y}: %{x} tasks<extra></extra>",
            width=0.55,
        )
    )
    fig.update_layout(**_base_layout(
        height=320,
        xaxis=dict(**_axis(), dtick=1, rangemode="tozero"),
        yaxis=dict(_axis(), autorange="reversed"),
        margin=dict(l=10, r=30, t=20, b=10),
    ))
    return fig


def status_gauge(completed: int, total: int) -> go.Figure:
    percent = 0 if total == 0 else round(completed / total * 100)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percent,
            number={"suffix": "%", "font": {"color": TEXT, "size": 40}},
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=MUTED, tickfont=dict(color=MUTED)),
                bar=dict(color=SUCCESS),
                bgcolor="rgba(255,255,255,0.05)",
                borderwidth=0,
                steps=[
                    dict(range=[0, 34], color="rgba(239, 68, 68, 0.20)"),
                    dict(range=[34, 67], color="rgba(245, 158, 11, 0.20)"),
                    dict(range=[67, 100], color="rgba(34, 197, 94, 0.20)"),
                ],
            ),
        )
    )
    fig.update_layout(**_base_layout(height=280, margin=dict(l=20, r=20, t=20, b=20)))
    return fig


def goal_progress(values: list[int], targets: list[int]) -> go.Figure:
    labels = ["Tasks today", "Focus minutes"]
    percents = [
        0 if targets[0] == 0 else min(100, round(values[0] / targets[0] * 100)),
        0 if targets[1] == 0 else min(100, round(values[1] / targets[1] * 100)),
    ]
    fig = go.Figure(
        go.Bar(
            x=percents,
            y=labels,
            orientation="h",
            marker=dict(color=[PRIMARY, CYAN], line=dict(width=0)),
            text=[f"{p}%" for p in percents],
            textposition="outside",
            textfont=dict(color=TEXT),
            hovertemplate="%{y}: %{x}%<extra></extra>",
            width=0.5,
        )
    )
    fig.update_layout(**_base_layout(
        height=240,
        xaxis=dict(**_axis(), range=[0, 115], ticksuffix="%"),
        yaxis=dict(_axis(), autorange="reversed"),
        margin=dict(l=10, r=40, t=20, b=10),
    ))
    return fig
