import os
import requests

def probe():
    fmp_key = os.getenv("FMP_API_KEY")
    fm_token = os.getenv("FINMIND_TOKEN")

    print(f"--- 環境變數診斷 ---")
    print(f"FMP Key 是否存在: {'✅ Yes' if fmp_key else '❌ No'}")
    print(f"FinMind Token 是否存在: {'✅ Yes' if fm_token else '❌ No'}")
    if fmp_key: print(f"FMP Key 長度: {len(fmp_key)}")
    if fm_token: print(f"FinMind Token 長度: {len(fm_token)}")

    # 1. 探測 FMP 最基礎端點 (Profile 通常是免費權限)
    print(f"\n--- FMP 探針 (META) ---")
    fmp_url = f"https://financialmodelingprep.com/api/v3/profile/META?apikey={fmp_key}"
    r_fmp = requests.get(fmp_url)
    print(f"Status: {r_fmp.status_code}")
    print(f"Response Snapshot: {r_fmp.text[:100]}")

    # 2. 探測 FinMind 基礎端點
    if fm_token:
        print(f"\n--- FinMind 探針 (2330) ---")
        fm_url = "https://api.finmindtrade.com/api/v4/data"
        params = {
            "dataset": "TaiwanStockMonthRevenue",
            "data_id": "2330",
            "token": fm_token,
            "start_date": "2026-01-01"
        }
        r_fm = requests.get(fm_url, params=params)
        print(f"Status: {r_fm.status_code}")
        print(f"Response Snapshot: {r_fm.text[:200]}")

if __name__ == "__main__":
    probe()
