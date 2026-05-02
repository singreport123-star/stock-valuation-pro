import yfinance as yf
import requests
import json

def deep_probe():
    print("=== 1. 美股深度偵測 (META) ===")
    meta = yf.Ticker("META")
    info = meta.info
    
    # 選取幾個關鍵預測與分析師欄位
    keys_to_check = [
        'targetMeanPrice', 'recommendationMean', 'numberOfAnalystOpinions',
        'forwardEps', 'forwardPE', 'heldPercentInstitutions', 
        'shortRatio', 'earningsQuarterlyGrowth'
    ]
    
    print("--- 關鍵分析師數據 ---")
    for key in keys_to_check:
        print(f"{key}: {info.get(key, 'N/A')}")
        
    print("\n=== 2. 台股預測接口偵測 (2330) ===")
    # 這是鉅亨網的隱藏 API，我們測試其穩定性
    anue_url = "https://invest.cnyes.com/api/v1/quote/TWS:2330:STOCK/institutionalConsensus"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(anue_url, headers=headers)
    if res.status_code == 200:
        print(f"Anue 連線成功！回傳資料範例: {json.dumps(res.json(), indent=2)[:200]}...")
    else:
        print(f"Anue 連線失敗，狀態碼: {res.status_code}")

if __name__ == "__main__":
    deep_probe()
