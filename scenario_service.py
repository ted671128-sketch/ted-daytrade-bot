import logging
from decimal import ROUND_DOWN, ROUND_UP, Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.scenario import Scenario as ScenarioRow
from app.models.watchlist import Watchlist
from app.utils import now_tw

log = logging.getLogger(__name__)


def tick_size(price: float) -> float:
    if price < 10:
        return 0.01
    if price < 50:
        return 0.05
    if price < 100:
        return 0.1
    if price < 500:
        return 0.5
    if price < 1000:
        return 1
    return 5


def snap(price: float, up: bool = False) -> float:
    """對齊台股升降單位。up=True 往上進位，否則往下。"""
    t = Decimal(str(tick_size(price)))
    p = Decimal(str(price))
    mode = ROUND_UP if up else ROUND_DOWN
    return float((p / t).to_integral_value(rounding=mode) * t)


def create_scenario(close_price, high_price, low_price) -> dict | None:
    if not close_price or not high_price or not low_price:
        return None

    tk = tick_size(close_price)
    day_range = max(high_price - low_price, tk)

    breakout = snap(high_price, up=True)

    support = snap(close_price - day_range * 0.3)
    if support >= close_price:
        support = snap(close_price - tk)

    stop = snap(support - day_range * 0.2)
    if stop >= support:
        stop = snap(support - tk)

    target1 = snap(breakout + day_range * 0.5)
    if target1 <= breakout:
        target1 = snap(breakout + tk, up=True)
    target2 = snap(breakout + day_range * 1.0)
    if target2 <= target1:
        target2 = snap(target1 + tk, up=True)

    risk = breakout - stop
    rr = round((target1 - breakout) / risk, 2) if risk > 0 else None

    return {
        "breakout": round(breakout, 2),
        "support": round(support, 2),
        "stop": round(stop, 2),
        "target1": round(target1, 2),
        "target2": round(target2, 2),
        "risk_reward": rr,
    }


def build_plan(svc, db: Session) -> list[dict]:
    """依自選股計算情境並存檔，回傳 [{stock, scenario}, ...]。"""
    today = now_tw().date()
    items: list[dict] = []
    for w in db.query(Watchlist).order_by(Watchlist.id).all():
        stock = svc.get_stock(w.code)
        if not stock:
            continue
        sc = create_scenario(stock["close"], stock["high"], stock["low"])
        if not sc:
            log.warning("%s 價格資料無效，略過", w.code)
            continue
        if stock["name"] and w.name != stock["name"]:
            w.name = stock["name"]
        db.query(ScenarioRow).filter(
            ScenarioRow.code == w.code, ScenarioRow.plan_date == today
        ).delete()
        db.add(
            ScenarioRow(
                code=w.code,
                name=stock["name"],
                plan_date=today,
                close=stock["close"],
                **sc,
            )
        )
        items.append({"stock": stock, "scenario": sc})
    db.commit()
    return items


def run_plan(svc, alerts) -> list[dict]:
    """算計畫、存檔，並重新載入價位警示。"""
    db = SessionLocal()
    try:
        items = build_plan(svc, db)
    finally:
        db.close()
    alerts.load(items)
    return items


def latest_plan_from_db() -> list[dict]:
    """從資料庫取每檔自選股最新一筆情境（重啟後恢復警示用）。"""
    db = SessionLocal()
    try:
        items = []
        for w in db.query(Watchlist).all():
            row = (
                db.query(ScenarioRow)
                .filter(ScenarioRow.code == w.code)
                .order_by(ScenarioRow.id.desc())
                .first()
            )
            if row is None:
                continue
            items.append(
                {
                    "stock": {"code": row.code, "name": row.name, "close": row.close},
                    "scenario": {
                        "breakout": row.breakout,
                        "support": row.support,
                        "stop": row.stop,
                        "target1": row.target1,
                        "target2": row.target2,
                        "risk_reward": row.risk_reward,
                    },
                }
            )
        return items
    finally:
        db.close()
