import os, requests, json
import yfinance as yf
from datetime import datetime

# --- 美股多源並列聯集收割機 V4 ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY")
BASE_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Union] {msg}")

def fetch_fmp(endpoint, params={}):
    if not FMP_KEY: return []
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{TARGET}"
    params['apikey'] = FMP_KEY
    try:
        r = requests.get(url, params=params, timeout=15)
        log(f"📡 FMP {endpoint}: HTTP {r.status_code}")
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        log(f"💥 FMP {endpoint} 崩潰: {e}")
        return []

def harvest_extreme_union():
    log(f"🚀 啟動 {TARGET} 全量並列聯集任務...")
    
    # --- 軌道 1: yfinance (基礎肉源) ---
    log("🧵 執行 yfinance 軌道...")
    yf_stock = yf.Ticker(TARGET)
    yf_data = {
        "info": yf_stock.info if yf_stock.info else {},
        "yf_news": yf_stock.news if hasattr(yf_stock, 'news') else []
    }
    log(f"✅ yfinance 完成 (新聞: {len(yf_data['yf_news'])} 筆)")

    # --- 軌道 2: FMP (核心深度肉源) ---
    log("🧵 執行 FMP 專業軌道...")
    fmp_union = {
        "estimates": fetch_fmp("analyst-estimates"),        # 分析師預期
        "insider": fetch_fmp("insider-trading"),            # 內部人
        "institutional": fetch_fmp("institutional-holder"), # 13F 機構
        "sec_filings": fetch_fmp("sec_filings"),            # SEC 連結
        "metrics": fetch_fmp("key-metrics-ttm"),            # 深度指標
        "segments": fetch_fmp("revenue-product-segmentation"), # 分段營收
        "fmp_news": fetch_fmp("stock_news", {"limit": 15})   # 專業新聞
    }
    
    # --- 最終聯集 (Merge) ---
    full_payload = {
        "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "source": "Parallel-Union-V4"},
        "fundamental": yf_data["info"],
        "deep_analysis": fmp_union,
        "news_aggregate": {
            "yahoo": yf_data["yf_news"],
            "fmp": fmp_union["fmp_news"]
        }
    }

    # 存檔
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False, indent=2)
    
    log(f"🏁 {TARGET} 全量聯集入庫成功。")

if __name__ == "__main__":
    harvest_extreme_union()
