import requests
from bs4 import BeautifulSoup
import re

def parse_heavy_data(ticker):
    print(f"=== 執行 {ticker} 深度解析探針 ===")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # 1. Cmoney 專家解析
    cm_url = f"https://www.cmoney.tw/follow/channel/stock-{ticker}?chart=target"
    try:
        res = requests.get(cm_url, headers=headers)
        # 尋找 HTML 中的目標價數值 (通常隱藏在 JavaScript 變數或特定標籤中)
        prices = re.findall(r"\"TargetPrice\":([\d\.]+)", res.text)
        if not prices:
            # 備選：搜尋頁面上的文字標籤
            soup = BeautifulSoup(res.text, 'html.parser')
            text_search = soup.find_all(string=re.compile("目標價"))
            print(f"[Cmoney] 找到關鍵字區塊數: {len(text_search)}")
            if prices: print(f"[Cmoney] 提取到目標價數值: {prices}")
        else:
            print(f"[Cmoney] 成功提取目標價列表: {prices[:3]}")
    except Exception as e:
        print(f"[Cmoney] 解析異常: {e}")

    # 2. MoneyDJ 報告解析
    mdj_url = f"https://www.moneydj.com/KMDJ/Common/ListNewData.aspx?index=1&svc=NW&a=TWS:{ticker}"
    try:
        res = requests.get(mdj_url, headers=headers)
        if "研究報告" in res.text:
            print(f"[MoneyDJ] 確認包含研究報告清單")
        else:
            print(f"[MoneyDJ] 未發現研究報告關鍵字")
    except Exception as e:
        print(f"[MoneyDJ] 解析異常: {e}")

if __name__ == "__main__":
    parse_heavy_data("2330")
