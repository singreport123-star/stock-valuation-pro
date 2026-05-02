import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 專案配置 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log(f"📁 數據保險箱已就緒: {DATA_DIR}")

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
    """強化版 API 請求：處理 403 轉向與 422 校驗"""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            # 針對 FMP 的特定警告進行記錄但不報錯中斷
            log(f"⚠️ API 狀態碼 {r.status_code}: {url.split('apikey=')[0]}")
        except Exception as e:
            log(f"❌ 請求失敗: {e}")
        time.sleep(2)
    return None

# =========================
# 擷取層 (Crawlers)：校準版
# =========================
def harvest_extreme(ticker, is_tw=True):
    log(f"🚀 啟動修復版收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 四大財報 (FMP 採用 Stable 路徑避開 403 Legacy)
    fmp_base = "https://financialmodelingprep.com/stable"
    financial_statements = {
        "annual": {
            "income": df_to_dict(stock.financials, "Annual-Income"),
            "balance": df_to_dict(stock.balance_sheet, "Annual-Balance"),
            "cashflow": df_to_dict(stock.cashflow, "Annual-Cashflow"),
            "socie": safe_api(f"{fmp_base}/statement-of-changes-in-equity", {"symbol": ticker, "apikey": fmp_key})
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials, "Q-Income"),
            "balance": df_to_dict(stock.quarterly_balance_sheet, "Q-Balance"),
            "cashflow": df_to_dict(stock.quarterly_cashflow, "Q-Cashflow")
        }
    }

    # 2. 歷史價量與分析師預期
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except: price_list = []
    
    forecasts = {
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "period": "annual", "apikey": fmp_key})
    }

    # 3. FinMind 在地數據 (對齊探針成功參數)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            # 使用探針證實成功的參數結構
            data = safe_api(fm_url, {
                "dataset": ds, 
                "data_id": ticker, 
                "token": fm_token, 
                "start_date": "2024-01-01"
            })
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 整合存檔
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
    log(f"✅ {ticker}.json 數據包已安全入庫")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_extreme(t, True)
    for t in TARGETS["US"]: harvest_extreme(t, False)
    log("🏁 全量採集任務完成")
