"""Paytm Pulse — FastAPI application entry point."""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS, DB_MODE, LLM_PROVIDER, FORECAST_ENGINE

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Module-level flag
forecasts_ready = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed data + run forecasts."""
    global forecasts_ready
    logger.info("Starting Paytm Pulse...")
    logger.info(f"  DB_MODE={DB_MODE}  LLM_PROVIDER={LLM_PROVIDER}  FORECAST_ENGINE={FORECAST_ENGINE}")

    try:
        from app.seed import seed_all
        seed_all()
        forecasts_ready = True
        logger.info("✅ Seed + forecasts complete. Ready to serve.")
    except Exception as e:
        logger.error(f"Startup seed failed: {e}", exc_info=True)

    yield


def create_app() -> FastAPI:
    """Build an isolated app instance so extension flags can be tested safely."""
    application = FastAPI(title="Paytm Pulse", lifespan=lifespan)
    application.state.enabled_extensions = []
    application.state.available_extensions = []
    application.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health")
    def health():
        return {
            "status": "ok",
            "db_mode": DB_MODE,
            "llm_mode": __import__("app.llm", fromlist=["llm_mode"]).llm_mode(),
            "forecast_engine": FORECAST_ENGINE,
            "forecasts_ready": forecasts_ready,
        }

    from app.routes import router
    application.include_router(router)
    from app.ext import load_extensions
    load_extensions(application)
    return application


# ── Health check ────────────────────────────────────────────────
# ── Mount routes ────────────────────────────────────────────────
app = create_app()
