import os, requests, json
import yfinance as yf
from datetime import datetime

# --- 美股全量聯集：路由加固版 V8 ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY", "").strip()
BASE_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Union] {msg}")

def fetch_fmp_fixed(endpoint):
    """修正 Legacy Endpoint 報錯：加入 period 參數並檢查路由"""
    if not FMP_KEY: return []
    # 根據官方建議，部分帳戶需明確指定 period
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{TARGET}"
    params = {"apikey": FMP_KEY, "period": "annual", "limit": 5}
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict) and "Error Message" in data:
                log(f"🚨 FMP {endpoint} 邏輯錯誤: {data['Error Message']}")
                return []
            log(f"✅ FMP {endpoint} 成功: {len(data) if isinstance(data, list) else 1} 筆")
            return data
        else:
            log(f"🚨 FMP {endpoint} 失敗: HTTP {r.status_code}")
            return []
    except Exception as e:
        log(f"💥 FMP {endpoint} 異常: {e}")
        return []

def harvest_us_v8():
    log(f"🚀 啟動 {TARGET} 路由修正收割任務...")
    
    # 軌道 A: yfinance (並列)
    yf_payload = {}
    try:
        stock = yf.Ticker(TARGET)
        yf_payload = {"info": stock.info, "news": stock.news}
        log(f"✅ yfinance 軌道完成 (新聞: {len(yf_payload['news'])} 筆)")
    except Exception as e:
        log(f"❌ yfinance 異常: {e}")

    # 軌道 B: FMP (法定財報重攻)
    fmp_payload = {
        "profile": fetch_fmp_fixed("profile"),
        "income": fetch_fmp_fixed("income-statement"),
        "balance": fetch_fmp_fixed("balance-sheet-statement"),
        "cash_flow": fetch_fmp_fixed("cash-flow-statement")
    }

    # 全量合併
    full_output = {
        "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "ver": "V8-Fixed"},
        "fundamental": yf_payload.get("info", {}),
        "financial_statements": fmp_payload,
        "news": yf_payload.get("news", [])
    }

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(full_output, f, ensure_ascii=False, indent=2)
    log(f"🏁 {TARGET} 數據入庫完成。")

if __name__ == "__main__":
    harvest_us_v8()
