import os
from contextlib import contextmanager

from fastapi.testclient import TestClient


@contextmanager
def client_for(flags):
    os.environ.update({"EXT_ENABLED": flags, "DB_MODE": "memory", "LLM_PROVIDER": "none", "FORECAST_ENGINE": "fallback"})
    from app.repo import reset_repo
    from app.main import create_app
    reset_repo()
    with TestClient(create_app()) as client:
        yield client
    reset_repo()
