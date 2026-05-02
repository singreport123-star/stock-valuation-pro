import os
import yfinance as yf
import requests
import json
import time
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
        log(f"📁 自動建立資料夾: {DATA_DIR}")

def json_serial(obj):
    """處理 JSON 無法識別的日期與時間格式"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

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
    log(f"🚀 啟動旗艦修復版採集: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    # 1. yfinance 深度採集
    symbol = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol)
    
    # 2. FMP Stable 全量預測
    fmp_base = "https://financialmodelingprep.com/stable"
    fmp_res = {
        "profile": safe_api(f"{fmp_base}/profile", {"symbol": ticker, "apikey": fmp_key}),
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "period": "annual", "apikey": fmp_key})
    }

    # 3. FinMind 在地數據
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            data = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token, "start_date": "2025-01-01"})
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 數據整合與 SGR 計算
    info = stock.info if stock else {}
    # 獲取歷史價格並重設索引，轉換日期為字串
    try:
        history_df = stock.history(period="6mo").reset_index()
        # 關鍵修正：將 DataFrame 中的日期轉換為字串，避免序列化錯誤
        price_list = json.loads(history_df.to_json(orient="records", date_format="iso"))
    except:
        price_list = []

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
            "price_6m": price_list,
            "local_chip": fm_res
        },
        "intelligence": {
            "news": stock.news if stock else [],
            "info_snapshot": info
        }
    }

    # 5. 標的隔離儲存 (使用自定義 default 處理剩餘的 Timestamp)
    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 序列化並入庫成功")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_full_union(t, True)
    for t in TARGETS["US"]: harvest_full_union(t, False)
    log("🏁 任務修復後全量完成")
