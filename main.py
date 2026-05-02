import os
import yfinance as yf
import requests
import json
from datetime import datetime, date
import pandas as pd

# --- 配置 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def df_to_dict(df):
    """專門處理 yfinance 報表轉 JSON 的輔助函數"""
    if df is None or df.empty:
        return []
    # 轉置 DataFrame 讓日期變成每一筆資料的 Key
    return json.loads(df.to_json(orient="index", date_format="iso"))

def safe_api(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=20)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# =========================
# 採集引擎：超級旗艦版
# =========================
def harvest_extreme(ticker, is_tw=True):
    log(f"🔥 啟動全量報表收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol)
    
    # 1. 抓取【四大報表】(年度與季度)
    log(f"📊 正在下載 {ticker} 完整財報歷史...")
    financials = {
        "income_statement": df_to_dict(stock.financials),
        "balance_sheet": df_to_dict(stock.balance_sheet),
        "cashflow": df_to_dict(stock.cashflow),
        "quarterly_income_statement": df_to_dict(stock.quarterly_financials),
        "quarterly_balance_sheet": df_to_dict(stock.quarterly_balance_sheet),
        "quarterly_cashflow": df_to_dict(stock.quarterly_cashflow)
    }

    # 2. 抓取歷史價量 (6個月)
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except:
        price_list = []

    # 3. FMP 專家預估 (含 2030 矩陣)
    fmp_base = "https://financialmodelingprep.com/stable"
    fmp_data = {
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "period": "annual", "apikey": fmp_key})
    }

    # 4. FinMind 在地數據 (營收抓取從 2024 開始，確保完整)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            data = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token, "start_date": "2024-01-01"})
            fm_res[ds] = data.get("data", []) if data else []

    # 5. 封裝
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat()},
        "financial_statements": financials,
        "market_data": {"price_history": price_list, "local_chip": fm_res},
        "intelligence": {
            "forecasts": fmp_data,
            "news": stock.news if stock else [],
            "info_snapshot": stock.info if stock else {}
        }
    }

    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 超級數據包已完整入庫")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_extreme(t, True)
    for t in TARGETS["US"]: harvest_extreme(t, False)
