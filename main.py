import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.line.webhook import router as line_router
from app.scheduler.push_job import start_scheduler, stop_scheduler
from app.services.alert_service import AlertService
from app.services.line_push_service import push_text
from app.services.scenario_service import latest_plan_from_db
from app.services.shioaji_service import ShioajiService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    svc = ShioajiService()
    alerts = AlertService(svc, push_text)
    app.state.shioaji = svc
    app.state.alerts = alerts

    alerts.load(latest_plan_from_db())  # 重啟後恢復警示
    start_scheduler(svc, alerts)
    yield
    stop_scheduler()
    alerts.shutdown()
    svc.close()


app = FastAPI(title="ted-daytrade-bot", lifespan=lifespan)
app.include_router(line_router, prefix="/line")


@app.get("/health")
def health():
    return {"status": "ok", "shioaji": app.state.shioaji.connected}
