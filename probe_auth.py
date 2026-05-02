import os
import yfinance as yf
import requests
import re
import json
import concurrent.futures
from datetime import datetime

# 全量聯集標的
TARGET_TW = ["2330", "4958"]
TARGET_US = ["META"]

def fetch_finmind(ticker, dataset, token):
    url = "https://api.finmindtrade.com/api/v4/data"
    # 修正 CB 可能產生的 422 錯誤：精確指定日期範圍
    params = {"dataset": dataset, "data_id": ticker, "token": token, "start_date": "2026-04-01"}
    try:
        res = requests.get(url, params=params, timeout=10)
        return res.json().get('data', [])
    except: return []

def fetch_fmp(ticker, endpoint, key):
    # 嘗試解決 403：模擬瀏覽器標頭
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = f"https://financialmodelingprep.com/api/v3/{endpoint}/{ticker}?apikey={key}"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else f"Error_{res.status_code}"
    except: return "Conn_Error"

def fetch_news(ticker):
    """聯集擴充：抓取 Yahoo News 摘要"""
    stock = yf.Ticker(ticker)
    return stock.news[:3] # 取前三則

def probe_all_in_one(ticker, is_tw=True):
    print(f"🚀 開始全量掃描: {ticker}...")
    fm_token = os.getenv('FINMIND_TOKEN')
    fmp_key = os.getenv('FMP_API_KEY')
    
    results = {"ticker": ticker, "timestamp": datetime.now().isoformat()}

    # 1. 核心底盤 (yfinance + SGR Logic)
    symbol = f"{ticker}.TW" if is_tw else ticker
    yf_stock = yf.Ticker(symbol)
    info = yf_stock.info
    results["base_expert"] = {
        "global_target": info.get('targetMeanPrice'),
        "analyst_count": info.get('numberOfAnalystOpinions')
    }
    
    # 2. 官方事實 (FinMind - 聯集)
    if is_tw:
        results["official_facts"] = {
            "revenue": fetch_finmind(ticker, "TaiwanStockMonthRevenue", fm_token),
            "chip": fetch_finmind(ticker, "TaiwanStockInstitutionalInvestorsBuySell", fm_token),
            "cb_derivative": fetch_finmind(ticker, "ConvertibleBondDailyTransaction", fm_token)
        }
        # 在地專家解析 (Cmoney/MoneyDJ)
        headers = {'User-Agent': 'Mozilla/5.0'}
        cm_url = f"https://www.cmoney.tw/follow/channel/stock-{ticker}?chart=target"
        cm_res = requests.get(cm_url, headers=headers)
        results["local_expert"] = {
            "cm_targets": re.findall(r"\"TargetPrice\":([\d\.]+)", cm_res.text)[:3],
            "mdj_ready": "研究報告" in requests.get(f"https://www.moneydj.com/KMDJ/Common/ListNewData.aspx?index=1&svc=NW&a=TWS:{ticker}", headers=headers).text
        }

    # 3. 美股預測與事實 (FMP - 聯集)
    if not is_tw or ticker == "2330": # 2330 亦可測 FMP
        results["fmp_forecast"] = {
            "dcf": fetch_fmp(ticker, "discounted-cash-flow", fmp_key),
            "estimates": fetch_fmp(ticker, "analyst-estimates", fmp_key)
        }

    # 4. 新聞聯集
    results["news_feed"] = fetch_news(symbol)

    return results

if __name__ == "__main__":
    final_output = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(probe_all_in_one, t, (t != "META")): t for t in TARGET_TW + TARGET_US}
        for f in concurrent.futures.as_completed(futures):
            res = f.result()
            final_output[res['ticker']] = res
    
    print("\n" + "🔥" * 10 + " 聯集整合數據報告 " + "🔥" * 10)
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
