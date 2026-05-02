import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 配置區 (標的隔離) ---
TARGETS = {"TW": ["2330"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    """環境自癒：自動重建資料目錄"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log(f"📁 已重新建立數據保險箱: {DATA_DIR}")

def json_serial(obj):
    """處理序列化地雷 (Timestamp/Date)"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    return str(obj)

def df_to_dict(df, name=""):
    """安全轉換 DataFrame 為字典"""
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_api(url, params=None, method="GET", data=None):
    """具備重試機制的靜默請求 (Anti-Choke)"""
    for _ in range(2):
        try:
            if method == "POST":
                r = requests.post(url, data=data, timeout=25)
            else:
                r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200: return r.json()
        except: time.sleep(2)
    return None

# =========================
# 數據源插件 (Pluggable)
# =========================
def get_mops_summary(year="113", season="1"):
    """MOPS 原始爬蟲插件：直接從官網抓取彙總表 (解決掐脖子問題)"""
    url = "https://mops.twse.com.tw/mops/web/ajax_t163sb04"
    payload = {
        "encodeURIComponent": 1, "step": 1, "firstin": 1, "off": 1,
        "TYPEK": "sii", "year": year, "season": season
    }
    try:
        res = requests.post(url, data=payload, timeout=20)
        tables = pd.read_html(res.text)
        return tables
    except: return []

def calculate_sgr(info):
    """可持續成長率: $SGR = ROE \times (1 - \text{Payout Ratio})$"""
    try:
        roe = info.get('returnOnEquity')
        payout = info.get('payoutRatio')
        if roe is not None and payout is not None:
            sgr = roe * (1 - payout)
            return {"sgr_raw": sgr, "sgr_pct": f"{round(sgr * 100, 2)}%"}
    except: pass
    return {"sgr_raw": None, "sgr_pct": "N/A"}

# =========================
# 擷取主邏輯 (Invincible Edition)
# =========================
def harvest_invincible(ticker, is_tw=True):
    log(f"🚀 啟動韌性採集: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 核心肉源 (yfinance) - 包含四大報表與季報
    log(f"📊 抓取 {ticker} 核心財報與季報...")
    financial_statements = {
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

    # 2. 備援源 (FMP/FinMind/MOPS)
    fmp_v3 = "https://financialmodelingprep.com/api/v3"
    supplementary = {
        "socie": safe_api(f"{fmp_v3}/statement-of-changes-in-equity/{ticker}", {"apikey": fmp_key}),
        "dcf": safe_api(f"{fmp_v3}/discounted-cash-flow/{ticker}", {"apikey": fmp_key})
    }

    local_chip = {}
    if is_tw:
        # 整合 MOPS 原始數據 (僅示範路徑)
        mops_data = get_mops_summary()
        local_chip["mops_snapshot"] = "Detected" if len(mops_data) > 0 else "None"
        
        # FinMind 備援 (2026 探針版)
        if fm_token:
            fm_url = "https://api.finmindtrade.com/api/v4/data"
            for ds in ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell"]:
                res = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token.strip(), "start_date": "2026-01-01"})
                local_chip[ds] = res.get("data", []) if res else []

    # 3. 數據整合與 SGR 運算
    info = stock.info if hasattr(stock, 'info') else {}
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat(), "is_tw": is_tw},
        "valuation_logic": {
            "sgr_model": calculate_sgr(info),
            "target_price": info.get('targetMeanPrice'),
            "fmp_forecasts": supplementary
        },
        "financial_statements": financial_statements,
        "market_data": {"local_chip": local_chip},
        "intelligence": {
            "news": stock.news if hasattr(stock, 'news') else [],
            "info_snapshot": info
        }
    }

    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 韌性入庫完成")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_invincible(t, True)
    for t in TARGETS["US"]: harvest_invincible(t, False)
    log("🏁 收割任務順利完成")
