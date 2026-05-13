import json
import os
import time
from datetime import datetime

import anthropic
from composio.tools import ComposioToolSet
from dotenv import load_dotenv

import config
import notifier
import tracker

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    """Return a short UTC timestamp string."""
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _log(msg: str):
    """Print a timestamped log line."""
    print(f"[{_ts()}] {msg}")


# ---------------------------------------------------------------------------
# Agent / tool-calling logic
# ---------------------------------------------------------------------------

def _run_agent(client: anthropic.Anthropic, tools: list, prompt: str) -> str:
    """Run the Claude agentic loop and return the final text response."""
    messages = [{"role": "user", "content": prompt}]
    toolset = ComposioToolSet(api_key=os.environ["COMPOSIO_API_KEY"])

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            tools=tools,
            messages=messages,
        )

        # Collect any tool-use blocks
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if response.stop_reason == "end_turn" or not tool_use_blocks:
            # Extract final text
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool call via Composio and build the user result turn
        tool_results = []
        for block in tool_use_blocks:
            _log(f"  → Calling tool: {block.name}")
            try:
                result = toolset.execute_action(
                    action=block.name,
                    params=block.input,
                )
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
    """
    Parse a JSON array of jobs from Claude's response text.
    Falls back to an empty list if no valid JSON array is found.
    """
    # Try to find a JSON block in the response
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        jobs = json.loads(text[start : end + 1])
        if isinstance(jobs, list):
            return jobs
    except json.JSONDecodeError:
        pass
    return []


# ---------------------------------------------------------------------------
# Main poll cycle
# ---------------------------------------------------------------------------

def fetch_and_notify(client: anthropic.Anthropic, tools: list):
    """Search LinkedIn for each keyword and notify on new fresher jobs."""
    total_new = 0

    for keyword in config.SEARCH_KEYWORDS:
        _log(f"🔍 Searching: '{keyword}' in {config.LOCATION_FILTER} …")

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
            # Handle LinkedIn rate limiting
            if "rate limit" in str(exc).lower() or "429" in str(exc):
                _log(f"⏳ Rate limited. Waiting 60 s before retrying '{keyword}' …")
                time.sleep(60)
                try:
                    response_text = _run_agent(client, tools, prompt)
                except Exception as exc2:
                    _log(f"❌ Retry failed for '{keyword}': {exc2}")
                    continue
            else:
                _log(f"❌ Error searching '{keyword}': {exc}")
                continue

        jobs = _extract_jobs(response_text)

        if not jobs:
            _log(f"  ℹ️  No results returned for '{keyword}'.")
            continue

        _log(f"  ✅ {len(jobs)} job(s) returned for '{keyword}'.")

        for job in jobs:
            job_id = str(job.get("job_id", "")).strip()
            if not job_id:
                continue

            if tracker.is_seen(job_id):
                continue  # already notified

            notifier.send_notification(job)
            tracker.mark_seen(
                job_id,
                job.get("title", ""),
                job.get("company", ""),
            )
            total_new += 1

    seen_total = tracker.get_seen_count()
    _log(f"📊 Cycle complete. {total_new} new job(s) found. Total tracked: {seen_total}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Load config, initialise dependencies, and run the polling loop."""
    load_dotenv()

    # Validate required env vars early
    for var in ("ANTHROPIC_API_KEY", "COMPOSIO_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

    tracker.init_db()

    # Startup banner
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

    # Initialise Composio toolset and discover LinkedIn tools
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
        _log("    Continuing with no tools — Claude will operate in text-only mode.")
        tools = []

    # Initialise Anthropic client
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Send Telegram startup ping
    notifier.send_telegram(
        "✅ <b>LinkedIn Job Tracker is live!</b>\n"
        f"Monitoring for fresher roles in <b>{config.LOCATION_FILTER}</b>.\n"
        f"Polling every <b>{config.POLL_INTERVAL_MINUTES} minutes</b>."
    )

    # Main polling loop
    try:
        while True:
            _log("🚀 Starting poll cycle …")
            fetch_and_notify(client, tools)
            _log(f"💤 Sleeping {config.POLL_INTERVAL_MINUTES} minutes until next cycle …\n")
            time.sleep(config.POLL_INTERVAL_MINUTES * 60)
    except KeyboardInterrupt:
        print("\n\n👋 Tracker stopped by user. Goodbye!\n")


if __name__ == "__main__":
    main()
