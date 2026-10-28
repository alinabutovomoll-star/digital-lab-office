#!/usr/bin/env bun
// Задачи и проекты Digital Lab Office (Supabase). Без зависимостей, запуск через bun.
//
//   bun tools/tasks.ts projects [--all]
//   bun tools/tasks.ts add-project '{"title":"...","client":"...","kind":"лендинг","deadline":"2026-11-05","brief":"..."}'
//   bun tools/tasks.ts update-project 3 '{"status":"готов","links":"https://..."}'
//   bun tools/tasks.ts tasks [--assignee alina] [--area личное] [--status review] [--project 3] [--all]
//   bun tools/tasks.ts add-tasks '[{"title":"...","assignee":"maxim","project_id":3,"due":"2026-11-01T18:00:00+07:00"}]'
//   bun tools/tasks.ts update-task 12 '{"status":"done"}'
//   bun tools/tasks.ts due            — напоминания, которые пора отправить (и отметить отправленными)
//   bun tools/tasks.ts note "текст"   — сохранить заметку / идею
//   bun tools/tasks.ts notes          — последние заметки

const URL_ = process.env.SUPABASE_URL;
const KEY = process.env.SUPABASE_SERVICE_KEY;
if (!URL_ || !KEY) {
  console.error("Нет SUPABASE_URL / SUPABASE_SERVICE_KEY в файле .env");
  process.exit(1);
}

async function sb(path: string, init: RequestInit = {}) {
  const r = await fetch(`${URL_}/rest/v1/${path}`, {
    ...init,
    headers: {
      apikey: KEY!, ...(KEY!.startsWith("eyJ") ? { Authorization: `Bearer ${KEY}` } : {}),
      "Content-Type": "application/json", Prefer: "return=representation",
      ...(init.headers || {}),
    },
  });
  const text = await r.text();
  if (!r.ok) throw new Error(`${r.status}: ${text}`);
  return text ? JSON.parse(text) : null;
}

const now = () => new Date().toISOString();
const enc = encodeURIComponent;
const [cmd, ...rest] = process.argv.slice(2);
const flag = (name: string) => {
  const i = rest.indexOf(`--${name}`);
  return i >= 0 ? rest[i + 1] : undefined;
};
const json = (s?: string) => {
  if (!s) throw new Error("Нужен JSON-аргумент");
  return JSON.parse(s);
};

const TASK_FIELDS = ["project_id", "title", "details", "assignee", "area", "status", "priority", "due", "remind_at"];
const PROJECT_FIELDS = ["title", "client", "kind", "status", "deadline", "budget", "brief", "links"];
const pick = (o: any, keys: string[]) => Object.fromEntries(Object.entries(o).filter(([k]) => keys.includes(k)));

function fmtTask(t: any) {
  const due = t.due ? ` · срок ${new Date(t.due).toLocaleString("ru-RU", { timeZone: "Asia/Bangkok", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}` : "";
  return `#${t.id} [${t.status}] ${t.priority === 1 ? "‼️ " : ""}${t.title} — ${t.assignee}/${t.area}${t.project_id ? ` · проект ${t.project_id}` : ""}${due}`;
}

async function main() {
  switch (cmd) {
    case "projects": {
      const q = rest.includes("--all") ? "" : "&status=neq.готов";
      const rows = await sb(`project_progress?select=*&order=id${q}`);
      for (const p of rows) console.log(`P${p.id} ${p.title} — ${p.status}, ${p.percent}% (${p.tasks_done}/${p.tasks_total})${p.client ? ` · ${p.client}` : ""}${p.deadline ? ` · до ${p.deadline}` : ""}`);
      if (!rows.length) console.log("Проектов нет");
      break;
    }
    case "add-project": {
      const [p] = await sb("projects", { method: "POST", body: JSON.stringify(pick(json(rest[0]), PROJECT_FIELDS)) });
      console.log(`Создан проект P${p.id}: ${p.title}`);
      break;
    }
    case "update-project": {
      const data = { ...pick(json(rest[1]), PROJECT_FIELDS), updated_at: now() };
      await sb(`projects?id=eq.${Number(rest[0])}`, { method: "PATCH", body: JSON.stringify(data) });
      console.log(`Проект P${rest[0]} обновлён`);
      break;
    }
    case "tasks": {
      let q = "tasks?select=*&order=priority,due.nullslast&limit=300";
      const st = flag("status");
      if (st) q += `&status=eq.${enc(st)}`; else if (!rest.includes("--all")) q += "&status=neq.done";
      for (const [f, col] of [["assignee", "assignee"], ["area", "area"], ["project", "project_id"]]) {
        const v = flag(f); if (v) q += `&${col}=eq.${enc(v)}`;
      }
      const rows = await sb(q);
      rows.forEach((t: any) => console.log(fmtTask(t)));
      if (!rows.length) console.log("Задач нет");
      break;
    }
    case "add-tasks": {
      let list = json(rest[0]); if (!Array.isArray(list)) list = [list];
      const rows = await sb("tasks", { method: "POST", body: JSON.stringify(list.map((t: any) => pick(t, TASK_FIELDS))) });
      rows.forEach((t: any) => console.log("Создана " + fmtTask(t)));
      break;
    }
    case "update-task": {
      const patch = json(rest[1]);
      const data: any = { ...pick(patch, TASK_FIELDS), updated_at: now() };
      if (patch.status === "done") data.done_at = now();
      if ("remind_at" in patch) data.reminded = false;
      const [t] = await sb(`tasks?id=eq.${Number(rest[0])}`, { method: "PATCH", body: JSON.stringify(data) });
      console.log(t ? "Обновлена " + fmtTask(t) : "Задача не найдена");
      break;
    }
    case "due": {
      const rows = await sb(`tasks?select=*&reminded=eq.false&status=neq.done&remind_at=lte.${enc(now())}`);
      for (const t of rows) {
        console.log("НАПОМНИТЬ: " + fmtTask(t));
        await sb(`tasks?id=eq.${t.id}`, { method: "PATCH", body: JSON.stringify({ reminded: true }) });
      }
      if (!rows.length) console.log("Напоминаний нет");
      break;
    }
    case "note": {
      await sb("notes", { method: "POST", body: JSON.stringify({ author: "alice", text: rest.join(" ") }) });
      console.log("Заметка сохранена");
      break;
    }
    case "notes": {
      const rows = await sb("notes?select=*&order=id.desc&limit=30");
      rows.forEach((n: any) => console.log(`${n.created_at.slice(0, 10)} ${n.text}`));
      break;
    }
    default:
      console.log("Команды: projects, add-project, update-project, tasks, add-tasks, update-task, due, note, notes");
  }
}

main().catch((e) => { console.error("Ошибка:", e.message); process.exit(1); });
