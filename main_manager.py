import os
import yfinance as yf
import requests
import json
from datetime import datetime

# --- 目標清單 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def safe_get_json(url):
    """防彈級 API 請求函數"""
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"⚠️ API 警告: 狀態碼 {response.status_code} | URL: {url.split('apikey=')[0]}")
            return None
        return response.json()
    except Exception as e:
        print(f"❌ API 失敗: {str(e)}")
        return None

def run_harvester(ticker, is_tw=True):
    print(f"🚀 啟動全量聯集採集：{ticker}...")
    fm_token = os.getenv('FINMIND_TOKEN')
    fmp_key = os.getenv('FMP_API_KEY')
    
    # 修正 FMP 查詢代號：台股可能需要 .TW 後綴 (依 API 需求調整)
    fmp_ticker = f"{ticker}.TW" if is_tw else ticker
    symbol_yf = f"{ticker}.TW" if is_tw else ticker
    
    # 1. 抓取 yfinance (新聞 + 基礎)
    stock = yf.Ticker(symbol_yf)
    
    # 2. 抓取 FMP Stable (使用防彈函數)
    fmp_url = "https://financialmodelingprep.com/stable"
    dcf = safe_get_json(f"{fmp_url}/discounted-cash-flow?symbol={fmp_ticker}&apikey={fmp_key}")
    est = safe_get_json(f"{fmp_url}/analyst-estimates?symbol={fmp_ticker}&period=annual&apikey={fmp_key}")

    # 3. 封裝數據 (聯集不刪減)
    payload = {
        "metadata": {
            "ticker": ticker, 
            "is_tw": is_tw,
            "update_time": datetime.now().isoformat()
        },
        "valuation": {
            "fmp_dcf": dcf, 
            "fmp_estimates": est, 
            "yf_target": stock.info.get('targetMeanPrice')
        },
        "news": stock.news,
        "raw_info": stock.info
    }
    
    # 4. 寫入檔案 (標的隔離)
    file_path = os.path.join(DATA_DIR, f"{ticker}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✅ {ticker}.json 儲存完畢")

if __name__ == "__main__":
    for t in TARGETS["TW"]: run_harvester(t, True)
    for t in TARGETS["US"]: run_harvester(t, False)
