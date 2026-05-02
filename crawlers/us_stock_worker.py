import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 配置區：美股專用 ---
TARGETS = ["META"]
BASE_DATA_DIR = "data/US/stocks"
FMP_KEY = os.getenv("FMP_API_KEY")

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Worker] {msg}")

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

def df_to_dict(df):
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_fmp_api(endpoint, ticker):
    """FMP 美股專項數據"""
    if not FMP_KEY: return None
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{ticker}"
    try:
        r = requests.get(url, params={"apikey": FMP_KEY}, timeout=20)
        return r.json() if r.status_code == 200 else None
    except: return None

def harvest_us_extreme(ticker):
    log(f"🚀 啟動美股極限收割: {ticker}")
    stock = yf.Ticker(ticker)
    
    # 1. 深度財務聯集 (yfinance)
    financial_union = {
        "annual": {
            "income": df_to_dict(stock.financials),
            "balance": df_to_dict(stock.balance_sheet),
            "cashflow": df_to_dict(stock.cashflow)
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials),
            "balance": df_to_dict(stock.quarterly_balance_sheet),
            "cashflow": df_to_dict(stock.quarterly_cashflow)
        }
    }

    # 2. 籌碼面聯集 (機構與內部人)
    holders = {
        "institutional": df_to_dict(stock.institutional_holders),
        "major": df_to_dict(stock.major_holders),
        "insider_transactions": df_to_dict(stock.insider_transactions)
    }

    # 3. 補充水源 (FMP - SOCIE/DCF)
    fmp_data = {
        "socie": safe_fmp_api("statement-of-changes-in-equity", ticker),
        "dcf": safe_fmp_api("discounted-cash-flow", ticker),
        "estimates": safe_fmp_api("analyst-estimates", ticker)
    }

    # 4. 美股新聞
    news = stock.news if hasattr(stock, 'news') else []

    # 封裝
    payload = {
        "metadata": {"ticker": ticker, "market": "US", "ts": datetime.now().isoformat()},
        "financials": financial_union,
        "holders": holders,
        "fmp_ext": fmp_data,
        "news": news,
        "info": stock.info if hasattr(stock, 'info') else {}
    }

    # 存檔 (物理隔離路徑)
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    with open(f"{BASE_DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 美股全量入庫完成")

if __name__ == "__main__":
    for t in TARGETS:
        harvest_us_extreme(t)
