import os
import yfinance as yf
import requests
import json
from datetime import datetime

# 對齊清單：匯率、利率、油、金、美債
# 匯率採集：USDTWD=X (台幣), EURUSD=X 等
MACRO_SYMBOLS = {
    "Rates": "^IRX", "Gold": "GC=F", "Oil": "CL=F", 
    "T-Bond_10Y": "^TNX", "USD_TWD": "TWD=X"
}
BASE_DATA_DIR = "data/US/macro"
FM_TOKEN = os.getenv("FINMIND_TOKEN")

def harvest_us_macro():
    macro_data = {}
    # 1. yfinance 總經數據
    for name, sym in MACRO_SYMBOLS.items():
        ticker = yf.Ticker(sym)
        hist = ticker.history(period="5d")
        macro_data[name] = json.loads(hist.to_json(orient="index")) if not hist.empty else {}
    
    # 2. FinMind 補充：12國利率、匯率全量 (如有 token)
    if FM_TOKEN:
        url = "https://api.finmindtrade.com/api/v4/data"
        for ds in ["InterestRate", "TaiwanExchangeRate"]:
            params = {"dataset": ds, "token": FM_TOKEN.strip(), "start_date": "2026-01-01"}
            r = requests.get(url, params=params, timeout=25)
            macro_data[ds] = r.json().get("data", []) if r.status_code == 200 else []

    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    with open(f"{BASE_DATA_DIR}/macro_indicators.json", "w", encoding="utf-8") as f:
        json.dump(macro_data, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 全球總經數據聯集完成")

if __name__ == "__main__":
    harvest_us_macro()
