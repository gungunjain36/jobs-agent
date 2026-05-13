import asyncio
import os
from datetime import datetime

from telegram import Bot


def _get_env(key: str) -> str:
    """Fetch a required environment variable, raise if missing."""
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing environment variable: {key}")
    return val


def send_telegram(message: str):
    """Send a message via the Telegram Bot API (blocking wrapper)."""
    try:
        token = _get_env("TELEGRAM_BOT_TOKEN")
        chat_id = _get_env("TELEGRAM_CHAT_ID")

        async def _send():
            bot = Bot(token=token)
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

        asyncio.run(_send())
    except Exception as exc:
        print(f"[{_ts()}] ⚠️  Telegram send failed: {exc}")


def send_notification(job: dict):
    """Format a job dict and dispatch Telegram + terminal notifications."""
    title = job.get("title", "N/A")
    company = job.get("company", "N/A")
    location = job.get("location", "N/A")
    posted_at = job.get("posted_at", "N/A")
    apply_link = job.get("apply_link", "#")

    html = (
        "🆕 <b>New Fresher Job Alert!</b>\n\n"
        f"💼 <b>Role:</b> {title}\n"
        f"🏢 <b>Company:</b> {company}\n"
        f"📍 <b>Location:</b> {location}\n"
        f"🕐 <b>Posted:</b> {posted_at}\n"
        f'🔗 <b>Apply:</b> <a href="{apply_link}">Click Here</a>\n\n'
        "#fresher #hiring #jobs"
    )

    # Terminal log
    print(
        f"\n[{_ts()}] 🆕 NEW JOB\n"
        f"  Role    : {title}\n"
        f"  Company : {company}\n"
        f"  Location: {location}\n"
        f"  Posted  : {posted_at}\n"
        f"  Apply   : {apply_link}\n"
    )

    send_telegram(html)


def _ts() -> str:
    """Return a short UTC timestamp string."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
