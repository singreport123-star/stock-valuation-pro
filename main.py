import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 配置 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log(f"📁 資料空間自動重建: {DATA_DIR}")

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError

def df_to_dict(df, name=""):
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_api(url, params=None, retries=3):
    """強化版請求：針對 402/404/422 進行精準攔截"""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                log(f"⚠️ 路徑不存在 (404): {url.split('?')[0]}")
                break # 路徑錯了重試也沒用
            elif r.status_code == 402:
                log(f"💡 權限不足 (402): 該標的需付費方案")
                return None
            elif r.status_code == 422:
                log(f"❌ 參數無效 (422): 請檢查日期或 Token")
                return None
        except Exception as e:
            log(f"❌ 請求失敗: {e}")
        time.sleep(2)
    return None

# =========================
# 擷取層：終極校準引擎
# =========================
def harvest_extreme(ticker, is_tw=True):
    log(f"🚀 啟動終極校準收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 四大財報 (FMP 採 Path-Parameter 格式避免 404)
    fmp_base = "https://financialmodelingprep.com/api/v3"
    financial_statements = {
        "annual": {
            "income": df_to_dict(stock.financials, "A-Income"),
            "balance": df_to_dict(stock.balance_sheet, "A-Balance"),
            "cashflow": df_to_dict(stock.cashflow, "A-Cashflow"),
            # 修正：FMP 的 SOCIE 需要將 Ticker 放在路徑中
            "socie": safe_api(f"{fmp_base}/statement-of-changes-in-equity/{ticker}", {"apikey": fmp_key})
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials, "Q-Income"),
            "balance": df_to_dict(stock.quarterly_balance_sheet, "Q-Balance"),
            "cashflow": df_to_dict(stock.quarterly_cashflow, "Q-Cashflow")
        }
    }

    # 2. 歷史價量與預測
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except: price_list = []
    
    # 預測部分針對 402 進行靜默處理
    forecasts = {
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "apikey": fmp_key})
    }

    # 3. FinMind (校準 422 參數：確保 start_date 格式嚴謹)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            # 校準：移除多餘字串，確保 token 清淨
            data = safe_api(fm_url, {
                "dataset": ds, 
                "data_id": ticker, 
                "token": fm_token.strip(), 
                "start_date": "2024-01-01" 
            })
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 數據整合
    info = stock.info if hasattr(stock, 'info') else {}
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat(), "is_tw": is_tw},
        "financial_statements": financial_statements,
        "market_data": {"price_history": price_list, "local_chip": fm_res},
        "intelligence": {
            "forecasts": forecasts,
            "news": stock.news if hasattr(stock, 'news') else [],
            "info_snapshot": info
        }
    }

    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 數據入庫完成")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_extreme(t, True)
    for t in TARGETS["US"]: harvest_extreme(t, False)
