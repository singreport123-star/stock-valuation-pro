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
    """環境自癒：確保資料夾存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
        log(f"📁 已建立數據保險箱: {DATA_DIR}")

def json_serial(obj):
    """處理 JSON 序列化衝突 (Timestamp/Date)"""
    if isinstance(obj, (datetime, date, pd.Timestamp)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def df_to_dict(df, name=""):
    """安全轉換 DataFrame 為字典"""
    try:
        if df is None or df.empty:
            return {}
        return json.loads(df.to_json(orient="index", date_format="iso"))
    except Exception as e:
        log(f"❌ {name} 報表轉換失敗: {e}")
        return {}

def safe_api(url, params=None, retries=3):
    """具備重試機制與錯誤診斷的 API 請求"""
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=25)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 402:
                log(f"💡 API 權限限制 (402): {url.split('?')[0]} - 請確認該標的是否支援或是否需付費。")
                return None
            elif r.status_code == 422:
                log(f"❌ API 參數錯誤 (422): {url} - 請檢查 Token 或 Dataset 設定。")
                return None
            log(f"⚠️ API 狀態碼 {r.status_code}: {url.split('apikey=')[0]}")
        except Exception as e:
            log(f"❌ 請求連線失敗 (第 {i+1} 次): {e}")
        time.sleep(2)
    return None

def safe_yf_attr(stock, attr):
    """防禦性獲取 yfinance 屬性"""
    try:
        val = getattr(stock, attr)
        return val() if callable(val) else val
    except Exception as e:
        log(f"⚠️ yfinance 屬性 {attr} 獲取失敗: {e}")
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
# 擷取層 (Crawlers)：旗艦收割機
# =========================
def harvest_extreme(ticker, is_tw=True):
    log(f"🚀 開始旗艦級收割: {ticker}")
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")
    
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol_yf)

    # 1. 四大財報 (對齊官方 Restful 路徑)
    fmp_v3 = "https://financialmodelingprep.com/api/v3"
    log(f"📊 採集 {ticker} 完整年報/季報/權益變動表...")
    financial_statements = {
        "annual": {
            "income": df_to_dict(stock.financials, "Annual-Income"),
            "balance": df_to_dict(stock.balance_sheet, "Annual-Balance"),
            "cashflow": df_to_dict(stock.cashflow, "Annual-Cashflow"),
            "socie": safe_api(f"{fmp_v3}/statement-of-changes-in-equity/{ticker}", {"apikey": fmp_key})
        },
        "quarterly": {
            "income": df_to_dict(stock.quarterly_financials, "Q-Income"),
            "balance": df_to_dict(stock.quarterly_balance_sheet, "Q-Balance"),
            "cashflow": df_to_dict(stock.quarterly_cashflow, "Q-Cashflow")
        }
    }

    # 2. 價量與 FMP 預測
    try:
        hist = stock.history(period="6mo").reset_index()
        price_list = json.loads(hist.to_json(orient="records", date_format="iso"))
    except: price_list = []
    
    forecasts = {
        "dcf": safe_api(f"{fmp_v3}/discounted-cash-flow", {"symbol": ticker, "apikey": fmp_key}),
        "estimates": safe_api(f"{fmp_v3}/analyst-estimates", {"symbol": ticker, "apikey": fmp_key})
    }

    # 3. FinMind 在地化數據 (強化 Token 安全檢查)
    fm_res = {}
    if is_tw and fm_token and len(fm_token.strip()) > 5:
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
        for ds in datasets:
            data = safe_api(fm_url, {"dataset": ds, "data_id": ticker, "token": fm_token.strip(), "start_date": "2024-01-01"})
            fm_res[ds] = data.get("data", []) if data else []
    else:
        log(f"⚠️ 跳過 FinMind: Token 無效或非台股任務")

    # 4. 情報整合與 SGR 運算
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

    # 5. 安全寫入 (標的隔離)
    file_path = f"{DATA_DIR}/{ticker}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=json_serial)
    log(f"✅ {ticker}.json 數據包已完整入庫")

if __name__ == "__main__":
    init_env()
    for t in TARGETS["TW"]: harvest_extreme(t, True)
    for t in TARGETS["US"]: harvest_extreme(t, False)
    log("🏁 旗艦收割任務全量完成")
