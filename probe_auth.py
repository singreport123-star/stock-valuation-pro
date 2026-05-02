import os
import requests
import json
import concurrent.futures

def fetch_fmp_stable(symbol, endpoint):
    key = os.getenv('FMP_API_KEY')
    url = f"https://financialmodelingprep.com/stable/{endpoint}?symbol={symbol}&apikey={key}"
    try:
        res = requests.get(url)
        return res.json() if res.status_code == 200 else f"Error_{res.status_code}"
    except: return "Conn_Error"

def fetch_finmind_all(ticker):
    token = os.getenv('FINMIND_TOKEN')
    datasets = ["TaiwanStockMonthRevenue", "TaiwanStockInstitutionalInvestorsBuySell", "ConvertibleBondDailyTransaction"]
    results = {}
    for ds in datasets:
        url = "https://api.finmindtrade.com/api/v4/data"
        params = {"dataset": ds, "data_id": ticker, "token": token, "start_date": "2026-04-01"}
        res = requests.get(url, params=params)
        results[ds] = len(res.json().get('data', [])) if res.status_code == 200 else "Error"
    return results

if __name__ == "__main__":
    print("🚀 啟動終極聯集探針 (Stable API 版)...")
    results = {
        "TW_2330": fetch_finmind_all("2330"),
        "US_META_Stable": {
            "profile": fetch_fmp_stable("META", "profile"),
            "dcf": fetch_fmp_stable("META", "discounted-cash-flow"),
            "estimates": fetch_fmp_stable("META", "analyst-estimates")
        }
    }
    print(json.dumps(results, indent=2, ensure_ascii=False))
