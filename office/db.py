"""Работа с базой задач в Supabase."""
from datetime import datetime, timezone
from supabase import create_client

from .config import SUPABASE_URL, SUPABASE_SERVICE_KEY

sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

PROJECT_FIELDS = {"title", "client", "kind", "status", "deadline", "budget", "brief", "links"}
TASK_FIELDS = {"project_id", "title", "details", "assignee", "area", "status",
               "priority", "due", "remind_at"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _clean(data: dict, allowed: set) -> dict:
    return {k: v for k, v in data.items() if k in allowed and v is not None}


def create_project(**kw):
    return sb.table("projects").insert(_clean(kw, PROJECT_FIELDS)).execute().data[0]


def update_project(project_id: int, **kw):
    data = _clean(kw, PROJECT_FIELDS) | {"updated_at": _now()}
    return sb.table("projects").update(data).eq("id", project_id).execute().data


def list_projects(include_done: bool = False):
    q = sb.table("project_progress").select("*").order("id")
    if not include_done:
        q = q.neq("status", "готов")
    return q.execute().data


def create_task(**kw):
    return sb.table("tasks").insert(_clean(kw, TASK_FIELDS)).execute().data[0]


def update_task(task_id: int, **kw):
    data = _clean(kw, TASK_FIELDS) | {"updated_at": _now()}
    if kw.get("status") == "done":
        data["done_at"] = _now()
    if "remind_at" in data:
        data["reminded"] = False
    return sb.table("tasks").update(data).eq("id", task_id).execute().data


def list_tasks(status=None, assignee=None, area=None, project_id=None, include_done=False):
    q = sb.table("tasks").select("*").order("priority").order("due", nullsfirst=False)
    if status:
        q = q.eq("status", status)
    elif not include_done:
        q = q.neq("status", "done")
    if assignee:
        q = q.eq("assignee", assignee)
    if area:
        q = q.eq("area", area)
    if project_id:
        q = q.eq("project_id", project_id)
    return q.limit(200).execute().data


def due_reminders():
    return (sb.table("tasks").select("*").eq("reminded", False)
            .lte("remind_at", _now()).neq("status", "done").execute().data)


def mark_reminded(task_id: int):
    sb.table("tasks").update({"reminded": True}).eq("id", task_id).execute()


def add_note(author: str, text: str):
    return sb.table("notes").insert({"author": author, "text": text}).execute().data[0]


def recent_notes(limit: int = 20):
    return sb.table("notes").select("*").order("id", desc=True).limit(limit).execute().data
