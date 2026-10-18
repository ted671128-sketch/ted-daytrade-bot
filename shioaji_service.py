import logging
import threading

import shioaji as sj

from app.config import settings

log = logging.getLogger(__name__)


class ShioajiService:
    def __init__(self):
        self.api = None
        self.connected = False
        self._subscribed: set[str] = set()
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        if not (settings.SHIOAJI_API_KEY and settings.SHIOAJI_SECRET_KEY):
            log.warning("未設定 Shioaji 金鑰，行情功能停用")
            return
        try:
            self.api = sj.Shioaji(simulation=settings.SHIOAJI_SIMULATION)
            self.api.login(
                api_key=settings.SHIOAJI_API_KEY,
                secret_key=settings.SHIOAJI_SECRET_KEY,
                contracts_timeout=10000,
            )
            self.connected = True
            log.info("Shioaji 登入成功（simulation=%s）", settings.SHIOAJI_SIMULATION)
        except Exception:
            log.exception("Shioaji 登入失敗，行情功能停用")
            self.api = None

    def _contract(self, code: str):
        try:
            return self.api.Contracts.Stocks[code]
        except (KeyError, AttributeError):
            return None

    def get_stock(self, code: str) -> dict | None:
        if not self.connected:
            return None
        contract = self._contract(code)
        if contract is None:
            log.warning("找不到股票代號：%s", code)
            return None
        try:
            snap = self.api.snapshots([contract])[0]
        except Exception:
            log.exception("取得 snapshot 失敗：%s", code)
            return None
        return {
            "code": code,
            "name": contract.name,
            "close": snap.close,
            "open": snap.open,
            "high": snap.high,
            "low": snap.low,
            "change_rate": snap.change_rate,
            "volume": snap.total_volume,
        }

    def subscribe(self, code: str) -> bool:
        if not self.connected:
            return False
        with self._lock:
            if code in self._subscribed:
                return True
            contract = self._contract(code)
            if contract is None:
                return False
            self.api.quote.subscribe(
                contract,
                quote_type=sj.constant.QuoteType.Tick,
                version=sj.constant.QuoteVersion.v1,
            )
            self._subscribed.add(code)
            return True

    def close(self) -> None:
        if self.api is not None:
            try:
                self.api.logout()
            except Exception:
                log.exception("Shioaji 登出失敗")
