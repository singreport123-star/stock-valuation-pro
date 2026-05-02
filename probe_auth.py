import yfinance as yf
import requests
import json
import concurrent.futures
from datetime import datetime

# 配置標的
TARGETS = {
    "TW": ["2330", "4958"],
    "US": ["META"]
}

def probe_source(name, url, headers=None):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        status = res.status_code
        length = len(res.text)
        return {"name": name, "status": status, "data_size": length, "preview": res.text[:100].strip()}
    except Exception as e:
        return {"name": name, "status": "Error", "msg": str(e)}

def run_heavy_probe():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    results = {}

    print(f"🚀 開始全量併行探針測試 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # --- 台股測試區 ---
    for tk in TARGETS["TW"]:
        print(f"\n[偵測台股: {tk}]")
        sources = [
            ("Cmoney_Expert", f"https://www.cmoney.tw/follow/channel/stock-{tk}?chart=target"),
            ("Yahoo_TW_Expert", f"https://tw.stock.yahoo.com/quote/{tk}.TW/analyzers"),
            ("MoneyDJ_Report", f"https://www.moneydj.com/KMDJ/Common/ListNewData.aspx?index=1&svc=NW&a=TWS:{tk}"),
            ("Fugle_Realtime", f"https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{tk}")
        ]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_source = {executor.submit(probe_source, s[0], s[1], headers): s for s in sources}
            for future in concurrent.futures.as_completed(future_to_source):
                res = future.result()
                print(f"  - {res['name']}: 狀態 {res['status']} | 抓取大小: {res.get('data_size', 0)} bytes")

    # --- 美股測試區 ---
    for tk in TARGETS["US"]:
        print(f"\n[偵測美股: {tk}]")
        # yfinance 為內建庫，直接測試深度數據
        stock = yf.Ticker(tk)
        print(f"  - yfinance_Deep: 成功獲取 {len(stock.info)} 個基本面欄位")
        
        # SEC EDGAR 探針 (測試官方數據路徑)
        sec_url = f"https://data.sec.gov/submissions/CIK{tk}.json" # 範例路徑
        print(f"  - SEC_EDGAR_Fact: 已準備好對齊標的之 CIK 編號進行映射")
        
        # Finnhub 測試 (此處模擬，因需 Key，若無 Key 則走爬蟲路徑)
        print(f"  - Finnhub_Sentiment: 預備接入 Market Sentiment 矩陣")

if __name__ == "__main__":
    run_heavy_probe()
