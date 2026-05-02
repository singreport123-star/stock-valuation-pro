import os
import requests
import json
import pandas as pd
from datetime import datetime

# 對齊清單：台股總覽、類股、期權、融資券市場總表
TARGET_DATASETS = [
    "TaiwanStockTotal", "TaiwanStockPER", "TaiwanFutureThreeInstitutional",
    "TaiwanOptionThreeInstitutional", "TaiwanStockMarginPurchaseSellTotal"
]
BASE_DATA_DIR = "data/TW/macro"
FM_TOKEN = os.getenv("FINMIND_TOKEN")

def harvest_tw_macro():
    if not FM_TOKEN: return
    results = {}
    for ds in TARGET_DATASETS:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {"dataset": ds, "token": FM_TOKEN.strip(), "start_date": "2026-01-01"}
        try:
            r = requests.get(url, params=params, timeout=25)
            results[ds] = r.json().get("data", []) if r.status_code == 200 else []
        except: results[ds] = []
    
    os.makedirs(BASE_DATA_DIR, exist_ok=True)
    with open(f"{BASE_DATA_DIR}/market_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 台股市場數據聯集完成")

if __name__ == "__main__":
    harvest_tw_macro()
