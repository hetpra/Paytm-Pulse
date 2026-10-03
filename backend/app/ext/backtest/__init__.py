"""Honest holdout accuracy metrics and an explicitly-assumed festival uplift."""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

import pandas as pd
from fastapi import APIRouter

from app.ext import hooks
from app.ext.store import get_table
from app.repo import get_repo

FLAG = "backtest"
router = APIRouter()
FESTIVAL_UPLIFT = 1.25


def metrics(actual, predicted) -> dict:
    denom = sum(actual)
    wape = sum(abs(a - p) for a, p in zip(actual, predicted)) / denom if denom else 0.0
    return {"wape": round(wape, 4), "accuracy": round(max(0, 1 - wape), 4)}


def _festival_days(today: date, horizon: int = 21) -> tuple[str, date] | None:
    try:
        import holidays
        indian = holidays.India(years=[today.year, (today + timedelta(days=horizon)).year])
        for holiday, name in sorted(indian.items()):
            if today <= holiday <= today + timedelta(days=horizon):
                return str(name), holiday
    except Exception:
        return None
    return None


def festival_uplift(series: list[dict], *, today: date, backtest: bool = False, **_) -> list[dict]:
    if backtest or FESTIVAL_UPLIFT == 1:
        return series
    festival = _festival_days(today, len(series))
    if not festival:
        return series
    _, holiday = festival
    for point in series:
        day = date.fromisoformat(point["date"])
        if holiday - timedelta(days=2) <= day <= holiday:
            for field in ("yhat", "lower", "upper"):
                point[field] = round(point[field] * FESTIVAL_UPLIFT, 2)
            point["festival"] = True
    return series


def compute_backtest(merchant_id: str = "m1") -> dict:
    from app.forecast import fit_predict
    repo, rows = get_repo(), []
    all_actual, all_pred, all_naive = [], [], []
    for sku in repo.list_skus(merchant_id):
        sales = repo.get_sales(sku["id"], 120)
        if len(sales) < 28:
            continue
        train, holdout = sales[:-14], sales[-14:]
        frame = pd.DataFrame(train).rename(columns={"sale_date":"ds", "units_sold":"y"})
        prediction = fit_predict(frame, 14, sku=sku, backtest=True)
        actual = [row["units_sold"] for row in holdout]
        predicted = [row["yhat"] for row in prediction]
        naive = [sales[len(sales)-14-7+i]["units_sold"] for i in range(14)]
        current, baseline = metrics(actual, predicted), metrics(actual, naive)
        lift = (baseline["wape"] - current["wape"]) / baseline["wape"] * 100 if baseline["wape"] else 0
        rows.append({"sku_id":sku["id"], **current, "naive_wape":baseline["wape"], "naive_accuracy":baseline["accuracy"], "lift_pct":round(lift, 2)})
        all_actual += actual; all_pred += predicted; all_naive += naive
    overall, baseline = metrics(all_actual, all_pred), metrics(all_actual, all_naive)
    festival = _festival_days(date.today())
    return {"ready":True, "engine":"fallback", "holdout_days":14, "overall":{**overall, "naive_wape":baseline["wape"], "naive_accuracy":baseline["accuracy"]}, "skus":rows, "computed_at":datetime.now().isoformat(), "festival":({"name":festival[0], "date":festival[1].isoformat(), "days_away":(festival[1]-date.today()).days, "uplift":FESTIVAL_UPLIFT} if festival else None)}


def _dashboard(payload: dict, merchant_id: str, **_) -> dict:
    stored = get_table("backtests").get(merchant_id)
    if stored:
        payload.setdefault("extras", {})["accuracy"] = stored["result"]
    return payload


@router.get("/")
def get_backtest(merchant_id: str = "m1", refresh: int = 0):
    table = get_table("backtests")
    stored = table.get(merchant_id)
    if refresh or not stored:
        result = compute_backtest(merchant_id)
        if stored: table.update(merchant_id, result=result)
        else: table.insert({"id":merchant_id, "result":result})
    else:
        result = stored["result"]
    return result


def setup(app) -> None:
    hooks.register_filter("forecast.model", lambda model, **_: _add_holidays(model))
    hooks.register_filter("forecast.series", festival_uplift)
    hooks.register_filter("dashboard.payload", _dashboard)


def _add_holidays(model):
    try:
        return model.add_country_holidays(country_name="IN")
    except Exception:
        return model
