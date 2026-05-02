import os
import requests
import json

def omni_union_probe(ticker_tw, ticker_us):
    fm_token = os.getenv('FINMIND_TOKEN')
    fmp_key = os.getenv('FMP_API_KEY')
    
    # 1. FinMind 聯集測試 (台股 2330 / 4958)
    print(f"--- 執行 FinMind 聯集探針 ({ticker_tw}) ---")
    datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
    for ds in datasets:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {"dataset": ds, "data_id": ticker_tw, "token": fm_token, "start_date": "2026-03-01"}
        res = requests.get(url, params=params)
        print(f"[{ds}] 狀態: {res.status_code} | 資料量: {len(res.json().get('data', []))}")

    # 2. FMP 聯集測試 (美股 META)
    print(f"\n--- 執行 FMP 聯集探針 ({ticker_us}) ---")
    # 測試 DCF 與 分析師預期
    fmp_endpoints = [f"discounted-cash-flow/{ticker_us}", f"analyst-estimates/{ticker_us}"]
    for ep in fmp_endpoints:
        url = f"https://financialmodelingprep.com/api/v3/{ep}?apikey={fmp_key}"
        res = requests.get(url)
        print(f"[{ep}] 狀態: {res.status_code} | 資料量: {len(res.json()) if isinstance(res.json(), list) else '1'}")

if __name__ == "__main__":
    omni_union_probe("2330", "META")
