import asyncio
import logging
import re

from fastapi import APIRouter, Header, HTTPException, Request
from linebot.v3 import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.config import settings
from app.database import SessionLocal
from app.line.flex_builder import plan_carousel
from app.models.watchlist import Watchlist
from app.services.line_push_service import reply_flex, reply_text
from app.services.scenario_service import run_plan

log = logging.getLogger(__name__)
router = APIRouter()
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)

CODE = r"([0-9A-Za-z]{4,6})"
HELP = (
    "指令：\n"
    "加入 2330　加入自選股\n"
    "移除 2330　移除自選股\n"
    "清單　查看自選股\n"
    "計畫　立即產生情境並啟用警示\n"
    "2330　查詢報價"
)


def handle_text(event: MessageEvent, svc, alerts) -> None:
    uid = event.source.user_id
    token = event.reply_token
    text = event.message.text.strip()

    if not settings.LINE_USER_ID:
        reply_text(token, f"尚未設定 LINE_USER_ID。\n你的 user id：\n{uid}\n請填入 .env 後重啟。")
        return
    if uid != settings.LINE_USER_ID:
        log.warning("忽略非白名單使用者：%s", uid)
        return

    if m := re.fullmatch(rf"(?:加入|新增)\s*{CODE}", text):
        code = m.group(1).upper()
        if svc.connected and svc.get_stock(code) is None:
            reply_text(token, f"找不到 {code}")
            return
        db = SessionLocal()
        try:
            if db.query(Watchlist).filter_by(code=code).first():
                reply_text(token, f"{code} 已在清單")
            else:
                db.add(Watchlist(code=code))
                db.commit()
                reply_text(token, f"已加入 {code}，輸入「計畫」立即產生情境")
        finally:
            db.close()
        return

    if m := re.fullmatch(rf"(?:移除|刪除)\s*{CODE}", text):
        code = m.group(1).upper()
        db = SessionLocal()
        try:
            n = db.query(Watchlist).filter_by(code=code).delete()
            db.commit()
        finally:
            db.close()
        reply_text(token, f"已移除 {code}" if n else f"清單中沒有 {code}")
        return

    if text in ("清單", "list"):
        db = SessionLocal()
        try:
            rows = db.query(Watchlist).order_by(Watchlist.id).all()
        finally:
            db.close()
        body = "\n".join(f"{r.code} {r.name}".strip() for r in rows) or "（空）"
        reply_text(token, f"自選股：\n{body}")
        return

    if text in ("計畫", "plan"):
        if not svc.connected:
            reply_text(token, "行情服務未連線，請檢查 Shioaji 設定")
            return
        items = run_plan(svc, alerts)
        if not items:
            reply_text(token, "沒有可用資料（清單為空，或非交易時間無報價）")
            return
        reply_flex(token, "當沖計畫", plan_carousel(items))
        return

    if re.fullmatch(CODE, text) and text[0].isdigit():
        data = svc.get_stock(text.upper())
        if not data:
            reply_text(token, f"查無 {text}（或行情服務未連線）")
            return
        reply_text(
            token,
            f"{data['code']} {data['name']}\n現價 {data['close']}　"
            f"漲跌幅 {data['change_rate']}%\n高 {data['high']}　低 {data['low']}",
        )
        return

    reply_text(token, HELP)


@router.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(...)):
    body = (await request.body()).decode("utf-8")
    try:
        events = parser.parse(body, x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    svc = request.app.state.shioaji
    alerts = request.app.state.alerts
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            try:
                await asyncio.to_thread(handle_text, event, svc, alerts)
            except Exception:
                log.exception("處理訊息失敗")
    return {"status": "ok"}
