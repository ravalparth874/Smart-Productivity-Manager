"""Task management: add, edit, delete, search and filter."""

from __future__ import annotations

import sqlite3
from datetime import date

import streamlit as st

from src import database as db, styles
from src.utils import deadline_label, flash, parse_date


def _task_card(task: dict) -> str:
    completed = task.get("status") == "Completed"
    priority = task.get("priority", "Medium")
    accent = styles.PRIORITY_COLORS.get(priority, styles.PRIMARY)
    status_color = styles.STATUS_COLORS.get(task.get("status", "Pending"), styles.MUTED)

    badges = [
        styles.badge(task.get("category") or "General", styles.PRIMARY),
        styles.badge(f"{priority}", accent),
        styles.badge(task.get("status", "Pending"), status_color),
    ]
    if task.get("deadline"):
        dl_color = styles.DANGER if db.is_overdue(task) else styles.MUTED
        badges.append(styles.badge(deadline_label(task["deadline"], completed), dl_color))

    description = task.get("description") or ""
    desc_html = f'<div class="task-desc">{description}</div>' if description else ""

    return (
        f'<div class="task-row {"done" if completed else ""}" style="--accent:{accent};">'
        f'<div style="flex:1;">'
        f'<div class="task-title">{task["title"]}</div>'
        f"{desc_html}"
        f'<div class="task-meta">{"".join(badges)}</div>'
        f"</div></div>"
    )


def _render_add_form() -> None:
    categories = db.get_categories()
    with st.expander("Add a new task", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            title = st.text_input("Task title", placeholder="What needs to get done?")
            description = st.text_area("Description", placeholder="Optional details", height=80)
            col1, col2, col3 = st.columns(3)
            with col1:
                category = st.selectbox("Category", categories, index=0)
                new_category = st.text_input("Or new category", placeholder="e.g. Reading")
            with col2:
                priority = st.selectbox("Priority", db.PRIORITIES, index=1)
                status = st.selectbox("Status", db.STATUSES, index=0)
            with col3:
                has_deadline = st.checkbox("Set deadline", value=False)
                deadline = st.date_input("Deadline", value=date.today(), disabled=not has_deadline)

            submitted = st.form_submit_button("Add task", type="primary", width="stretch")

        if submitted:
            final_category = (new_category or "").strip() or category
            try:
                db.add_task(
                    title=title,
                    description=description,
                    category=final_category,
                    priority=priority,
                    deadline=deadline if has_deadline else None,
                    status=status,
                )
                flash(f"Task '{title.strip()}' added.")
                st.rerun()
            except (ValueError, sqlite3.Error) as exc:
                st.error(f"Could not add task: {exc}")


def _render_edit_form(task_id: int) -> None:
    task = db.get_task(task_id)
    if task is None:
        st.session_state.pop("edit_task_id", None)
        return

    categories = db.get_categories()
    category_index = categories.index(task["category"]) if task["category"] in categories else 0
    priority_index = db.PRIORITIES.index(task["priority"]) if task["priority"] in db.PRIORITIES else 1
    status_index = db.STATUSES.index(task["status"]) if task["status"] in db.STATUSES else 0
    deadline_value = parse_date(task["deadline"]) or date.today()

    with st.expander(f"Editing: {task['title']}", expanded=True):
        with st.form(f"edit_task_form_{task_id}"):
            title = st.text_input("Task title", value=task["title"])
            description = st.text_area("Description", value=task["description"] or "", height=80)
            col1, col2, col3 = st.columns(3)
            with col1:
                category = st.selectbox("Category", categories, index=category_index)
            with col2:
                priority = st.selectbox("Priority", db.PRIORITIES, index=priority_index)
                status = st.selectbox("Status", db.STATUSES, index=status_index)
            with col3:
                has_deadline = st.checkbox("Has deadline", value=bool(task["deadline"]))
                deadline = st.date_input("Deadline", value=deadline_value, disabled=not has_deadline)

            save_col, cancel_col = st.columns(2)
            saved = save_col.form_submit_button("Save changes", type="primary", width="stretch")
            cancelled = cancel_col.form_submit_button("Cancel", width="stretch")

        if saved:
            try:
                db.update_task(
                    task_id,
                    title=title.strip(),
                    description=description,
                    category=category,
                    priority=priority,
                    status=status,
                    deadline=deadline if has_deadline else "",
                )
                st.session_state.pop("edit_task_id", None)
                flash("Task updated.")
                st.rerun()
            except (ValueError, sqlite3.Error) as exc:
                st.error(f"Could not update task: {exc}")
        if cancelled:
            st.session_state.pop("edit_task_id", None)
            st.rerun()


def _render_delete_confirm(task_id: int) -> None:
    task = db.get_task(task_id)
    if task is None:
        st.session_state.pop("delete_task_id", None)
        return
    with st.container(border=True):
        st.warning(f"Delete task '{task['title']}'? This cannot be undone.")
        col1, col2 = st.columns(2)
        if col1.button("Yes, delete", key=f"confirm_delete_{task_id}", type="primary", width="stretch"):
            db.delete_task(task_id)
            st.session_state.pop("delete_task_id", None)
            flash("Task deleted.")
            st.rerun()
        if col2.button("Keep task", key=f"cancel_delete_{task_id}", width="stretch"):
            st.session_state.pop("delete_task_id", None)
            st.rerun()


def _render_filters() -> dict:
    categories = ["All"] + db.get_categories()
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    search = col1.text_input("Search", placeholder="Search title, notes, category", key="task_search")
    category = col2.selectbox("Category", categories, key="task_filter_category")
    priority = col3.selectbox("Priority", ["All"] + db.PRIORITIES, key="task_filter_priority")
    status = col4.selectbox("Status", ["All"] + db.STATUSES, key="task_filter_status")
    sort_by = col5.selectbox(
        "Sort by",
        ["created_at", "deadline", "priority", "title", "status"],
        format_func=lambda value: {
            "created_at": "Newest",
            "deadline": "Deadline",
            "priority": "Priority",
            "title": "Title",
            "status": "Status",
        }.get(value, value),
        key="task_sort",
    )
    return {
        "search": search,
        "category": category,
        "priority": priority,
        "status": status,
        "sort_by": sort_by,
    }


def _render_task_list(filters: dict) -> None:
    tasks = db.list_tasks(**filters)
    if not tasks:
        st.info("No tasks match your filters. Try adjusting the search or add a new task.")
        return

    st.caption(f"{len(tasks)} task(s) shown")
    for task in tasks:
        info_col, action_col = st.columns([5, 1.7], gap="small")
        with info_col:
            st.markdown(_task_card(task), unsafe_allow_html=True)
        with action_col:
            b1, b2, b3 = st.columns(3)
            is_completed = task["status"] == "Completed"
            if b1.button(
                "Undo" if is_completed else "Done",
                key=f"toggle_{task['id']}",
                width="stretch",
                help="Toggle completion",
            ):
                db.toggle_task_complete(task["id"])
                st.rerun()
            if b2.button("Edit", key=f"edit_{task['id']}", width="stretch"):
                st.session_state["edit_task_id"] = task["id"]
                st.session_state.pop("delete_task_id", None)
                st.rerun()
            if b3.button("Del", key=f"del_{task['id']}", width="stretch"):
                st.session_state["delete_task_id"] = task["id"]
                st.session_state.pop("edit_task_id", None)
                st.rerun()


def render() -> None:
    styles.page_header("Tasks", "Organise, prioritise and track everything on your plate.")

    edit_id = st.session_state.get("edit_task_id")
    if edit_id:
        _render_edit_form(edit_id)

    delete_id = st.session_state.get("delete_task_id")
    if delete_id:
        _render_delete_confirm(delete_id)

    _render_add_form()

    st.write("")
    filters = _render_filters()
    st.write("")
    _render_task_list(filters)
