"""Запуск Алисы в Telegram:  python -m office.bot"""
import asyncio
import io
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                           WebAppInfo)

from . import alice, db
from .config import (ALICE_BOT_TOKEN, DASHBOARD_URL, EVENING_HOUR, MORNING_HOUR,
                     OFFICE_CHAT_ID, OWNER_ID, TIMEZONE)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
bot = Bot(ALICE_BOT_TOKEN)
dp = Dispatcher()
TZ = ZoneInfo(TIMEZONE)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # необязательно: для голосовых сообщений


def owner_only(m: Message) -> bool:
    return bool(m.from_user and m.from_user.id == OWNER_ID)


def addressed_to_alice(m: Message, me_username: str) -> bool:
    """В группе Алиса отвечает, если к ней обратились; в личке — всегда."""
    if m.chat.type == "private":
        return True
    text = (m.text or m.caption or "").lower()
    if "алис" in text or f"@{me_username.lower()}" in text:
        return True
    return bool(m.reply_to_message and m.reply_to_message.from_user
                and m.reply_to_message.from_user.username == me_username)


def dashboard_kb():
    if not DASHBOARD_URL:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📊 Открыть дашборд", web_app=WebAppInfo(url=DASHBOARD_URL))]])


async def send_long(chat_id: int, text: str, **kw):
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id, text[i:i + 4000], **kw)


async def transcribe(m: Message) -> str | None:
    if not OPENAI_API_KEY:
        return None
    from openai import AsyncOpenAI
    f = await bot.get_file((m.voice or m.audio or m.video_note).file_id)
    buf = io.BytesIO()
    await bot.download_file(f.file_path, buf)
    buf.name = "voice.ogg"
    r = await AsyncOpenAI(api_key=OPENAI_API_KEY).audio.transcriptions.create(
        model="whisper-1", file=buf, language="ru")
    return r.text


@dp.message(Command("start"))
async def start(m: Message):
    if not owner_only(m):
        return await m.answer("Это рабочий бот Digital Lab. Чтобы обсудить проект, напишите @alinaaa_ss.")
    await m.answer("Привет, Алина! Я Алиса, твой ассистент 👩‍💼\n"
                   "Пиши или наговаривай голосом: задачи, идеи, ТЗ клиентов, личные дела — я всё разложу.\n"
                   "Команды: /today — сводка, /dashboard — дашборд, /id — id чата.",
                   reply_markup=dashboard_kb())


@dp.message(Command("id"))
async def chat_id(m: Message):
    if owner_only(m):
        await m.answer(f"id этого чата: <code>{m.chat.id}</code>", parse_mode="HTML")


@dp.message(Command("dashboard"))
async def dashboard(m: Message):
    if owner_only(m):
        await m.answer("Дашборд:" if DASHBOARD_URL else "Ссылка на дашборд ещё не настроена.",
                       reply_markup=dashboard_kb())


@dp.message(Command("today"))
async def today(m: Message):
    if owner_only(m):
        await bot.send_chat_action(m.chat.id, ChatAction.TYPING)
        await send_long(m.chat.id, await alice.ask(m.chat.id, SUMMARY_PROMPT["morning"]))


@dp.message(F.text | F.voice | F.audio | F.video_note | F.caption)
async def on_message(m: Message):
    if not owner_only(m):
        return
    me = await bot.me()
    text = m.text or m.caption
    if m.voice or m.audio or m.video_note:
        text = await transcribe(m)
        if text is None:
            return await m.answer("Голосовые я пока не слышу — нужен ключ OpenAI в настройках. Напиши текстом, пожалуйста 🙏")
    if not text or not (addressed_to_alice(m, me.username) or m.voice):
        return
    await bot.send_chat_action(m.chat.id, ChatAction.TYPING)
    try:
        reply = await alice.ask(m.chat.id, text)
    except Exception as e:  # noqa: BLE001
        logging.exception("alice failed")
        reply = f"Ой, что-то сломалось: {e}"
    await send_long(m.chat.id, reply)


SUMMARY_PROMPT = {
    "morning": "[Автоматически] Доброе утро-сводка: посмотри проекты и задачи. Напиши Алине коротко: "
               "что сегодня главное (её задачи и личные дела), что горит по срокам, что ждёт её согласования, "
               "прогресс по проектам в процентах. Максимум 12 строк.",
    "evening": "[Автоматически] Вечерняя сводка: что закрыто сегодня, что сдвинулось, что перенести на завтра. "
               "Коротко, максимум 8 строк. Если день был пустой — просто пожелай хорошего вечера.",
}


async def scheduler():
    """Раз в минуту: напоминания; в заданные часы — утренняя и вечерняя сводка."""
    sent = set()
    target = OFFICE_CHAT_ID or OWNER_ID
    while True:
        try:
            for t in await asyncio.to_thread(db.due_reminders):
                await bot.send_message(OWNER_ID, f"⏰ Напоминаю: {t['title']} (#{t['id']})")
                await asyncio.to_thread(db.mark_reminded, t["id"])
            now = datetime.now(TZ)
            for kind, hour in (("morning", MORNING_HOUR), ("evening", EVENING_HOUR)):
                key = (kind, now.date())
                if now.hour == hour and key not in sent:
                    sent.add(key)
                    text = await alice.ask(OWNER_ID, SUMMARY_PROMPT[kind])
                    await send_long(target, text, reply_markup=dashboard_kb() if kind == "morning" else None)
        except Exception:  # noqa: BLE001
            logging.exception("scheduler error")
        await asyncio.sleep(60)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
