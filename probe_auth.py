import requests
import os

key = os.getenv('FMP_API_KEY')
# 測試 v4 新版 DCF 與 v3 的關鍵指標 (通常比 profile 穩定)
test_endpoints = [
    f"https://financialmodelingprep.com/api/v4/advanced_discounted_cash_flow?symbol=META&apikey={key}",
    f"https://financialmodelingprep.com/api/v3/key-metrics/META?limit=1&apikey={key}",
    f"https://financialmodelingprep.com/api/v3/analyst-estimates/META?apikey={key}"
]

print("🚀 FMP 路徑校準測試啟動...")
for url in test_endpoints:
    res = requests.get(url)
    # 隱藏 API Key 顯示
    clean_url = url.split('?')[0]
    print(f"\nURL: {clean_url}")
    print(f"Status: {res.status_code}")
    # 若 200 則顯示內容，否則顯示原始 Error
    if res.status_code == 200:
        print(f"Success: 抓取到 {len(res.text)} bytes 數據")
    else:
        print(f"Error Response: {res.text}")
