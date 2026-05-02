import yfinance as yf
import requests
import json

def final_probe_with_fix():
    print("=== 1. 美股深度確認 (META) - 資料量已達標 ===")
    meta = yf.Ticker("META")
    print(f"確認：機構持倉 {meta.info.get('heldPercentInstitutions')*100:.2f}%")

    print("\n=== 2. 台股預測接口 (2330) - 增加標頭修復測試 ===")
    anue_url = "https://invest.cnyes.com/api/v1/quote/TWS:2330:STOCK/institutionalConsensus"
    
    # 模擬更真實的瀏覽器行為，避開 500 錯誤
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://invest.cnyes.com/twstock/TWS/2330',
        'Origin': 'https://invest.cnyes.com'
    }
    
    try:
        res = requests.get(anue_url, headers=headers, timeout=10)
        print(f"Anue 狀態碼: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"成功抓取！目標價中位數: {data.get('data', {}).get('targetPriceMedium', 'N/A')}")
        else:
            print(f"失敗訊息: {res.text[:100]}")
    except Exception as e:
        print(f"連線異常: {e}")

if __name__ == "__main__":
    final_probe_with_fix()
