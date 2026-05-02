import os, requests, json
import yfinance as yf
from datetime import datetime

# --- 美股權限修復與混合同步版 V5 ---
TARGET = "META"
FMP_KEY = os.getenv("FMP_API_KEY")
BASE_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Fix] {msg}")

def fetch_fmp_safe(endpoint):
    """測試 FMP 免費版支援的基礎接口"""
    if not FMP_KEY: return []
    # 注意：免費版通常只支援基礎財務報表
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{TARGET}"
    try:
        r = requests.get(url, params={"apikey": FMP_KEY}, timeout=15)
        if r.status_code == 403:
            log(f"⚠️ FMP {endpoint} 被拒絕 (403): 權限不足，略過。")
            return []
        return r.json() if r.status_code == 200 else []
    except: return []

def harvest_us_v5():
    log(f"🚀 啟動 {TARGET} 權限修復採集...")

    # --- 軌道 1: yfinance (強化 Headers 繞過) ---
    log("🧵 執行 yfinance 強化軌道...")
    # 使用自定義 Session 繞過 GitHub IP 限制嘗試
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})
    yf_stock = yf.Ticker(TARGET, session=session)
    
    try:
        yf_info = yf_stock.info
        yf_news = yf_stock.news
    except:
        yf_info, yf_news = {}, []

    # --- 軌道 2: FMP (鎖定免費版可用接口) ---
    log("🧵 執行 FMP 基礎軌道...")
    fmp_data = {
        "profile": fetch_fmp_safe("profile"),
        "income_statement": fetch_fmp_safe("income-statement"), # 免費版核心
        "enterprise_value": fetch_fmp_safe("enterprise-value")
    }

    # 合併聯集
    payload = {
        "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "ver": "V5-Fix"},
        "fundamental": yf_info if yf_info else (fmp_data["profile"][0] if fmp_data["profile"] else {}),
        "financial_history": fmp_data["income_statement"],
        "news_aggregate": yf_news if yf_news else []
    }

    os.makedirs(BASE_DIR, exist_ok=True)
    with open(f"{BASE_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    
    log(f"🏁 {TARGET} 採集完成。FMP 報表筆數: {len(fmp_data['income_statement'])}")

if __name__ == "__main__":
    harvest_us_v5()
