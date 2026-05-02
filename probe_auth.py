import requests
import pandas as pd

def local_expert_probe(ticker):
    print(f"\n=== 偵測在地專家: {ticker} ===")
    
    # 探針 A: Fugle (富果) 公開法人共識接口
    fugle_url = f"https://api.fugle.tw/marketdata/v1.0/stock/intraday/quote/{ticker}"
    # 備註：Fugle 有時需要特殊的公鑰，我們先測基礎響應
    
    # 探針 B: Cmoney 法人目標價網頁 (模擬網頁解析)
    cmoney_url = f"https://www.cmoney.tw/follow/channel/stock-{ticker}?chart=target"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        # Cmoney 測試
        res_cm = requests.get(cmoney_url, headers=headers, timeout=10)
        print(f"[Cmoney] 網頁響應狀態: {res_cm.status_code}")
        if "目標價" in res_cm.text:
            print(f"[Cmoney] 成功！在頁面中偵測到關鍵字『目標價』")
        else:
            print(f"[Cmoney] 警告：頁面未包含目標價關鍵字，可能需進階解析")
            
        # Yahoo 台灣版測試 (在地專家的另一種解法)
        y_tw_url = f"https://tw.stock.yahoo.com/quote/{ticker}.TW"
        res_ytw = requests.get(y_tw_url, headers=headers)
        print(f"[Yahoo_TW] 響應狀態: {res_ytw.status_code}")

    except Exception as e:
        print(f"探針異常: {e}")

if __name__ == "__main__":
    for t in ["2330", "4958"]:
        local_expert_probe(t)
