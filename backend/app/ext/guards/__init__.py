"""Pack, MOQ, and conservative overstock ordering safeguards."""
from __future__ import annotations
import math
from app.ext import hooks
from app.ext.store import get_table

FLAG="guards"; router=__import__('fastapi').APIRouter(); MAX_COVER_DAYS=21
RULES={"parle-g":(24,48,.5),"maggi":(24,48,0),"lays":(20,40,1),"coke":(12,24,0),"surf":(6,6,0),"atta":(5,5,.5),"salt":(25,25,0),"tea":(10,10,0)}
def seed(**_):
    table=get_table("sku_order_rules"); table.clear()
    for sku,(pack,moq,sd) in RULES.items():table.insert({"id":sku,"sku_id":sku,"pack":pack,"moq":moq,"lead_time_sd_days":sd})
def lead(value,*,sku,**_):
    rule=get_table("sku_order_rules").get(sku['id']); return int(value+math.ceil(1.28*rule['lead_time_sd_days'])) if rule else value
def adjust(items,*,skus,forecasts,**_):
    source={sku['id']:sku for sku in skus}
    for item in items:
        rule=get_table("sku_order_rules").get(item['sku_id']); sku=source[item['sku_id']]; fc=forecasts.get(item['sku_id'],{}); avg=fc.get('avg_daily_demand',0)
        if not rule or not item['qty']:continue
        changes=[]; q=item['qty']; pack,moq=rule['pack'],rule['moq']; rounded=math.ceil(q/pack)*pack
        if rounded!=q:changes.append(f"rounded to pack of {pack}")
        q=max(rounded,moq); changes.extend([f"raised to MOQ {moq}"] if q==moq and rounded<moq else [])
        cap=math.floor(MAX_COVER_DAYS*avg)-(sku['current_stock']+sku.get('incoming_qty',0))
        if cap<moq:q=0;changes.append("enough cover; MOQ would overstock")
        elif q>cap:q=max(0,math.floor(cap/pack)*pack);changes.append("capped by overstock guard")
        item['qty']=q;item['line_total']=round(q*item['unit_cost'],2);item['adjustments']=changes
    return [item for item in items if item['qty']>0]
def setup(app): hooks.register_event('data.seeded',seed);hooks.register_filter('planner.lead_time',lead);hooks.register_filter('planner.line_items',adjust)
