import os
import yfinance as yf
import requests
import json
import time
from datetime import datetime

# --- 配置 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def init_env():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        log(f"📁 自動建立資料夾: {DATA_DIR}")

def safe_api(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=20)
        return r.json() if r.status_code == 200 else None
    except:
        return None

# =========================
# 運算模組：SGR 計算機
# =========================
def calculate_sgr(info):
    """計算可持續成長率: SGR = ROE * (1 - Payout_Ratio)"""
    try:
        roe = info.get('returnOnEquity')
        payout = info.get('payoutRatio')
        if roe is not None and payout is not None:
            sgr = roe * (1 - payout)
            return {"sgr_raw": sgr, "sgr_pct": f"{round(sgr * 100, 2)}%"}
    except:
        pass
    return {"sgr_raw": None, "sgr_pct": "N/A"}

# =========================
# 採集引擎
# =========================
def harvest_full_union(ticker, is_tw=True):
    log(f"🚀 啟動旗艦版採集: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    # 1. yfinance 深度採集
    symbol = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol)
    
    # 2. FMP Stable 全量預測 (US/TW 均嘗試)
    fmp_base = "https://financialmodelingprep.com/stable"
    fmp_res = {
        "profile": safe_api(f"{fmp_base}/profile", {"symbol": ticker, "apikey": fmp_key}),
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "period": "annual", "apikey": fmp_key})
    }

    # 3. FinMind 在地數據 (營收+籌碼+可轉債)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            data = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token, "start_date": "2025-01-01"})
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 數據整合與 SGR 計算
    info = stock.info if stock else {}
    payload = {
        "metadata": {
            "ticker": ticker,
            "is_tw": is_tw,
            "last_update": datetime.now().isoformat()
        },
        "valuation_logic": {
            "sgr_model": calculate_sgr(info),
            "fmp_forecasts": fmp_res,
            "yf_target": info.get('targetMeanPrice')
        },
        "market_data": {
            "price_6m": stock.history(period="6mo").reset_index().to_dict("records") if stock else [],
            "local_chip": fm_res
        },
        "intelligence": {
            "news": stock.news if stock else [],
            "info_snapshot": info
        }
    }

    # 5. 標的隔離儲存
    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    log(f"✅ {ticker}.json 入庫成功")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_full_union(t, True)
    for t in TARGETS["US"]: harvest_full_union(t, False)
    log("🏁 任務全量完成")
