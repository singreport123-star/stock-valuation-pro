import os, requests, json
from datetime import datetime

# --- 美股極限聯集收割機 V3 (FMP 重點強化) ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY")
BASE_DIR = "data/US/stocks"

def fetch_fmp(endpoint, params={}):
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{TARGET}"
    params['apikey'] = FMP_KEY
    try:
        r = requests.get(url, params=params, timeout=15)
        return r.json() if r.status_code == 200 else []
    except: return []

def extreme_harvest():
    print(f"🚀 啟動 META 極限聯集收割 (FMP API)...")
    
    # 執行 8 大維度聯集
    union_data = {
        "profile": fetch_fmp("profile"),                    # 基礎資訊
        "estimates": fetch_fmp("analyst-estimates"),        # 分析師預期 (關鍵缺失)
        "insider": fetch_fmp("insider-trading"),            # 內部人交易 (解決 None 問題)
        "institutional": fetch_fmp("institutional-holder"), # 機構持倉 13F
        "sec_filings": fetch_fmp("sec_filings"),            # SEC 原始文件連結
        "rating": fetch_fmp("rating"),                      # 綜合技術/基本評分
        "metrics": fetch_fmp("key-metrics-ttm"),            # 關鍵指標 (P/E, P/S 深度版)
        "news": fetch_fmp("stock_news", {"limit": 10})      # 專業新聞水源 (解決 yfinance 封鎖)
    }

    # 數據檢查探針
    for key, val in union_data.items():
        print(f"📊 維度 [{key}]: 取得 {len(val) if isinstance(val, list) else '1'} 筆資料")

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(union_data, f, ensure_ascii=False, indent=2)
    print(f"✅ META 極限聯集數據已入庫")

if __name__ == "__main__":
    if not FMP_KEY:
        print("❌ 錯誤：未偵測到 FMP_API_KEY，請檢查 GitHub Secrets")
    else:
        extreme_harvest()
