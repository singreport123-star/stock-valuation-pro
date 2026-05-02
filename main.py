import os
import yfinance as yf
import requests
import json
import time
import pandas as pd
from datetime import datetime, date

# --- 專案配置 (標的隔離) ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
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
    raise TypeError

def df_to_dict(df, name=""):
    """處理 yfinance 報表格式轉換"""
    try:
        if df is None or df.empty: return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except: return {}

def safe_api(url, params=None, retries=3):
    """具備重試機制的 API 請求"""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            log(f"⚠️ API 狀態碼 {r.status_code}: {url.split('apikey=')[0]}")
        except Exception as e:
            log(f"❌ 請求失敗 (第 {i+1} 次): {e}")
        time.sleep(2)
    return None

# =========================
# 邏輯層 (Models)：SGR 計算
# =========================
def calculate_sgr(info):
    """可持續成長率: SGR = ROE * (1 - Payout_Ratio)"""
    try:
        roe = info.get('returnOnEquity')
        payout = info.get('payoutRatio')
        if roe is not None and payout is not None:
            sgr = roe * (1 - payout)
            return {"sgr_raw": sgr, "sgr_pct": f"{round(sgr * 100, 2)}%"}
    except: pass
    return {"sgr_raw": None, "sgr_pct": "N/A"}

# =========================
# 擷取層 (Crawlers)：官方文件校準版
# =========================
def harvest_ultimate(ticker, is_tw=True):
    log(f"🚀 啟動終極校準收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 四大財報 (對齊 FMP 官方 v3 Path-Parameter 格式)
    fmp_v3 = "https://financialmodelingprep.com/api/v3"
    log(f"📊 正在下載 {ticker} 完整年報/季報/權益變動表...")
    financial_statements = {
        "annual": {
            "income": df_to_dict(stock.financials, "A-Income"),
            "balance": df_to_dict(stock.balance_sheet, "A-Balance"),
            "cashflow": df_to_dict(stock.cashflow, "A-Cashflow"),
            # SOCIE 對齊官方文件路徑格式
            "socie": safe_api(f"{fmp_v3}/statement-of-changes-in-equity/{ticker}", {"apikey": fmp_key})
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials, "Q-Income"),
            "balance": df_to_dict(stock.quarterly_balance_sheet, "Q-Balance"),
            "cashflow": df_to_dict(stock.quarterly_cashflow, "Q-Cashflow")
        }
    }

    # 2. 價量與預估 (對齊 FMP 官方路徑)
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except: price_list = []
    
    forecasts = {
        "dcf": safe_api(f"{fmp_v3}/discounted-cash-flow/{ticker}", {"apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_v3}/analyst-estimates/{ticker}", {"apikey": fmp_key})
    }

    # 3. FinMind 在地數據 (對齊探針成功參數)
    fm_res = {}
    if is_tw and fm_token:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            # 使用探針證實成功的參數結構，修正 start_date 為 2025
            data = safe_api(fm_url, {
                "dataset": ds, 
                "data_id": ticker, 
                "token": fm_token.strip(), 
                "start_date": "2025-01-01"
            })
            fm_res[ds] = data.get("data", []) if data else []

    # 4. 情報整合與 SGR 運算
    info = stock.info if hasattr(stock, 'info') else {}
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
            "news": stock.news if hasattr(stock, 'news') else [],
            "info_snapshot": info
        }
    }

    # 5. 安全入庫 (標的隔離)
    with open(f"{DATA_DIR}/{ticker}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 終極封包入庫完成")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_ultimate(t, True)
    for t in TARGETS["US"]: harvest_ultimate(t, False)
    log("🏁 全量任務修復完畢")
