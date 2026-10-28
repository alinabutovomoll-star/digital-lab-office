import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass


def _need(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise SystemExit(f"Не задана переменная {name} в файле .env")
    return v


ANTHROPIC_API_KEY = _need("ANTHROPIC_API_KEY")
SUPABASE_URL = _need("SUPABASE_URL")
SUPABASE_SERVICE_KEY = _need("SUPABASE_SERVICE_KEY")
ALICE_BOT_TOKEN = _need("ALICE_BOT_TOKEN")
OWNER_ID = int(_need("OWNER_TELEGRAM_ID"))          # Telegram ID Алины — только ей бот подчиняется
OFFICE_CHAT_ID = int(os.getenv("OFFICE_CHAT_ID", "0"))  # id группы «Digital Lab Office» (необязательно)
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Bangkok")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MORNING_HOUR = int(os.getenv("MORNING_HOUR", "9"))
EVENING_HOUR = int(os.getenv("EVENING_HOUR", "20"))
