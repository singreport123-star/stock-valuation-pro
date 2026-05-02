import os
import yfinance as yf
import json
import pandas as pd
from datetime import datetime, date

# --- 診斷強化版 ---
TARGETS = ["META"]
BASE_DATA_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Probe] {msg}")

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

def harvest_us_extreme(ticker):
    log(f"🚀 啟動美股探針收割: {ticker}")
    stock = yf.Ticker(ticker)
    
    # 探針 1: 檢查新聞
    news = stock.news
    log(f"📰 新聞擷取數量: {len(news) if news else 0}")

    # 探針 2: 檢查內部人交易
    insider = stock.insider_transactions
    log(f"👥 內部人交易筆數: {len(insider) if insider is not None else 0}")

    # 封裝數據
    payload = {
        "metadata": {"ticker": ticker, "ts": datetime.now().isoformat()},
        "holders": {"insider_transactions": json.loads(insider.to_json(orient="index")) if insider is not None else {}},
        "news": news if news else [],
        "info": stock.info
    }

    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    with open(f"{BASE_DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 探針入庫完成")

if __name__ == "__main__":
    harvest_us_extreme("META")
