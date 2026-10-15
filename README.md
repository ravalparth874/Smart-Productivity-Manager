# Smart Productivity Manager

A modern, professional productivity workspace built with **Python**, **Streamlit** and **SQLite3**.
It combines task management, a built-in Pomodoro timer, daily goals, streak tracking and
interactive analytics in a single premium dark-themed dashboard.

All data is stored locally in a SQLite database, so your tasks, focus sessions, goals and
statistics persist after you close and restart the app.

---

## Features

- **Dashboard** - total, completed, pending and overdue tasks, daily progress ring and a weekly productivity chart.
- **Task management** - add, edit, delete, search and filter tasks by category, priority and status.
- **Priorities and metadata** - Low / Medium / High priority, categories, deadlines and status tracking.
- **Pomodoro timer** - customisable focus, short-break and long-break sessions with live countdown.
- **Daily goals and study tracking** - set daily targets, log study sessions and monitor streaks.
- **Analytics** - interactive Plotly charts for weekly activity, category mix, priority split and completion rate.
- **Notifications** - automatic alerts for tasks due today, upcoming deadlines and overdue tasks.
- **Persistent storage** - everything is saved in `data/productivity.db` via SQLite3.

---

## Tech Stack

| Layer      | Technology            |
|------------|-----------------------|
| UI         | Streamlit             |
| Charts     | Plotly                |
| Data       | SQLite3 (standard lib)|
| Language   | Python 3.9+           |

---

## Project Structure

```
.
├── app.py                  # Application entry point and navigation
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .streamlit/
│   └── config.toml         # Dark theme + server configuration
├── data/
│   └── productivity.db     # SQLite database (created automatically)
└── src/
    ├── __init__.py
    ├── database.py         # All SQLite access (tasks, sessions, goals, stats)
    ├── charts.py           # Plotly chart builders
    ├── styles.py           # Dark theme CSS and reusable card helpers
    ├── utils.py            # Small helpers (dates, notifications, flash messages)
    └── pages/
        ├── dashboard.py    # Overview page
        ├── tasks.py        # Task management page
        ├── pomodoro.py     # Pomodoro timer page
        ├── goals.py        # Daily goals and streaks page
        └── analytics.py    # Charts and statistics page
```

---

## Setup Instructions

### 1. Clone or open the project

```bash
cd /workspace
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

On Windows use `.venv\Scripts\activate` instead.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` in your browser. On first launch the
database file and its tables are created automatically.

---

## Usage Guide

### Dashboard
Shows headline metrics (total, completed, pending, overdue) and your daily progress.
The **Notifications** panel highlights overdue tasks and deadlines due within three days.
The **Deadline Radar** lists the next five deadlines, and **Recent Tasks** shows what is pending.

### Tasks
Open the **Add a new task** panel to create a task with a title, description, category,
priority, status and an optional deadline. Use the filter row to search and narrow the list,
then use the per-task **Done / Undo**, **Edit** and **Del** buttons to manage each item.
Deleting a task always asks for confirmation first.

### Pomodoro
Pick a session type (Focus, Short Break or Long Break), optionally link it to a task, then press
**Start session**. The clock updates every second. When a focus session finishes it is logged
automatically, a sound plays and the app suggests a break. Adjust the durations under
**Timer settings**; the values are saved to the database.

### Goals & Streaks
Set a daily target for completed tasks and focus minutes, and add a focus note.
The streak cards show your current and longest streak, and a 14-day strip shows which days
were active. Log study sessions with a subject, duration, date and optional notes.

### Analytics
Interactive charts for weekly activity, task categories, priorities, focus minutes and overall
completion, plus a summary table of all-time statistics.

---

## How Data Persistence Works

- All reads and writes go through `src/database.py`, which opens a short-lived SQLite
  connection per operation and commits automatically.
- The database lives at `data/productivity.db`. Deleting this file resets the app.
- `src/database.py::init_db()` is idempotent: it only creates tables that do not exist yet,
  so restarting the app never loses data.

---

## Troubleshooting

- **Port already in use** - run `streamlit run app.py --server.port 8502`.
- **Reset all data** - stop the app and remove `data/productivity.db`, then start again.
- **Blank charts** - add a few tasks and log a focus session; charts fill in as data arrives.

---

## License

Provided as-is for personal and educational use.
