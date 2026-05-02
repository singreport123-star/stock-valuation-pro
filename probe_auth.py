import os
import yfinance as yf
import requests
import re
import json
import concurrent.futures
from datetime import datetime

# 目標清單
STOCKS_TW = ["2330", "4958"]
STOCKS_US = ["META"]

def get_finmind_data(ticker, token):
    """取得台股月營收 (驗證 API Token 活性)"""
    url = "https://api.finmindtrade.com/api/v4/data"
    params = {"dataset": "TaiwanStockMonthRevenue", "data_id": ticker, "token": token}
    res = requests.get(url, params=params)
    return res.json().get('data', [])[-1:] if res.status_code == 200 else "API_Error"

def get_expert_local(ticker):
    """強攻 Cmoney 與 MoneyDJ (解析在地專家)"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    # Cmoney 解析目標價數值
    cm_url = f"https://www.cmoney.tw/follow/channel/stock-{ticker}?chart=target"
    cm_res = requests.get(cm_url, headers=headers)
    cm_prices = re.findall(r"\"TargetPrice\":([\d\.]+)", cm_res.text)
    # MoneyDJ 確認報告清單
    mdj_url = f"https://www.moneydj.com/KMDJ/Common/ListNewData.aspx?index=1&svc=NW&a=TWS:{ticker}"
    mdj_res = requests.get(mdj_url, headers=headers)
    return {
        "cmoney_consensus": cm_prices[:5],
        "has_moneydj_reports": "研究報告" in mdj_res.text
    }

def get_stock_full_package(ticker, is_tw=True):
    """匯整單一標的所有數據 (Global + Internal + (Local if TW))"""
    print(f"--- 正在提取 {ticker} 全量數據包 ---")
    symbol = f"{ticker}.TW" if is_tw else ticker
    stock = yf.Ticker(symbol)
    info = stock.info
    
    # 1. 核心與全球專家 (yfinance)
    package = {
        "ticker": ticker,
        "name": info.get('longName', 'N/A'),
        "price": info.get('currentPrice') or info.get('lastPrice'),
        "expert_global": {
            "target": info.get('targetMeanPrice'),
            "count": info.get('numberOfAnalystOpinions'),
            "rating": info.get('recommendationKey')
        },
        "fundamentals": {
            "roe": info.get('returnOnEquity'),
            "payout": info.get('payoutRatio'),
            "inst_held": info.get('heldPercentInstitutions')
        }
    }
    
    # 2. 系統計算 (Internal SGR)
    if package["fundamentals"]["roe"] and package["fundamentals"]["payout"]:
        package["internal_sgr"] = f"{package['fundamentals']['roe'] * (1 - package['fundamentals']['payout']) * 100:.2f}%"
    
    # 3. 台股專屬 (Local + FinMind)
    if is_tw:
        fm_token = os.getenv('FINMIND_TOKEN')
        package["expert_local"] = get_expert_local(ticker)
        package["official_revenue"] = get_finmind_data(ticker, fm_token)
        
    return package

def run_ultimate_probe():
    all_data = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # 併行抓取所有標的
        future_tw = {executor.submit(get_stock_full_package, tk, True): tk for tk in STOCKS_TW}
        future_us = {executor.submit(get_stock_full_package, tk, False): tk for tk in STOCKS_US}
        
        for future in concurrent.futures.as_completed({**future_tw, **future_us}):
            res = future.result()
            all_data[res['ticker']] = res

    print("\n" + "🚀" * 10 + " 全量整合數據成果展示 " + "🚀" * 10)
    print(json.dumps(all_data, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50)

if __name__ == "__main__":
    run_ultimate_probe()
