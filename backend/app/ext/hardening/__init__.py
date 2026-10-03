"""Small dependency-free HTTP safety layer and approval audit trail."""
from __future__ import annotations
import time,uuid
from collections import defaultdict,deque
from datetime import datetime,UTC
from fastapi import APIRouter,Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.ext import hooks
from app.ext.store import get_table

FLAG='hardening';router=APIRouter(); _hits=defaultdict(deque); LIMITS={'/api/analyze':10,'/api/ext/ask/':20,'/api/ext/byod/upload':5}
class SafetyMiddleware(BaseHTTPMiddleware):
 async def dispatch(self,request:Request,call_next):
    key=request.url.path; limit=LIMITS.get(key); client=request.client.host if request.client else 'unknown'
    if limit:
      now=time.time(); q=_hits[(id(request.app),client,key)]
      while q and q[0]<=now-60:q.popleft()
      if len(q)>=limit:
       return JSONResponse({"error":{"code":"rate_limited","message":"Try again shortly","request_id":"rate-limit"}},status_code=429,headers={'Retry-After':str(max(1,int(60-(now-q[0]))))})
      q.append(now)
    request_id=uuid.uuid4().hex
    try: response=await call_next(request)
    except Exception: return JSONResponse({"error":{"code":"internal_error","message":"Request failed","request_id":request_id}},500)
    response.headers['X-Request-ID']=request_id;response.headers['X-Content-Type-Options']='nosniff';response.headers['Referrer-Policy']='strict-origin-when-cross-origin';return response
def audit(*,proposal,loan=None,**_):
 payload=proposal.get('payload',{}); import json
 if isinstance(payload,str):payload=json.loads(payload)
 get_table('audit_log').insert({'proposal_id':proposal['id'],'merchant_id':proposal['merchant_id'],'when':datetime.now(UTC).isoformat(),'action':'approved' if proposal.get('status')=='approved' else 'rejected','total':payload.get('total',0),'loan':payload.get('loan_offer')})
@router.get('/audit')
def audit_log(merchant_id:str='m1'):return {'events':get_table('audit_log').list(merchant_id=merchant_id)}
def setup(app):
 _hits.clear()
 app.add_middleware(SafetyMiddleware);hooks.register_event('proposal.approved',audit);hooks.register_event('proposal.rejected',audit)
