import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
import io
from datetime import datetime, date

# --- 配置區：台股專用 ---
TARGETS = ["2330", "4958"]
BASE_DATA_DIR = "data/TW/stocks"
FM_TOKEN = os.getenv("FINMIND_TOKEN")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [TW-Worker] {msg}")

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

def df_to_dict(df):
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_finmind_api(dataset, ticker):
    if not FM_TOKEN: return []
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": dataset,
        "data_id": ticker,
        "token": FM_TOKEN.strip(),
        "start_date": "2024-01-01" # 確保抓取足夠長的歷史用於分析
    }
    try:
        r = requests.get(url, params=params, timeout=25)
        return r.json().get("data", []) if r.status_code == 200 else []
    except: return []

def harvest_tw_extreme(ticker):
    log(f"🚀 啟動台股深度收割: {ticker}")
    stock = yf.Ticker(f"{ticker}.TW")
    
    # 1. 基礎財報 (yfinance)
    financials = {
        "annual": {"income": df_to_dict(stock.financials), "balance": df_to_dict(stock.balance_sheet)},
        "quarterly": {"income": df_to_dict(stock.quarterly_financials), "balance": df_to_dict(stock.quarterly_balance_sheet)}
    }

    # 2. 深度籌碼與 CB 聯集 (FinMind)
    log(f"🔍 正在對接 FinMind 聯集數據 (含 CB、融資券)...")
    chip_union = {
        "month_revenue": safe_finmind_api("TaiwanStockMonthRevenue", ticker),
        "inst_investors": safe_finmind_api("TaiwanStockInstitutionalInvestorsBuySell", ticker),
        "margin_trading": safe_finmind_api("TaiwanStockMarginPurchaseSell", ticker),
        "cb_transaction": safe_finmind_api("ConvertibleBondDailyTransaction", ticker) # 4958 的重點
    }

    # 3. 個股新聞聯集
    # yfinance 提供的是英文或聚合新聞，台股需要額外注意
    news = stock.news if hasattr(stock, 'news') else []

    # 封裝
    payload = {
        "metadata": {"ticker": ticker, "market": "TW", "ts": datetime.now().isoformat()},
        "financials": financials,
        "chip_union": chip_union,
        "news": news,
        "info": stock.info if hasattr(stock, 'info') else {}
    }

    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    with open(f"{BASE_DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 台股全量入庫完成 (含 CB/籌碼/新聞)")

if __name__ == "__main__":
    for t in TARGETS:
        harvest_tw_extreme(t)
