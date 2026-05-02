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
        os.makedirs(DATA_DIR)
        log(f"📁 已建立數據保險箱: {DATA_DIR}")

def json_serial(obj):
    """處理 JSON 無法識別的 Timestamp 與 Date"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError

def df_to_dict(df, name=""):
    """將 yfinance 報表轉為字典，加入空值保護"""
    try:
        if df is None or df.empty:
            log(f"⚠️ {name} 報表為空")
            return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except Exception as e:
        log(f"❌ {name} 轉換出錯: {e}")
        return {}

def safe_api(url, params=None, retries=3):
    """具備重試機制的 API 請求"""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 200:
                return r.json()
            log(f"⚠️ API 狀態碼 {r.status_code}: {url.split('apikey=')[0]}")
        except Exception as e:
            log(f"❌ 請求失敗 (第 {i+1} 次): {e}")
        time.sleep(2)
    return None

def safe_yf_attr(stock, attr):
    """防禦性獲取 yfinance 屬性"""
    try:
        return getattr(stock, attr)
    except Exception as e:
        log(f"⚠️ yfinance 屬性 {attr} 獲取失敗: {e}")
        return None

# =========================
# 運算模組：SGR 計算機 (補回核心功能)
# =========================
def calculate_sgr(info):
    try:
        roe = info.get('returnOnEquity')
        payout = info.get('payoutRatio')
        if roe is not None and payout is not None:
            sgr = roe * (1 - payout)
            return {"sgr_raw": sgr, "sgr_pct": f"{round(sgr * 100, 2)}%"}
    except: pass
    return {"sgr_raw": None, "sgr_pct": "N/A"}

# =========================
# 主收割邏輯
# =========================
def harvest_ultimate(ticker, is_tw=True):
    log(f"🚀 開始旗艦級收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol = f"{ticker}.TW" if is_tw else ticker
    stock = safe_yf_attr(yf, "Ticker")(symbol) if hasattr(yf, "Ticker") else yf.Ticker(symbol)

    # 1. 四大財報 (年度 + 季度) + SOCIE
    fmp_base = "https://financialmodelingprep.com/stable"
    log(f"📊 正在下載 {ticker} 完整財報...")
    financial_statements = {
        "annual": {
            "income_statement": df_to_dict(safe_yf_attr(stock, "financials"), "A-Income"),
            "balance_sheet": df_to_dict(safe_yf_attr(stock, "balance_sheet"), "A-Balance"),
            "cashflow": df_to_dict(safe_yf_attr(stock, "cashflow"), "A-Cashflow"),
            "socie": safe_api(f"{fmp_base}/statement-of-changes-in-equity", {"symbol": ticker, "apikey": fmp_key})
        },
        "quarterly": {
            "income_statement": df_to_dict(safe_yf_attr(stock, "quarterly_financials"), "Q-Income"),
            "balance_sheet": df_to_dict(safe_yf_attr(stock, "quarterly_balance_sheet"), "Q-Balance"),
            "cashflow": df_to_dict(safe_yf_attr(stock, "quarterly_cashflow"), "Q-Cashflow")
        }
    }

    # 2. 價量與預估
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except: price_list = []
    
    forecasts = {
        "dcf": safe_api(f"{fmp_base}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_base}/analyst-estimates", {"symbol": ticker, "period": "annual", "apikey": fmp_key})
    }

    # 3. FinMind 在地數據 (CB + 營收 + 籌碼)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            data = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token, "start_date": "2024-01-01"})
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 深度情報與模型運算
    info = safe_yf_attr(stock, "info") or {}
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat(), "is_tw": is_tw},
        "valuation_logic": {
            "sgr_model": calculate_sgr(info),
            "yf_target": info.get('targetMeanPrice'),
            "fmp_forecasts": forecasts
        },
        "financial_statements": financial_statements,
        "market_data": {"price_history": price_list, "local_chip": fm_res},
        "intelligence": {
            "news": safe_yf_attr(stock, "news") or [],
            "info_snapshot": info
        }
    }

    # 5. 安全序列化入庫
    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 完整封包入庫成功")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_ultimate(t, True)
    for t in TARGETS["US"]: harvest_ultimate(t, False)
    log("🏁 任務全量回歸完成")
