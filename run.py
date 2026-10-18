import uvicorn

if __name__ == "__main__":
    # 單一 worker：排程與 Shioaji 連線不能重複
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
