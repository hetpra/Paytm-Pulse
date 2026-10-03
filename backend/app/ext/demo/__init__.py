"""Judge-facing status endpoint; frontend supplies the optional guided tour."""
from __future__ import annotations
from fastapi import APIRouter,Request
from app.config import DB_MODE,FORECAST_ENGINE
from app.llm import llm_mode
FLAG='demo';router=APIRouter()
def setup(app):
 @app.get('/status')
 def status(request:Request):
  from app.main import forecasts_ready
  return {'status':'ok','db_mode':DB_MODE,'llm_mode':llm_mode(),'forecast_engine':FORECAST_ENGINE,'enabled_extensions':request.app.state.enabled_extensions,'forecasts_ready':forecasts_ready,'version':'demo'}
