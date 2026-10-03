"""Paytm Pulse — configuration (all business constants live here)."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ── Infrastructure ──────────────────────────────────────────────
DB_MODE: str = os.getenv("DB_MODE", "memory")                # memory | supabase
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")        # none | openrouter | anthropic | openai
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "")                  # optional override

FORECAST_ENGINE: str = os.getenv("FORECAST_ENGINE", "prophet")  # prophet | fallback
MERCHANT_ID: str = os.getenv("MERCHANT_ID", "m1")
CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

# ── Business constants ──────────────────────────────────────────
FORECAST_HORIZON: int = 21          # days forecast ahead
COVER_DAYS: int = 7                 # days of stock wanted after an order arrives
SAFETY_FACTOR: float = 1.10        # demand buffer
AT_RISK_BUFFER_DAYS: int = 3       # warning window beyond lead time
OPERATING_RESERVE: float = 1000    # ₹ merchant must keep in cash
PLATFORM_FEE_PCT: float = 1.0     # % of PO subtotal (Paytm income)
LOAN_RATE_PCT: float = 1.5        # flat for the whole tenure
LOAN_PROC_FEE_PCT: float = 1.0    # % of principal
LOAN_TENURE_DAYS: int = 30
LOAN_ROUNDING: int = 500           # principal rounded up to this multiple
PREMIUM_PRICE: float = 499         # ₹/month
