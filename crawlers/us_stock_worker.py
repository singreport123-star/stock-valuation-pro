import os, requests, json
import yfinance as yf
from datetime import datetime

# --- 美股全量並列聯集收割機 (不容縮水版) ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY", "").strip()
BASE_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Union] {msg}")

def harvest_us_full():
    log(f"🚀 啟動 {TARGET} 全量並列收割任務...")
    
    # 診斷：檢查 Key 物理長度 (嚴防 Secret 設定錯誤)
    log(f"🔑 API Key 檢查: 長度為 {len(FMP_KEY)}, 前兩位為 {FMP_KEY[:2] if FMP_KEY else '??'}")

    # --- 軌道 1: yfinance (基礎與新聞) ---
    log("🧵 軌道 A: yfinance 啟動...")
    yf_data = {}
    try:
        stock = yf.Ticker(TARGET)
        yf_data = {
            "info": stock.info,
            "news": stock.news
        }
        log(f"✅ yfinance 取得成功 (新聞 {len(yf_data['news'])} 筆)")
    except Exception as e:
        log(f"❌ yfinance 軌道崩潰: {e}")

    # --- 軌道 2: FMP (法定財務資料 - 官網規格) ---
    log("🧵 軌道 B: FMP 專業數據啟動...")
    fmp_payload = {}
    endpoints = {
        "profile": "profile",
        "income": "income-statement",
        "balance": "balance-sheet-statement",
        "cash_flow": "cash-flow-statement"
    }
    
    for key, api_path in endpoints.items():
        url = f"https://financialmodelingprep.com/api/v3/{api_path}/{TARGET}"
        try:
            r = requests.get(url, params={"apikey": FMP_KEY}, timeout=15)
            if r.status_code == 200:
                fmp_payload[key] = r.json()
                log(f"✅ FMP {key} 成功: {len(fmp_payload[key])} 筆")
            else:
                log(f"🚨 FMP {key} 警告: HTTP {r.status_code} | 回傳: {r.text[:50]}")
        except Exception as e:
            log(f"💥 FMP {key} 連線異常: {e}")

    # --- 強行聯集 (Union) ---
    final_output = {
        "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "source": "Ultimate-Union-V7"},
        "fundamental": yf_data.get("info", {}),
        "financial_statements": fmp_payload,
        "news": yf_data.get("news", [])
    }

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    
    log(f"🏁 {TARGET} 全量入庫完成。")

if __name__ == "__main__":
    harvest_us_full()
