#!/usr/bin/env bun
// Сообщение в рабочий чат «Digital Lab Office» от имени сотрудника (его собственным ботом).
//
//   bun tools/say.ts maxim "Взял задачу #5, к 18:00 пришлю превью"
//   bun tools/say.ts dmitry "План проекта готов" --file /полный/путь/plan.md
//   bun tools/say.ts maria --typing            — показать «печатает…»
//
// Токены ботов — в .env: TG_TOKEN_DMITRY, TG_TOKEN_MARIA, TG_TOKEN_MAXIM, TG_TOKEN_ILYA,
// TG_TOKEN_ALEXANDER, TG_TOKEN_DARIA. Id группы — OFFICE_CHAT_ID в .env или файл .office_chat_id.
import { existsSync, readFileSync } from "fs";
import { basename, join } from "path";

const ROOT = join(import.meta.dir, "..");
const NAMES: Record<string, string> = {
  dmitry: "Дмитрий", maria: "Мария", maxim: "Максим",
  ilya: "Илья", alexander: "Александр", daria: "Дарья", alice: "Алиса",
};

const args = process.argv.slice(2);
const who = (args[0] || "").toLowerCase();
if (!NAMES[who]) {
  console.error(`Кто говорит? Один из: ${Object.keys(NAMES).join(", ")}`);
  process.exit(1);
}
const token = process.env[`TG_TOKEN_${who.toUpperCase()}`];
if (!token) {
  console.error(`Нет токена TG_TOKEN_${who.toUpperCase()} в .env — бот ${NAMES[who]} ещё не подключён.`);
  process.exit(1);
}
const chatFile = join(ROOT, ".office_chat_id");
const chatId = process.env.OFFICE_CHAT_ID || (existsSync(chatFile) ? readFileSync(chatFile, "utf8").trim() : "");
if (!chatId) {
  console.error("Не знаю id рабочего чата: нет OFFICE_CHAT_ID в .env и файла .office_chat_id");
  process.exit(1);
}

const flagVal = (f: string) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : undefined; };
const file = flagVal("--file");
const replyTo = flagVal("--reply");
const typing = args.includes("--typing");
const text = args.slice(1).filter((a, i, all) =>
  !a.startsWith("--") && !["--file", "--reply"].includes(all[i - 1])).join(" ").trim();

const API_BASE = process.env.TG_API_BASE || "https://api.telegram.org";
const api = (method: string) => `${API_BASE}/bot${token}/${method}`;

async function call(method: string, body: Record<string, unknown> | FormData) {
  const r = await fetch(api(method), body instanceof FormData
    ? { method: "POST", body }
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const j: any = await r.json();
  if (!j.ok) throw new Error(`${method}: ${j.description}`);
  return j.result;
}

try {
  if (typing) await call("sendChatAction", { chat_id: chatId, action: "typing" });
  if (text) {
    for (let i = 0; i < text.length; i += 4000) {
      const m = await call("sendMessage", {
        chat_id: chatId, text: text.slice(i, i + 4000),
        ...(replyTo && i === 0 ? { reply_parameters: { message_id: Number(replyTo) } } : {}),
      });
      if (i === 0) console.log(`Отправлено (${NAMES[who]}), message_id=${m.message_id}`);
    }
  }
  if (file) {
    const fd = new FormData();
    fd.append("chat_id", chatId);
    fd.append("document", new Blob([readFileSync(file)]), basename(file));
    await call("sendDocument", fd);
    console.log(`Файл отправлен (${NAMES[who]}): ${basename(file)}`);
  }
} catch (e: any) {
  console.error("Ошибка Telegram:", e.message);
  process.exit(1);
}
