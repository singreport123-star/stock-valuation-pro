import os
import requests
import datetime

def diagnostic_run():
    fmp_key = os.getenv('FMP_API_KEY')
    finmind_token = os.getenv('FINMIND_TOKEN')

    print("=== 診斷 A: FMP 權限測試 ===")
    # 測試基礎 Quote 接口 (免費版權限)
    fmp_url = f"https://financialmodelingprep.com/api/v3/quote/META?apikey={fmp_key}"
    res_fmp = requests.get(fmp_url)
    print(f"FMP Status: {res_fmp.status_code}")
    if res_fmp.status_code == 200:
        print(f"FMP Key 存活，回傳內容: {res_fmp.json()[0]['name']}")
    else:
        print(f"FMP 報錯訊息: {res_fmp.text}")

    print("\n=== 診斷 B: FinMind 參數測試 ===")
    # 根據截圖要求，加入 start_date 參數，並指定台股總覽數據
    fm_url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockMonthRevenue",
        "data_id": "2330",
        "start_date": (datetime.datetime.now() - datetime.timedelta(days=60)).strftime('%Y-%m-%d'),
        "token": finmind_token
    }
    res_fm = requests.get(fm_url, params=params)
    print(f"FinMind Status: {res_fm.status_code}")
    if res_fm.status_code == 200:
        data_len = len(res_fm.json().get('data', []))
        print(f"FinMind 連線成功，抓到 {data_len} 筆月營收數據。")
    else:
        print(f"FinMind 報錯訊息: {res_fm.text}")

if __name__ == "__main__":
    diagnostic_run()
