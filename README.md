# ted-daytrade-bot

LINE 當沖助理：Shioaji 行情 + FastAPI webhook + APScheduler 晨間推播 + 即時價位警示。
本專案只做行情查詢與通知，不含下單功能。

## 啟動
1. `cp .env.example .env` 並填入 LINE / Shioaji 金鑰
2. `docker compose up -d --build`（或本機 `pip install -r requirements.txt && python run.py`）
3. LINE Developers 後台設定 Webhook URL：`https://你的網域/line/callback`（本機可用 `ngrok http 8000`）
4. 對 bot 傳任意訊息，取得 user id，填入 `.env` 的 `LINE_USER_ID` 後重啟

## LINE 指令
加入 2330 / 移除 2330 / 清單 / 計畫 / 2330（查報價）
