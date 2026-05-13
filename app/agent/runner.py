import asyncio
import json
import os
import threading
import time
from datetime import datetime

import anthropic
from composio.tools import ComposioToolSet
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from app.core import config as cfg
from app.core import notifier, tracker
from app.agent import websearch
from app import state


def _ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str):
    print(f"[{_ts()}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Claude agent loop
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
            _log(f"  Calling tool: {block.name}")
            try:
                result = toolset.execute_action(action=block.name, params=block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
            except Exception as exc:
                _log(f"  Tool error ({block.name}): {exc}")
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
# Search
# ---------------------------------------------------------------------------

def _search_keyword(client: anthropic.Anthropic, tools: list, keyword: str) -> int:
    global state

    prompt = (
        f"Search LinkedIn for jobs matching the keyword '{keyword}' "
        f"in the location '{cfg.LOCATION_FILTER}'. "
        f"Return up to {cfg.MAX_JOBS_PER_QUERY} results. "
        "For each job, return a JSON array where every element has these exact keys: "
        "job_id, title, company, location, posted_at, apply_link. "
        "Only return the raw JSON array, no other text."
    )

    try:
        response_text = _run_agent(client, tools, prompt)
    except Exception as exc:
        if "rate limit" in str(exc).lower() or "429" in str(exc):
            _log(f"Rate limited. Waiting 60s before retrying '{keyword}' ...")
            time.sleep(60)
            try:
                response_text = _run_agent(client, tools, prompt)
            except Exception as exc2:
                _log(f"Retry failed for '{keyword}': {exc2}")
                return 0
        else:
            _log(f"Error searching '{keyword}': {exc}")
            return 0

    jobs = _extract_jobs(response_text)

    if not jobs:
        _log(f"  LinkedIn tools returned nothing for '{keyword}'. Falling back to web search ...")
        jobs = websearch.search_jobs(keyword, cfg.LOCATION_FILTER, cfg.MAX_JOBS_PER_QUERY)
        if jobs:
            _log(f"  Web search found {len(jobs)} result(s) for '{keyword}'.")
        else:
            _log(f"  Web search also returned nothing for '{keyword}'.")
            return 0

    _log(f"  {len(jobs)} job(s) returned for '{keyword}'.")
    new_count = 0
    for job in jobs:
        job_id = str(job.get("job_id", "")).strip()
        if not job_id or tracker.is_seen(job_id):
            continue
        notifier.send_notification(job)
        tracker.mark_seen(job_id, job.get("title", ""), job.get("company", ""))
        new_count += 1

    with state.status_lock:
        state.total_new_this_session += new_count

    return new_count


def fetch_and_notify(client: anthropic.Anthropic, tools: list):
    total_new = 0
    for keyword in cfg.SEARCH_KEYWORDS:
        _log(f"Searching: '{keyword}' in {cfg.LOCATION_FILTER} ...")
        total_new += _search_keyword(client, tools, keyword)

    with state.status_lock:
        state.last_cycle_time = _ts()

    seen_total = tracker.get_seen_count()
    _log(f"Cycle complete. {total_new} new job(s) found. Total tracked: {seen_total}")


# ---------------------------------------------------------------------------
# Telegram bot
# ---------------------------------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>Jobs Agent Bot</b>\n\n"
        "Commands:\n"
        "/status — agent status\n"
        "/search &lt;keyword&gt; — trigger immediate search\n"
        "/recent — last 5 jobs tracked\n"
        "/pause — pause auto-polling\n"
        "/resume — resume auto-polling\n"
        "/help — show this message",
        parse_mode="HTML",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, context)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    agent_state = "Paused" if state.paused.is_set() else "Running"
    with state.status_lock:
        last = state.last_cycle_time
        new_count = state.total_new_this_session
    seen_total = tracker.get_seen_count()
    await update.message.reply_text(
        f"<b>Agent Status</b>\n\n"
        f"State         : {agent_state}\n"
        f"Last cycle    : {last}\n"
        f"New (session) : {new_count}\n"
        f"Total tracked : {seen_total}\n"
        f"Poll interval : every {cfg.POLL_INTERVAL_MINUTES} min",
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
    state.paused.set()
    await update.message.reply_text("Paused. Send /resume to restart.")


async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state.paused.clear()
    await update.message.reply_text("Resumed!")


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args).strip()
    if not keyword:
        await update.message.reply_text("Usage: /search <keyword>")
        return
    await update.message.reply_text(f"Queued search for: <b>{keyword}</b>", parse_mode="HTML")
    state.search_queue.put(keyword)


def _run_telegram_bot(token: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("recent", cmd_recent))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("search", cmd_search))

    _log("Telegram bot listening for commands ...")
    app.run_polling(stop_signals=None)


# ---------------------------------------------------------------------------
# Poll loop
# ---------------------------------------------------------------------------

def _poll_loop(client: anthropic.Anthropic, tools: list):
    while True:
        while not state.search_queue.empty():
            keyword = state.search_queue.get()
            _log(f"On-demand search: '{keyword}'")
            new = _search_keyword(client, tools, keyword)
            notifier.send_telegram(
                f"<b>Search complete:</b> '{keyword}'\n"
                f"Found <b>{new}</b> new job(s)."
            )

        if not state.paused.is_set():
            _log("Starting poll cycle ...")
            fetch_and_notify(client, tools)
            _log(f"Sleeping {cfg.POLL_INTERVAL_MINUTES} minutes ...\n")

        for _ in range(cfg.POLL_INTERVAL_MINUTES * 6):
            time.sleep(10)
            if not state.search_queue.empty():
                break


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def start_agent():
    _log("Connecting to Composio and loading LinkedIn tools ...")
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
        _log(f"  {len(tools)} LinkedIn tool(s) loaded.")
    except Exception as exc:
        _log(f"Could not load LinkedIn tools: {exc}")
        tools = []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    bot_thread = threading.Thread(
        target=_run_telegram_bot,
        args=(os.environ["TELEGRAM_BOT_TOKEN"],),
        daemon=True,
        name="telegram-bot",
    )
    bot_thread.start()

    poll_thread = threading.Thread(
        target=_poll_loop,
        args=(client, tools),
        daemon=True,
        name="poll-loop",
    )
    poll_thread.start()

    notifier.send_telegram(
        "✅ <b>Jobs Agent is live!</b>\n"
        f"Monitoring fresher roles in <b>{cfg.LOCATION_FILTER}</b>.\n"
        f"Polling every <b>{cfg.POLL_INTERVAL_MINUTES} minutes</b>.\n\n"
        "Send /help to see available commands."
    )
