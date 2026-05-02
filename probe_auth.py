import os
import requests
import json

def fetch_calibrated_union(token_fm, key_fmp):
    results = {}
    
    # 1. 修復 FMP Estimates (加入 period 參數)
    fmp_url = f"https://financialmodelingprep.com/stable/analyst-estimates?symbol=META&period=annual&apikey={key_fmp}"
    res_fmp = requests.get(fmp_url)
    results["US_META_Estimates"] = res_fmp.json()[:3] if res_fmp.status_code == 200 else f"Error_{res_fmp.status_code}"

    # 2. 驗證台股 CB (使用 4958 測試，2330 無 CB 是正常的)
    fm_url = "https://api.finmindtrade.com/api/v4/data"
    fm_params = {
        "dataset": "ConvertibleBondDailyTransaction",
        "data_id": "4958", # 臻鼎-KY 有可轉債
        "token": token_fm,
        "start_date": "2026-04-01"
    }
    res_fm = requests.get(fm_url, params=fm_params)
    results["TW_4958_CB"] = len(res_fm.json().get('data', []))

    return results

if __name__ == "__main__":
    fm_token = os.getenv('FINMIND_TOKEN')
    fmp_key = os.getenv('FMP_API_KEY')
    print("🚀 執行最後校準：美股預期修復 & 台股 CB 鏈路驗證...")
    print(json.dumps(fetch_calibrated_union(fm_token, fmp_key), indent=2, ensure_ascii=False))
