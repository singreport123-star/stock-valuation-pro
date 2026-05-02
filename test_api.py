import os
import requests
import yfinance as yf

def log(msg):
    print(msg)

# =========================
# 1️⃣ 測試 FinMind
# =========================
def test_finmind():
    print("\n===== 測試 FinMind =====")

    token = os.getenv("FINMIND_TOKEN")
    print(f"Token: {token}")

    if not token:
        print("❌ FINMIND_TOKEN 沒有設定")
        return

    url = "https://api.finmindtrade.com/api/v4/data"
    params = {
        "dataset": "TaiwanStockMonthRevenue",
        "data_id": "2330",
        "token": token.strip()
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        print("Status:", r.status_code)

        try:
            data = r.json()
            print("Keys:", data.keys())

            if "data" in data:
                print(f"✅ 成功，筆數: {len(data['data'])}")
            else:
                print("⚠️ 回傳沒有 data:", data)

        except Exception as e:
            print("❌ JSON解析失敗:", e)

    except Exception as e:
        print("❌ 請求失敗:", e)


# =========================
# 2️⃣ 測試 FMP
# =========================
def test_fmp():
    print("\n===== 測試 FMP =====")

    key = os.getenv("FMP_API_KEY")
    print(f"API KEY: {key}")

    if not key:
        print("❌ FMP_API_KEY 沒有設定")
        return

    url = "https://financialmodelingprep.com/api/v3/profile/AAPL"

    try:
        r = requests.get(url, params={"apikey": key}, timeout=15)
        print("Status:", r.status_code)

        if r.status_code == 200:
            print("✅ FMP 正常")
        else:
            print("❌ FMP 失敗:", r.text)

    except Exception as e:
        print("❌ 請求失敗:", e)


# =========================
# 3️⃣ 測試 yfinance
# =========================
def test_yfinance():
    print("\n===== 測試 yfinance =====")

    try:
        stock = yf.Ticker("2330.TW")

        # 測價格
        hist = stock.history(period="5d")
        print(f"價格筆數: {len(hist)}")

        # 測 info
        try:
            info = stock.info
            print("info OK")
        except:
            print("⚠️ info 失敗")

        # 測 news
        try:
            news = stock.news
            print(f"news OK ({len(news)})")
        except:
            print("⚠️ news 失敗")

    except Exception as e:
        print("❌ yfinance 爆掉:", e)


# =========================
# 主程式
# =========================
if __name__ == "__main__":
    test_finmind()
    test_fmp()
    test_yfinance()
