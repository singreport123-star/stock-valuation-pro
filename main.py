import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 配置區 ---
TARGETS = {"TW": ["2330"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log(f"📁 數據空間已重新初始化: {DATA_DIR}")

def json_serial(obj):
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

def df_to_dict(df, name=""):
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_api(url, params=None, method="GET", data=None):
    """聯集專用請求器：失敗僅記錄，不影響其他水源採集"""
    for _ in range(2):
        try:
            if method == "POST":
                r = requests.post(url, data=data, timeout=25)
            else:
                r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200: return r.json()
            if r.status_code in [402, 403, 422]: break # 權限或參數錯誤，跳過
        except: time.sleep(2)
    return None

# =========================
# 水源模組：MOPS 原始爬蟲 (台股專用)
# =========================
def scrape_mops_union(ticker):
    """直接從 MOPS 官方源頭抓取彙總表，實現原始數據聯集"""
    url = "https://mops.twse.com.tw/mops/web/ajax_t163sb04"
    payload = {
        "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1,
        "TYPEK": "sii", "year": "113", "season": "1"
    }
    try:
        res = requests.post(url, data=payload, timeout=20)
        tables = pd.read_html(res.text)
        # 過濾出該標的的特定行 (聯集過濾邏輯)
        for df in tables:
            if '公司代碼' in df.columns and str(ticker) in df['公司代碼'].astype(str).values:
                return json.loads(df[df['公司代碼'].astype(str) == str(ticker)].to_json(orient="records"))
    except: pass
    return []

# =========================
# 收割主邏輯 (Union Strategy)
# =========================
def harvest_union(ticker, is_tw=True):
    log(f"🚀 啟動全量數據聯集採集: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 第一路水源: yfinance (基礎財報/年報/季報)
    financials = {
        "annual": {
            "income": df_to_dict(stock.financials, "A-Income"),
            "balance": df_to_dict(stock.balance_sheet, "A-Balance"),
            "cashflow": df_to_dict(stock.cashflow, "A-Cashflow")
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials, "Q-Income"),
            "balance": df_to_dict(stock.quarterly_balance_sheet, "Q-Balance"),
            "cashflow": df_to_dict(stock.quarterly_cashflow, "Q-Cashflow")
        }
    }

    # 2. 第二路水源: FMP (官方文件校準路徑)
    fmp_v3 = "https://financialmodelingprep.com/api/v3"
    fmp_data = {
        "socie": safe_api(f"{fmp_v3}/statement-of-changes-in-equity/{ticker}", {"apikey": fmp_key}),
        "dcf": safe_api(f"{fmp_v3}/discounted-cash-flow/{ticker}", {"apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_v3}/analyst-estimates/{ticker}", {"apikey": fmp_key})
    }

    # 3. 第三路水源: FinMind (在地籌碼/營收)
    local_data = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        for ds in ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell"]:
            res = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token.strip(), "start_date": "2026-01-01"})
            local_data[ds] = res.get("data", []) if res else []

    # 4. 第四路水源: MOPS 官方原始數據 (台股專用)
    mops_data = scrape_mops_union(ticker) if is_tw else []

    # 5. 數據大聯集封裝
    info = stock.info if hasattr(stock, 'info') else {}
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat(), "is_tw": is_tw},
        "all_financial_sources": {
            "yf_core": financials,
            "fmp_extension": fmp_data,
            "mops_official": mops_data
        },
        "market_and_chip": {
            "finmind_local": local_data,
            "yf_history": df_to_dict(stock.history(period="6mo").reset_index(), "Price-Hist")
        },
        "intelligence": {
            "news": stock.news if hasattr(stock, 'news') else [],
            "snapshot": info
        }
    }

    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 聯集入庫成功 (包含 MOPS/FMP/FinMind/yf)")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_union(t, True)
    for t in TARGETS["US"]: harvest_union(t, False)
    log("🏁 聯集收割任務完成")
