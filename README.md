# Jobs Agent

> An AI-powered agentic system that autonomously discovers and delivers fresher/entry-level job opportunities in real time — powered by Claude, Composio, and FastAPI.

---

## Overview

Jobs Agent is an intelligent job tracking system built with an agentic architecture. It uses **Claude (claude-sonnet-4-6)** as the reasoning engine to search LinkedIn for fresher and entry-level job postings, deduplicate results via SQLite, push instant **Telegram notifications**, and expose a **REST API** for programmatic control and data access.

The system runs continuously, polling LinkedIn at a configurable interval. A web search fallback (DuckDuckGo) ensures coverage even when LinkedIn's API returns sparse results.

---

## Key Features

- **Agentic AI Core** — Claude orchestrates LinkedIn tool calls via Composio, parses unstructured responses, and extracts structured job data autonomously
- **Real-time Telegram Alerts** — Instant push notifications for every new job found, with full job details and a direct apply link
- **Interactive Telegram Bot** — Control the agent (`/pause`, `/resume`, `/search`, `/status`) directly from your phone
- **FastAPI REST Interface** — Query tracked jobs, trigger searches, and manage the agent via a clean HTTP API with auto-generated docs
- **Smart Deduplication** — SQLite-backed job store ensures you never receive the same alert twice
- **Web Search Fallback** — DuckDuckGo fallback across LinkedIn, Naukri, Internshala, and Instahyre when primary tools return no results
- **On-demand Search** — Trigger custom keyword searches via Telegram or the API without waiting for the next poll cycle

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        main.py                          │
│          (Entry point — starts agent + API server)      │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────────┐
│  app/agent/     │    │  app/api/            │
│  runner.py      │    │  server.py (FastAPI) │
│                 │    │                      │
│  Poll Loop      │    │  GET  /jobs          │
│  Telegram Bot   │    │  GET  /jobs/recent   │
│  Claude Agent   │    │  GET  /jobs/search   │
│  Web Fallback   │    │  GET  /agent/status  │
└────────┬────────┘    │  POST /agent/search  │
         │             │  POST /agent/pause   │
         │             │  POST /agent/resume  │
         │             └──────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│               app/core/                     │
│  config.py   tracker.py   notifier.py       │
│  (Settings)  (SQLite DB)  (Telegram push)   │
└─────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│   Composio SDK               │
│   LinkedIn Job Search API    │
│   Claude claude-sonnet-4-6   │
└──────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Reasoning | Anthropic Claude (claude-sonnet-4-6) |
| Tool Integration | Composio SDK + LinkedIn API |
| REST API | FastAPI + Uvicorn |
| Notifications | python-telegram-bot |
| Web Fallback | DuckDuckGo Search (ddgs) |
| Persistence | SQLite |
| Config | python-dotenv |

---

## Project Structure

```
jobs-agent/
├── app/
│   ├── agent/
│   │   ├── runner.py        # Claude agent loop, poll cycle, Telegram bot handlers
│   │   └── websearch.py     # DuckDuckGo fallback search
│   ├── api/
│   │   ├── server.py        # FastAPI app instance
│   │   └── routes/
│   │       ├── jobs.py      # Job listing endpoints
│   │       └── agent.py     # Agent control endpoints
│   ├── core/
│   │   ├── config.py        # Keywords, location, intervals
│   │   ├── tracker.py       # SQLite read/write helpers
│   │   └── notifier.py      # Telegram message dispatcher
│   ├── schemas.py           # Pydantic request/response models
│   └── state.py             # Shared in-memory agent state
├── main.py                  # Application entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10+
- A [Composio](https://composio.dev) account with LinkedIn connected
- A Telegram Bot (create via [@BotFather](https://t.me/BotFather))

### 1. Clone and install

```bash
git clone https://github.com/gungunjain36/jobs-agent.git
cd jobs-agent

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `COMPOSIO_API_KEY` | Composio dashboard |
| `TELEGRAM_BOT_TOKEN` | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | `https://api.telegram.org/bot<TOKEN>/getUpdates` |

### 3. Connect LinkedIn via Composio

```bash
composio login
composio add linkedin
```

### 4. Run

```bash
python main.py
```

The agent starts polling immediately. The FastAPI server is available at `http://localhost:8000`.
Interactive API docs: `http://localhost:8000/docs`

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/jobs` | List all tracked jobs (`?limit=20`) |
| `GET` | `/jobs/recent` | Last 5 tracked jobs |
| `GET` | `/jobs/count` | Total jobs tracked |
| `GET` | `/jobs/search?q=` | Search tracked jobs by keyword |
| `GET` | `/agent/status` | Agent state, last cycle time, session stats |
| `POST` | `/agent/search` | Queue an on-demand search `{"keyword": "..."}` |
| `POST` | `/agent/pause` | Pause the polling loop |
| `POST` | `/agent/resume` | Resume the polling loop |
| `GET` | `/health` | Health check |

Full interactive documentation available at `/docs` (Swagger UI) and `/redoc`.

---

## Telegram Bot Commands

| Command | Description |
|---|---|
| `/start` | Show command menu |
| `/status` | View agent state and session stats |
| `/search <keyword>` | Trigger an immediate custom search |
| `/recent` | Show last 5 jobs tracked |
| `/pause` | Pause auto-polling |
| `/resume` | Resume auto-polling |

---

## Configuration

All tunable parameters live in `app/core/config.py`:

| Parameter | Default | Description |
|---|---|---|
| `SEARCH_KEYWORDS` | 5 fresher-focused terms | Keywords sent to LinkedIn search |
| `LOCATION_FILTER` | `"India"` | Target geography |
| `POLL_INTERVAL_MINUTES` | `30` | How often the agent polls LinkedIn |
| `MAX_JOBS_PER_QUERY` | `10` | Max results fetched per keyword per cycle |

---

## Future Roadmap

- **Resume Matching** — Upload a resume and let Claude score each job on fit before sending a notification, filtering out irrelevant listings automatically
- **Multi-platform Support** — Extend beyond LinkedIn to Naukri, Wellfound, and Greenhouse using additional Composio integrations
- **User Dashboard** — React/Next.js frontend to browse tracked jobs, configure keywords, and visualise application history
- **Application Tracking** — Mark jobs as applied/rejected and have Claude draft personalised cold emails or cover letters on demand
- **Smart Scheduling** — Use Claude to learn from application outcomes and dynamically adjust search keywords and timing for better hit rates
- **Email Digest** — Optional daily or weekly email summary of new listings for users who prefer not to use Telegram
- **Webhook Support** — Push new job events to any external system (Notion, Slack, Airtable) via configurable webhooks

---

## License

MIT
