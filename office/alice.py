"""Алиса — мозг ассистента: Claude + инструменты для работы с задачами."""
import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from . import db
from .config import ANTHROPIC_API_KEY, MODEL, TIMEZONE
from .team import AGENCY, TEAM, TEAM_LIST

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
history: dict[int, deque] = defaultdict(lambda: deque(maxlen=30))

ASSIGNEES = ["alina"] + list(TEAM)

TOOLS = [
    {"name": "create_project", "description": "Создать проект (заказ клиента или внутренний проект агентства).",
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string"}, "client": {"type": "string"},
         "kind": {"type": "string", "description": "лендинг, сайт, бот, mini app, автоматизация, управленческая система, дизайн, маркетинг, внутреннее"},
         "deadline": {"type": "string", "description": "YYYY-MM-DD"},
         "budget": {"type": "number"}, "brief": {"type": "string", "description": "ТЗ целиком или кратко"},
         "links": {"type": "string"}}, "required": ["title"]}},
    {"name": "update_project", "description": "Изменить проект: статус (новый, в работе, на согласовании, готов, пауза), срок, ссылки и т.д.",
     "input_schema": {"type": "object", "properties": {
         "project_id": {"type": "integer"}, "title": {"type": "string"}, "client": {"type": "string"},
         "kind": {"type": "string"}, "status": {"type": "string"}, "deadline": {"type": "string"},
         "budget": {"type": "number"}, "brief": {"type": "string"}, "links": {"type": "string"}},
         "required": ["project_id"]}},
    {"name": "list_projects", "description": "Проекты с процентом выполнения.",
     "input_schema": {"type": "object", "properties": {"include_done": {"type": "boolean"}}}},
    {"name": "create_tasks", "description": "Создать одну или несколько задач.",
     "input_schema": {"type": "object", "properties": {"tasks": {"type": "array", "items": {
         "type": "object", "properties": {
             "title": {"type": "string"}, "details": {"type": "string"},
             "project_id": {"type": "integer"},
             "assignee": {"type": "string", "enum": ASSIGNEES},
             "area": {"type": "string", "enum": ["работа", "личное"]},
             "priority": {"type": "integer", "enum": [1, 2, 3]},
             "due": {"type": "string", "description": "ISO дата-время с часовым поясом"},
             "remind_at": {"type": "string", "description": "ISO дата-время напоминания с часовым поясом"}},
         "required": ["title"]}}}, "required": ["tasks"]}},
    {"name": "update_task", "description": "Изменить задачу: статус (todo, doing, review, done), исполнителя, срок, напоминание.",
     "input_schema": {"type": "object", "properties": {
         "task_id": {"type": "integer"}, "title": {"type": "string"}, "details": {"type": "string"},
         "project_id": {"type": "integer"}, "assignee": {"type": "string", "enum": ASSIGNEES},
         "area": {"type": "string", "enum": ["работа", "личное"]},
         "status": {"type": "string", "enum": ["todo", "doing", "review", "done"]},
         "priority": {"type": "integer", "enum": [1, 2, 3]},
         "due": {"type": "string"}, "remind_at": {"type": "string"}}, "required": ["task_id"]}},
    {"name": "list_tasks", "description": "Список задач с фильтрами.",
     "input_schema": {"type": "object", "properties": {
         "status": {"type": "string", "enum": ["todo", "doing", "review", "done"]},
         "assignee": {"type": "string", "enum": ASSIGNEES},
         "area": {"type": "string", "enum": ["работа", "личное"]},
         "project_id": {"type": "integer"}, "include_done": {"type": "boolean"}}}},
    {"name": "save_note", "description": "Запомнить идею, договорённость или факт об агентстве/клиенте.",
     "input_schema": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "recent_notes", "description": "Последние сохранённые заметки и идеи.",
     "input_schema": {"type": "object", "properties": {}}},
]


def _run_tool(name: str, args: dict):
    match name:
        case "create_project": return db.create_project(**args)
        case "update_project": return db.update_project(args.pop("project_id"), **args)
        case "list_projects": return db.list_projects(**args)
        case "create_tasks": return [db.create_task(**t) for t in args["tasks"]]
        case "update_task": return db.update_task(args.pop("task_id"), **args)
        case "list_tasks": return db.list_tasks(**args)
        case "save_note": return db.add_note("alice", args["text"])
        case "recent_notes": return db.recent_notes()
    return {"error": f"unknown tool {name}"}


def system_prompt() -> str:
    a = TEAM["alice"]
    now = datetime.now(ZoneInfo(TIMEZONE)).strftime("%A, %d.%m.%Y %H:%M")
    return f"""Ты — {a['name']}, {a['role']} в агентстве Digital Lab. {a['character']}
Ты сотрудник, а не чат-бот: говоришь от первого лица, по-русски, на «ты» с Алиной (она CEO и твоя руководительница).

{AGENCY}

Команда:
{TEAM_LIST}
Сейчас к Telegram подключена только ты, остальные сотрудники подключаются по этапам. Задачи на них
всё равно заводи — они возьмут их, когда выйдут на работу. Пока их нет, предлагай Алине, что можешь
сделать сама (план, текст, разбор ТЗ, список вопросов клиенту).

Как работаешь:
- Всё, что звучит как дело, сразу превращай в задачи и проекты через инструменты. Не спрашивай разрешения на очевидное.
- ТЗ клиента → проект + разбивка на задачи по ролям (Дмитрий — план и вопросы, Мария — дизайн, Максим — сайт,
  Илья — боты/автоматизация, Александр — проверка, Дарья — продвижение). Срок ставь реалистичный.
- Цели по росту («хочу 5 клиентов в месяц») → проект «Привлечение клиентов» и задачи Дарье и Алине.
- Личные дела Алины — area «личное», assignee «alina».
- Если Алина просит напомнить — ставь remind_at. Время всегда указывай с часовым поясом {TIMEZONE}.
- Отвечай коротко: что сделала + что важно. Номера задач пиши как #12. Не используй markdown-таблицы.
Сейчас: {now} ({TIMEZONE})."""


async def ask(chat_id: int, text: str) -> str:
    msgs = history[chat_id]
    msgs.append({"role": "user", "content": text})
    convo = list(msgs)
    # история должна начинаться с сообщения пользователя
    while convo and convo[0]["role"] != "user":
        convo.pop(0)

    for _ in range(10):
        resp = await client.messages.create(
            model=MODEL, max_tokens=2000, system=system_prompt(), tools=TOOLS, messages=convo)
        convo.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            break
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                try:
                    out = await asyncio.to_thread(_run_tool, block.name, dict(block.input))
                    content = json.dumps(out, ensure_ascii=False, default=str)[:15000]
                    results.append({"type": "tool_result", "tool_use_id": block.id, "content": content})
                except Exception as e:  # noqa: BLE001
                    results.append({"type": "tool_result", "tool_use_id": block.id,
                                    "content": f"Ошибка: {e}", "is_error": True})
        convo.append({"role": "user", "content": results})

    reply = "".join(b.text for b in convo[-1]["content"] if getattr(b, "type", "") == "text").strip()
    # в долгую память кладём только текст, без служебных шагов
    msgs.append({"role": "assistant", "content": reply or "Готово."})
    return reply or "Готово ✅"
