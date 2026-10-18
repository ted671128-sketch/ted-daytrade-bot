import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.line.flex_builder import plan_carousel
from app.services.line_push_service import push_flex, push_text
from app.services.scenario_service import run_plan
from app.utils import is_trading_day

log = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)


def morning_push(svc, alerts) -> None:
    if not is_trading_day():
        log.info("今日休市，略過晨間推播")
        return
    try:
        items = run_plan(svc, alerts)
        if not items:
            push_text("今日無可用計畫（清單為空或行情未連線）")
            return
        for i in range(0, len(items), 12):
            push_flex("今日當沖計畫（依前日收盤計算）", plan_carousel(items[i:i + 12]))
    except Exception:
        log.exception("晨間推播失敗")
        try:
            push_text("⚠️ 晨間推播失敗，請查看 log")
        except Exception:
            log.exception("失敗通知也無法送出")


def start_scheduler(svc, alerts) -> None:
    scheduler.add_job(
        morning_push,
        "cron",
        args=[svc, alerts],
        day_of_week="mon-fri",
        hour=settings.MORNING_PUSH_HOUR,
        minute=settings.MORNING_PUSH_MINUTE,
        id="morning_push",
        replace_existing=True,
        misfire_grace_time=300,
        coalesce=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
