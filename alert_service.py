import logging
import threading
from concurrent.futures import ThreadPoolExecutor

from app.utils import in_trading_hours

log = logging.getLogger(__name__)


class Alert:
    def __init__(self, code, name, kind, level, direction):
        self.code, self.name = code, name
        self.kind = kind            # 突破 / 支撐 / 停損
        self.level = level
        self.direction = direction  # up：>= 觸發；down：<= 觸發
        self.fired = False


class AlertService:
    """訂閱即時 tick，價位觸發時推播一次。"""

    def __init__(self, svc, notify):
        self.svc = svc
        self.notify = notify
        self._alerts: dict[str, list[Alert]] = {}
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=2)
        if svc.connected:
            svc.api.quote.set_on_tick_stk_v1_callback(self._on_tick)

    def load(self, items: list[dict]) -> None:
        """以新的計畫取代所有警示（同時重置 fired 狀態）。"""
        new: dict[str, list[Alert]] = {}
        for it in items:
            s, sc = it["stock"], it["scenario"]
            code, name = s["code"], s.get("name", "")
            new[code] = [
                Alert(code, name, "突破", sc["breakout"], "up"),
                Alert(code, name, "支撐", sc["support"], "down"),
                Alert(code, name, "停損", sc["stop"], "down"),
            ]
        with self._lock:
            self._alerts = new
        for code in new:
            if not self.svc.subscribe(code):
                log.warning("訂閱失敗：%s", code)
        log.info("已載入 %d 檔警示", len(new))

    def _on_tick(self, exchange, tick) -> None:
        alerts = self._alerts.get(tick.code)
        if not alerts or not in_trading_hours():
            return
        price = float(tick.close)
        for a in alerts:
            with self._lock:
                if a.fired:
                    continue
                hit = price >= a.level if a.direction == "up" else price <= a.level
                if not hit:
                    continue
                a.fired = True
            if a.kind == "突破":
                msg = f"🔔 {a.name}({a.code}) 突破 {a.level}\n現價：{price}"
            else:
                msg = f"⚠️ {a.name}({a.code}) 跌破{a.kind} {a.level}\n現價：{price}"
            self._pool.submit(self._safe_notify, msg)

    def _safe_notify(self, msg: str) -> None:
        try:
            self.notify(msg)
        except Exception:
            log.exception("警示推播失敗")

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False)
