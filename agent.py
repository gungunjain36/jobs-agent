import asyncio
import json
import os
import queue
import threading
import time
from datetime import datetime

import anthropic
from composio.tools import ComposioToolSet
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import config
import notifier
import tracker
import websearch

# ---------------------------------------------------------------------------
# Globals for cross-thread state
# ---------------------------------------------------------------------------

_paused = threading.Event()   # set = paused, clear = running
_search_queue: queue.Queue = queue.Queue()
_status_lock = threading.Lock()
_last_cycle_time: str = "never"
_total_new_this_session: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str):
    print(f"[{_ts()}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Agent / tool-calling logic
# ---------------------------------------------------------------------------

def _run_agent(client: anthropic.Anthropic, tools: list, prompt: str) -> str:
    messages = [{"role": "user", "content": prompt}]
    toolset = ComposioToolSet(api_key=os.environ["COMPOSIO_API_KEY"])

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if response.stop_reason == "end_turn" or not tool_use_blocks:
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in tool_use_blocks:
            _log(f"  → Calling tool: {block.name}")
            try:
                result = toolset.execute_action(action=block.name, params=block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
            except Exception as exc:
                _log(f"  ⚠️  Tool error ({block.name}): {exc}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Error: {exc}",
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# Job extraction
# ---------------------------------------------------------------------------

def _extract_jobs(text: str) -> list[dict]:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        jobs = json.loads(text[start:end + 1])
        if isinstance(jobs, list):
            return jobs
    except json.JSONDecodeError:
        pass
    return []


# ---------------------------------------------------------------------------
# Search logic
# ---------------------------------------------------------------------------

def _search_keyword(client: anthropic.Anthropic, tools: list, keyword: str) -> int:
    """Search one keyword, notify on new jobs. Returns count of new jobs found."""
    global _total_new_this_session

    prompt = (
        f"Search LinkedIn for jobs matching the keyword '{keyword}' "
        f"in the location '{config.LOCATION_FILTER}'. "
        f"Return up to {config.MAX_JOBS_PER_QUERY} results. "
        "For each job, return a JSON array where every element has these exact keys: "
        "job_id, title, company, location, posted_at, apply_link. "
        "Only return the raw JSON array, no other text."
    )

    try:
        response_text = _run_agent(client, tools, prompt)
    except Exception as exc:
        if "rate limit" in str(exc).lower() or "429" in str(exc):
            _log(f"⏳ Rate limited. Waiting 60s before retrying '{keyword}' …")
            time.sleep(60)
            try:
                response_text = _run_agent(client, tools, prompt)
            except Exception as exc2:
                _log(f"❌ Retry failed for '{keyword}': {exc2}")
                return 0
        else:
            _log(f"❌ Error searching '{keyword}': {exc}")
            return 0

    jobs = _extract_jobs(response_text)

    # Fallback: LinkedIn tools gave nothing — use DuckDuckGo web search
    if not jobs:
        _log(f"  ℹ️  LinkedIn tools returned nothing for '{keyword}'. Falling back to web search …")
        jobs = websearch.search_jobs(keyword, config.LOCATION_FILTER, config.MAX_JOBS_PER_QUERY)
        if jobs:
            _log(f"  🌐 Web search found {len(jobs)} result(s) for '{keyword}'.")
        else:
            _log(f"  ℹ️  Web search also returned nothing for '{keyword}'.")
            return 0

    _log(f"  ✅ {len(jobs)} job(s) returned for '{keyword}'.")
    new_count = 0
    for job in jobs:
        job_id = str(job.get("job_id", "")).strip()
        if not job_id or tracker.is_seen(job_id):
            continue
        notifier.send_notification(job)
        tracker.mark_seen(job_id, job.get("title", ""), job.get("company", ""))
        new_count += 1

    with _status_lock:
        _total_new_this_session += new_count

    return new_count


def fetch_and_notify(client: anthropic.Anthropic, tools: list):
    global _last_cycle_time
    total_new = 0
    for keyword in config.SEARCH_KEYWORDS:
        _log(f"🔍 Searching: '{keyword}' in {config.LOCATION_FILTER} …")
        total_new += _search_keyword(client, tools, keyword)

    with _status_lock:
        _last_cycle_time = _ts()

    seen_total = tracker.get_seen_count()
    _log(f"📊 Cycle complete. {total_new} new job(s) found. Total tracked: {seen_total}")


# ---------------------------------------------------------------------------
# Telegram bot command handlers
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>LinkedIn Job Tracker Bot</b>\n\n"
        "Available commands:\n"
        "/status — show current bot status\n"
        "/search &lt;keyword&gt; — trigger an immediate search\n"
        "/recent — show last 5 jobs tracked\n"
        "/pause — pause auto-polling\n"
        "/resume — resume auto-polling\n"
        "/help — show this message",
        parse_mode="HTML",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = "⏸ Paused" if _paused.is_set() else "▶️ Running"
    with _status_lock:
        last = _last_cycle_time
        new_count = _total_new_this_session
    seen_total = tracker.get_seen_count()
    await update.message.reply_text(
        f"<b>Bot Status</b>\n\n"
        f"State      : {state}\n"
        f"Last cycle : {last}\n"
        f"New (session): {new_count}\n"
        f"Total tracked: {seen_total}\n"
        f"Poll interval: every {config.POLL_INTERVAL_MINUTES} min",
        parse_mode="HTML",
    )


async def cmd_recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    jobs = tracker.get_recent_jobs(5)
    if not jobs:
        await update.message.reply_text("No jobs tracked yet.")
        return
    lines = ["<b>Last 5 jobs tracked:</b>\n"]
    for j in jobs:
        lines.append(f"• <b>{j['title']}</b> @ {j['company']}\n  <i>{j['seen_at']}</i>")
    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _paused.set()
    await update.message.reply_text("⏸ Auto-polling paused. Send /resume to restart.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    _paused.clear()
    await update.message.reply_text("▶️ Auto-polling resumed!")


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("Usage: /search <keyword>\nExample: /search ML engineer fresher")
        return
    await update.message.reply_text(f"🔍 Queued search for: <b>{keyword}</b>", parse_mode="HTML")
    _search_queue.put(keyword)


# ---------------------------------------------------------------------------
# Telegram bot thread
# ---------------------------------------------------------------------------

def _run_bot(token: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = (
        Application.builder()
        .token(token)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("recent", cmd_recent))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("search", cmd_search))

    _log("🤖 Telegram bot listening for commands …")
    app.run_polling(stop_signals=None)


# ---------------------------------------------------------------------------
# Main polling loop
# ---------------------------------------------------------------------------

def _poll_loop(client: anthropic.Anthropic, tools: list):
    while True:
        # Drain any on-demand search requests first
        while not _search_queue.empty():
            keyword = _search_queue.get()
            _log(f"📨 On-demand search: '{keyword}'")
            new = _search_keyword(client, tools, keyword)
            notifier.send_telegram(
                f"🔍 <b>Search complete:</b> '{keyword}'\n"
                f"Found <b>{new}</b> new job(s)."
            )

        if not _paused.is_set():
            _log("🚀 Starting poll cycle …")
            fetch_and_notify(client, tools)
            _log(f"💤 Sleeping {config.POLL_INTERVAL_MINUTES} minutes …\n")

        # Sleep in small increments so we catch queue items and pause changes quickly
        for _ in range(config.POLL_INTERVAL_MINUTES * 6):
            time.sleep(10)
            if not _search_queue.empty():
                break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    for var in ("ANTHROPIC_API_KEY", "COMPOSIO_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

    tracker.init_db()

    print("\n" + "=" * 60)
    print("  LinkedIn Fresher Job Tracker")
    print("=" * 60)
    print(f"  Keywords  : {len(config.SEARCH_KEYWORDS)} configured")
    for kw in config.SEARCH_KEYWORDS:
        print(f"    • {kw}")
    print(f"  Location  : {config.LOCATION_FILTER}")
    print(f"  Interval  : every {config.POLL_INTERVAL_MINUTES} minutes")
    print(f"  Max/query : {config.MAX_JOBS_PER_QUERY} jobs")
    print("=" * 60 + "\n")

    _log("🔧 Connecting to Composio and loading LinkedIn tools …")
    toolset = ComposioToolSet(api_key=os.environ["COMPOSIO_API_KEY"])

    try:
        schemas = toolset.get_action_schemas(apps=["linkedin"])
        tools = [
            {
                "name": s.name,
                "description": s.description,
                "input_schema": s.parameters.model_dump() if hasattr(s.parameters, "model_dump") else dict(s.parameters),
            }
            for s in schemas
        ]
        _log(f"  ✅ {len(tools)} LinkedIn tool(s) loaded:")
        for t in tools:
            print(f"    • {t['name']}")
    except Exception as exc:
        _log(f"⚠️  Could not load LinkedIn tools: {exc}")
        tools = []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Start Telegram bot in a background daemon thread
    bot_thread = threading.Thread(
        target=_run_bot,
        args=(os.environ["TELEGRAM_BOT_TOKEN"],),
        daemon=True,
        name="telegram-bot",
    )
    bot_thread.start()

    notifier.send_telegram(
        "✅ <b>LinkedIn Job Tracker is live!</b>\n"
        f"Monitoring fresher roles in <b>{config.LOCATION_FILTER}</b>.\n"
        f"Polling every <b>{config.POLL_INTERVAL_MINUTES} minutes</b>.\n\n"
        "Send /help to see available commands."
    )

    try:
        _poll_loop(client, tools)
    except KeyboardInterrupt:
        print("\n\n👋 Tracker stopped by user. Goodbye!\n")


if __name__ == "__main__":
    main()
