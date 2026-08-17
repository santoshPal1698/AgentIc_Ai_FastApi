"""
All app-level config comes from environment variables (.env file).
NOTHING user-specific (email, SMTP password, resume, template) lives here —
those are all supplied dynamically per developer/user at runtime via the API.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional; env vars can be set directly instead

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "app.db"))

# Used only to hash/verify API keys server-side — never sent anywhere.
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")
if not APP_SECRET_KEY:
    raise RuntimeError(
        "APP_SECRET_KEY is not set. Create a .env file (see .env.example) "
        "with a random secret, e.g.: openssl rand -hex 32"
    )

# Safety defaults — can be overridden per-campaign, but capped here so no
# developer's misconfiguration can blast thousands of emails/minute.
MAX_DELAY_SECONDS = int(os.getenv("MAX_DELAY_SECONDS", "5"))       # min gap allowed between sends
MAX_DAILY_LIMIT = int(os.getenv("MAX_DAILY_LIMIT", "500"))          # hard ceiling per campaign
