import os

import uvicorn
from dotenv import load_dotenv

from app.core import tracker
from app.core import config as cfg
from app.agent.runner import start_agent
from app.api.server import app


def main():
    load_dotenv()

    for var in ("ANTHROPIC_API_KEY", "COMPOSIO_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        if not os.getenv(var):
            raise EnvironmentError(f"Missing required environment variable: {var}")

    tracker.init_db()

    print("\n" + "=" * 60)
    print("  Jobs Agent")
    print("=" * 60)
    print(f"  Keywords  : {len(cfg.SEARCH_KEYWORDS)} configured")
    for kw in cfg.SEARCH_KEYWORDS:
        print(f"    • {kw}")
    print(f"  Location  : {cfg.LOCATION_FILTER}")
    print(f"  Interval  : every {cfg.POLL_INTERVAL_MINUTES} minutes")
    print(f"  API       : http://localhost:8000/docs")
    print("=" * 60 + "\n")

    start_agent()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")


if __name__ == "__main__":
    main()
