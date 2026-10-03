"""Forecast engine — Prophet + fallback seasonal-average forecaster."""

from __future__ import annotations
import logging
import math
import sys
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from app.config import FORECAST_HORIZON, FORECAST_ENGINE
from app.repo import get_repo
from app.ext import hooks

logger = logging.getLogger(__name__)

# Silence Prophet/cmdstanpy loggers
for _name in ("cmdstanpy", "prophet", "prophet.models", "prophet.plot"):
    logging.getLogger(_name).setLevel(logging.CRITICAL)


# ── Stockout math ───────────────────────────────────────────────
def compute_stockout(stock: int, yhat: list[float], today: date) -> tuple[float, date]:
    """
    Compute days_left and stockout_date given current stock and daily forecast.

    Returns (days_left, stockout_date).
    """
    cum = np.cumsum(yhat)
    indices = np.where(cum >= stock)[0]

    if len(indices) > 0:
        i = indices[0]
        prev_cum = cum[i - 1] if i > 0 else 0
        days_left = i + (stock - prev_cum) / yhat[i]
    else:
        mean_yhat = np.mean(yhat)
        if mean_yhat > 0:
            days_left = len(yhat) + (stock - cum[-1]) / mean_yhat
        else:
            days_left = float("inf")

    stockout_date = today + timedelta(days=math.ceil(days_left))
    return float(days_left), stockout_date


# ── Prophet forecaster ──────────────────────────────────────────
def _prophet_forecast(df: pd.DataFrame, horizon: int = FORECAST_HORIZON, sku: dict | None = None) -> Optional[pd.DataFrame]:
    """Run Prophet forecast. Returns dataframe with ds, yhat, yhat_lower, yhat_upper or None on failure."""
    try:
        from prophet import Prophet

        m = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.8,
        )
        m = hooks.apply("forecast.model", m, sku=sku)
        m.fit(df)

        future = m.make_future_dataframe(periods=horizon)
        # Only keep the forecast period (tomorrow onward)
        forecast = m.predict(future)
        forecast = forecast.tail(horizon).reset_index(drop=True)

        # Clamp to >= 0
        for col in ("yhat", "yhat_lower", "yhat_upper"):
            forecast[col] = forecast[col].clip(lower=0)

        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
    except Exception as e:
        logger.warning(f"Prophet failed: {e}")
        return None


# ── Fallback forecaster ─────────────────────────────────────────
def _fallback_forecast(df: pd.DataFrame, today: date, horizon: int = FORECAST_HORIZON) -> pd.DataFrame:
    """
    Seasonal-average fallback.
    yhat[d] = mean(units on the same weekday over last 8 weeks) × trend_clamp
    trend_clamp = clamp(mean(last14)/mean(last56), 0.8, 1.2)
    lower/upper = yhat ∓ 1.28·std
    """
    df = df.copy()
    df["ds"] = pd.to_datetime(df["ds"])
    df["dow"] = df["ds"].dt.dayofweek

    # Last 56 days (8 weeks)
    cutoff_56 = today - timedelta(days=56)
    recent = df[df["ds"] >= pd.Timestamp(cutoff_56)]

    # Weekday averages and stds
    dow_mean = recent.groupby("dow")["y"].mean()
    dow_std = recent.groupby("dow")["y"].std().fillna(0)

    # Trend adjustment
    cutoff_14 = today - timedelta(days=14)
    last14 = df[df["ds"] >= pd.Timestamp(cutoff_14)]["y"].mean()
    last56 = recent["y"].mean()
    if last56 > 0:
        trend = max(0.8, min(1.2, last14 / last56))
    else:
        trend = 1.0

    rows = []
    for d in range(horizon):
        day = today + timedelta(days=d + 1)  # day 1 = tomorrow
        dow = day.weekday()
        yhat = max(0, dow_mean.get(dow, recent["y"].mean()) * trend)
        std = dow_std.get(dow, 0)
        rows.append({
            "ds": day,
            "yhat": round(yhat, 2),
            "yhat_lower": round(max(0, yhat - 1.28 * std), 2),
            "yhat_upper": round(yhat + 1.28 * std, 2),
        })

    return pd.DataFrame(rows)


def fit_predict(history_df: pd.DataFrame, horizon: int, sku: dict | None = None,
                backtest: bool = False) -> list[dict]:
    """Public engine seam used by extensions for deterministic backtests."""
    today = date.today()
    if FORECAST_ENGINE == "prophet":
        frame = _prophet_forecast(history_df, horizon, sku)
        if frame is None:
            frame = _fallback_forecast(history_df, today, horizon)
    else:
        frame = _fallback_forecast(history_df, today, horizon)
    return [{
        "date": row["ds"].strftime("%Y-%m-%d") if hasattr(row["ds"], "strftime") else str(row["ds"])[:10],
        "yhat": round(float(row["yhat"]), 2),
        "lower": round(float(row["yhat_lower"]), 2),
        "upper": round(float(row["yhat_upper"]), 2),
    } for _, row in frame.iterrows()]


# ── Main forecast runner ────────────────────────────────────────
def forecast_sku(sku_id: str, merchant_id: str = "m1") -> dict:
    """Forecast a single SKU and persist the result."""
    repo = get_repo()
    today = date.today()

    # Get sales history
    sales = repo.get_sales(sku_id, days=120)
    if not sales:
        logger.warning(f"No sales data for {sku_id}")
        return {}

    df = pd.DataFrame(sales)
    df = df.rename(columns={"sale_date": "ds", "units_sold": "y"})
    df["ds"] = pd.to_datetime(df["ds"])

    # Choose engine
    engine_used = FORECAST_ENGINE
    forecast_df = None

    if FORECAST_ENGINE == "prophet":
        forecast_df = _prophet_forecast(df, sku=next((s for s in repo.list_skus(merchant_id) if s["id"] == sku_id), None))
        if forecast_df is not None:
            engine_used = "prophet"
        else:
            logger.info(f"Falling back to seasonal-average for {sku_id}")
            forecast_df = _fallback_forecast(df, today)
            engine_used = "fallback"
    else:
        forecast_df = _fallback_forecast(df, today)
        engine_used = "fallback"

    sku = next((s for s in repo.list_skus(merchant_id) if s["id"] == sku_id), None)
    if not sku:
        return {}

    series = [{
        "date": row["ds"].strftime("%Y-%m-%d") if hasattr(row["ds"], "strftime") else str(row["ds"])[:10],
        "yhat": round(float(row["yhat"]), 2),
        "lower": round(float(row["yhat_lower"]), 2),
        "upper": round(float(row["yhat_upper"]), 2),
    } for _, row in forecast_df.iterrows()]
    series = hooks.apply("forecast.series", series, sku=sku, today=today, backtest=False)
    # Extensions may adjust forecast points (for example, a clearly-labelled
    # festival assumption).  Stockout math must use the adjusted series too.
    yhat_list = [point["yhat"] for point in series]
    days_left, stockout_date = compute_stockout(sku["current_stock"], yhat_list, today)
    avg_daily_demand = float(np.mean(yhat_list[:7]))

    result = {
        "engine": engine_used,
        "avg_daily_demand": round(avg_daily_demand, 2),
        "days_left": round(days_left, 2),
        "stockout_date": stockout_date.isoformat(),
        "series": series,
    }

    repo.upsert_forecast(sku_id, result)
    return result


def run_all_forecasts(merchant_id: str = "m1") -> list[dict]:
    """Run forecasts for all SKUs of a merchant."""
    repo = get_repo()
    skus = repo.list_skus(merchant_id)
    results = []
    for i, sku in enumerate(skus, 1):
        logger.info(f"  Forecasting {sku['id']} ({i}/{len(skus)})...")
        result = forecast_sku(sku["id"], merchant_id)
        results.append({"sku_id": sku["id"], **result})
    return results


# ── CLI entry point ─────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Must seed first
    from app.seed import seed_base, seed_sales
    seed_base()
    seed_sales()

    results = run_all_forecasts("m1")
    repo = get_repo()

    print(f"\n{'SKU':<12} {'Stock':>6} {'Avg/day':>8} {'Days Left':>10} {'Stockout':>12} {'Status':>8} {'Engine':>8}")
    print("-" * 72)

    from app.config import AT_RISK_BUFFER_DAYS
    for r in results:
        sku = next(s for s in repo.list_skus("m1") if s["id"] == r["sku_id"])
        dl = r.get("days_left", 999)
        lead = sku["lead_time_days"]
        if dl <= lead:
            status = "critical"
        elif dl <= lead + AT_RISK_BUFFER_DAYS:
            status = "warning"
        else:
            status = "ok"
        print(f"{r['sku_id']:<12} {sku['current_stock']:>6} {r.get('avg_daily_demand', 0):>8.1f} "
              f"{dl:>10.1f} {r.get('stockout_date', '?'):>12} {status:>8} {r.get('engine', '?'):>8}")
