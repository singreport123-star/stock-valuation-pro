import os
import yfinance as yf
import requests
import pandas as pd

def run_probe():
    # 取得金鑰 (由 GitHub Secrets 注入)
    fmp_key = os.getenv('FMP_API_KEY')
    finmind_token = os.getenv('FINMIND_TOKEN')

    print("=== 1. yfinance 探針 (價量) ===")
    for ticker in ["2330.TW", "META"]:
        price = yf.Ticker(ticker).fast_info['last_price']
        print(f"[{ticker}] 即時股價: {price}")

    print("\n=== 2. FMP 探針 (美股預測) ===")
    if fmp_key:
        url = f"https://financialmodelingprep.com/api/v3/analyst-estimates/META?apikey={fmp_key}"
        res = requests.get(url)
        if res.status_code == 200:
            print(f"[META] FMP 連線成功，取得數據長度: {len(res.json())}")
        else:
            print(f"[META] FMP 連線失敗，狀態碼: {res.status_code}")
    else:
        print("Error: 找不到 FMP_API_KEY")

    print("\n=== 3. FinMind 探針 (台股衛星) ===")
    if finmind_token:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": "TaiwanStockMonthRevenue",
            "data_id": "2330",
            "token": finmind_token
        }
        res = requests.get(url, params=params)
        if res.status_code == 200:
            print(f"[2330] FinMind 連線成功，取得數據筆數: {len(res.json().get('data', []))}")
        else:
            print(f"[2330] FinMind 連線失敗，狀態碼: {res.status_code}")
    else:
        print("Error: 找不到 FINMIND_TOKEN")

if __name__ == "__main__":
    run_probe()
