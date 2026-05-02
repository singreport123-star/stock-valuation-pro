import requests
import os

key = os.getenv('FMP_API_KEY')
# 測試一個最基礎的 Endpoint (Profile) 與 一個進階的 (DCF)
test_urls = [
    f"https://financialmodelingprep.com/api/v3/profile/META?apikey={key}",
    f"https://financialmodelingprep.com/api/v3/discounted-cash-flow/META?apikey={key}"
]

for url in test_urls:
    res = requests.get(url)
    print(f"URL: {url.split('?')[0]}")
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text[:100]}") # 只看前100字
