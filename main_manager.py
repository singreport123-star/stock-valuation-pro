import os
import yfinance as yf
import requests
import json
from datetime import datetime

# --- 目標清單 ---
TARGETS = {"TW": ["2330", "4958"], "US": ["META"]}
DATA_DIR = "data"

def run_harvester(ticker, is_tw=True):
    print(f"🚀 啟動全量聯集採集：{ticker}...")
    fm_token = os.getenv('FINMIND_TOKEN')
    fmp_key = os.getenv('FMP_API_KEY')
    symbol = f"{ticker}.TW" if is_tw else ticker
    
    # 1. 抓取 yfinance (新聞 + 基礎)
    stock = yf.Ticker(symbol)
    
    # 2. 抓取 FMP Stable
    fmp_url = f"https://financialmodelingprep.com/stable"
    dcf = requests.get(f"{fmp_url}/discounted-cash-flow?symbol={ticker}&apikey={fmp_key}").json()
    est = requests.get(f"{fmp_url}/analyst-estimates?symbol={ticker}&period=annual&apikey={fmp_key}").json()

    # 3. 封裝數據
    payload = {
        "metadata": {"ticker": ticker, "update_time": datetime.now().isoformat()},
        "valuation": {"fmp_dcf": dcf, "fmp_estimates": est, "yf_target": stock.info.get('targetMeanPrice')},
        "news": stock.news,
        "raw_info": stock.info
    }
    
    # 4. 寫入檔案
    file_path = os.path.join(DATA_DIR, f"{ticker}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"✅ {ticker}.json 儲存完畢 (路徑: {file_path})")

if __name__ == "__main__":
    for t in TARGETS["TW"]: run_harvester(t, True)
    for t in TARGETS["US"]: run_harvester(t, False)
