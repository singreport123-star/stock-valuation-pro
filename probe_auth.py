import yfinance as yf
import requests
import json
import datetime

def dual_stock_probe(ticker_list):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://invest.cnyes.com/',
        'Accept': 'application/json'
    }

    for ticker in ticker_list:
        print(f"\n{'='*20} 診斷標的: {ticker} {'='*20}")
        
        # 1. 全球專家 (Global)
        yf_ticker = f"{ticker}.TW"
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        print(f"[Global] Yahoo 目標價: {info.get('targetMeanPrice', 'N/A')}")
        print(f"[Global] 分析師人數: {info.get('numberOfAnalystOpinions', 'N/A')}")

        # 2. 在地專家 (Local - Anue 修正版)
        anue_url = f"https://invest.cnyes.com/api/v1/quote/TWS:{ticker}:STOCK/institutionalConsensus"
        try:
            res = requests.get(anue_url, headers=headers, timeout=10)
            if res.status_code == 200:
                local_data = res.json().get('data', {})
                print(f"[Local] Anue 目標價 (中位數): {local_data.get('targetPriceMedium', 'N/A')}")
                print(f"[Local] 本土券商評等數: {local_data.get('count', 'N/A')}")
            else:
                print(f"[Local] Anue 偵測失敗 (Status {res.status_code})")
        except Exception as e:
            print(f"[Local] Anue 連線異常: {e}")

        # 3. 系統邏輯 (Internal - SGR 計算)
        roe = info.get('returnOnEquity')
        payout = info.get('payoutRatio')
        if roe and payout:
            sgr = roe * (1 - payout)
            print(f"[Internal] 系統計算 SGR: {sgr*100:.2f}%")
        else:
            print("[Internal] 數據不足，無法計算 SGR")

if __name__ == "__main__":
    dual_stock_probe(["2330", "4958"])
