# LinkedIn Fresher Job Tracker Agent

## 1. What This Does

An AI agent that polls LinkedIn for entry-level / fresher job postings using
Composio's LinkedIn integration and Claude as the reasoning brain. Whenever a
new matching job is found it sends a Telegram notification and prints it to the
terminal. Already-seen jobs are stored in SQLite so you never get duplicate
alerts.

---

## 2. Prerequisites

- Python 3.10+
- A Telegram Bot (instructions below)
- A [Composio](https://composio.dev) account with LinkedIn connected

---

## 3. Setup: Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`, follow the prompts, and copy the **Bot Token**
3. Start a chat with your new bot and send any message (e.g. "hello")
4. Visit the URL below to find your **Chat ID** (look for `"id"` inside `"chat"`):
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
   If the array is empty, send another message to the bot and refresh.
5. Add both values to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   TELEGRAM_CHAT_ID=987654321
   ```

---

## 4. Setup: Composio + LinkedIn

```bash
pip install composio-core
composio login                   # authenticate with your Composio account
composio add linkedin            # follow the OAuth flow to connect LinkedIn
composio actions --app linkedin  # verify the LinkedIn actions are available
```

---

## 5. Setup: Project

```bash
# Clone / enter the project folder
cd linkedin-job-tracker

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the env template and fill in your values
cp .env.example .env
```

Edit `.env` and set all four variables:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | From [console.anthropic.com](https://console.anthropic.com) |
| `COMPOSIO_API_KEY` | From your Composio dashboard |
| `TELEGRAM_BOT_TOKEN` | From @BotFather |
| `TELEGRAM_CHAT_ID` | From the getUpdates URL |

---

## 6. Run

```bash
python agent.py
```

On startup the agent will:
- Print a banner showing all configured keywords and the polling interval
- List every LinkedIn tool it loaded from Composio
- Send a "Tracker is live!" message to your Telegram chat
- Immediately run the first poll cycle, then repeat every 30 minutes

Stop it at any time with **Ctrl+C**.

---

## 7. Customisation

| What to change | Where |
|---|---|
| Search keywords | `config.py` → `SEARCH_KEYWORDS` |
| Target location | `config.py` → `LOCATION_FILTER` |
| Polling frequency | `config.py` → `POLL_INTERVAL_MINUTES` |
| Jobs per query | `config.py` → `MAX_JOBS_PER_QUERY` |

---

## 8. How It Works

```
config.py  (keywords, interval, location)
     |
     v
agent.py  (main polling loop)
     |                  |
     |                  v
     |          Composio SDK ──► LinkedIn Job Search API
     |                  |
     |          Claude claude-sonnet-4-20250514
     |          (parses & extracts structured job list)
     |                  |
     v                  v
tracker.py          notifier.py
(SQLite —           (Telegram Bot  +  terminal log)
 deduplication)
```

### Flow per poll cycle

1. For each keyword in `SEARCH_KEYWORDS`:
   - Claude calls the LinkedIn tool via Composio
   - Claude returns a JSON array of jobs
   - Each job is checked against SQLite
   - New jobs → Telegram notification + SQLite insert
   - Known jobs → silently skipped
2. Summary printed: "X new jobs found. Total tracked: Y"
3. Agent sleeps for `POLL_INTERVAL_MINUTES` minutes, then repeats
