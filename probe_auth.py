import yfinance as yf
import requests
import pandas as pd

def global_vision_probe():
    ticker_tw = "2330.TW"
    print(f"=== 1. 偵測 Yahoo 國際版對台股 ({ticker_tw}) 的預測欄位 ===")
    stock = yf.Ticker(ticker_tw)
    info = stock.info
    
    # 測試國際財經站對台股的分析師覆蓋
    predictive_keys = ['targetMeanPrice', 'numberOfAnalystOpinions', 'recommendationKey']
    for key in predictive_keys:
        print(f"{key}: {info.get(key, 'N/A')}")

    print(f"\n=== 2. 偵測 SGR 模型數據 (自研預算路徑) ===")
    # 嘗試從 Yahoo 抓取計算 SGR 所需的基本面
    # SGR = ROE * (1 - Payout_Ratio)
    roe = info.get('returnOnEquity', 'N/A')
    payout = info.get('payoutRatio', 'N/A')
    
    if roe != 'N/A' and payout != 'N/A':
        sgr = roe * (1 - payout)
        print(f"成功取得財務數據！系統預算可持續成長率 (SGR): {sgr*100:.2f}%")
    else:
        print("無法從 Yahoo 取得 ROE/Payout，將需從 FinMind 歷史財報二次抓取。")

if __name__ == "__main__":
    global_vision_probe()
