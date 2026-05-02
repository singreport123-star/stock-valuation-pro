import os, requests, json
import yfinance as yf
from datetime import datetime

# --- 美股 FMP 專業對標版 V6 ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY")
BASE_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-FMP] {msg}")

def fetch_fmp_statement(statement_type, limit=5):
    """對齊 FMP 官網文檔: income-statement, balance-sheet-statement, cash-flow-statement"""
    if not FMP_KEY: return []
    url = f"https://financialmodelingprep.com/api/v3/{statement_type}/{TARGET}"
    params = {"apikey": FMP_KEY, "limit": limit}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            log(f"✅ {statement_type} 擷取成功: {len(data)} 筆")
            return data
        else:
            log(f"⚠️ {statement_type} 失敗: HTTP {r.status_code}")
            return []
    except Exception as e:
        log(f"💥 {statement_type} 崩潰: {e}")
        return []

def harvest_us_v6():
    log(f"🚀 啟動 {TARGET} FMP 官方規格採集...")

    # --- 軌道 1: yfinance (移除 Session 避免報錯) ---
    log("🧵 執行 yfinance 基礎軌道...")
    try:
        yf_stock = yf.Ticker(TARGET)
        yf_info = yf_stock.info
    except:
        yf_info = {}

    # --- 軌道 2: FMP (三大報表全量聯集) ---
    log("🧵 執行 FMP 財務數據軌道...")
    statements = {
        "income": fetch_fmp_statement("income-statement"),
        "balance": fetch_fmp_statement("balance-sheet-statement"),
        "cash_flow": fetch_fmp_statement("cash-flow-statement")
    }

    # 合併聯集
    payload = {
        "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "ver": "V6-FMP-Standard"},
        "profile": fetch_fmp_statement("profile"),
        "financial_statements": statements,
        "fundamental_summary": yf_info
    }

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    log(f"🏁 {TARGET} 官方規格採集完成，數據已入庫。")

if __name__ == "__main__":
    harvest_us_v6()
