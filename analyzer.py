import json
import os
import pandas as pd
from datetime import datetime

# --- 配置與路徑 ---
BASE_PATH = "data"

def load_json(path):
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def analyze_tw_4958(data):
    """台股深度分析：CB 壓力與籌碼聯集"""
    print(f"\n{'='*20} 🇹🇼 4958 臻鼎-KY 深度診斷 {'='*20}")
    
    # 1. CB 稀釋壓力評估
    cb_list = data.get("chip_union", {}).get("cb_transaction", [])
    if cb_list:
        df_cb = pd.DataFrame(cb_list)
        latest = df_cb.iloc[-1]
        print(f"🚩 [可轉債監控]: 最新日期 {latest['date']} | 價格: {latest['Closing_Price']} | 成交量: {latest['Trade_Volume']}")
    
    # 2. 法人籌碼動向
    inst = data.get("chip_union", {}).get("inst_investors", [])
    if inst:
        df_inst = pd.DataFrame(inst).tail(5)
        # 修正資料型態並計算合計
        net = df_inst['buy'].astype(float).sum() - df_inst['sell'].astype(float).sum()
        status = "🟢 偏多" if net > 0 else "🔴 偏空"
        print(f"👥 [法人籌碼]: 近 5 日累計買賣超: {net:,.0f} 股 | 趨勢: {status}")

def analyze_us_meta(data):
    """美股深度分析：自由現金流與成長性"""
    print(f"\n{'='*20} 🇺🇸 META Meta Platforms 深度診斷 {'='*20}")
    
    # 1. 財務報表煉金 (取損益表最新兩季)
    income = data.get("financial_statements", {}).get("income", {})
    if income:
        # yfinance 資料格式通常以日期為 Key
        df_inc = pd.DataFrame(income).T.sort_index(ascending=False)
        rev_growth = (df_inc['Total Revenue'].iloc[0] / df_inc['Total Revenue'].iloc[1] - 1) * 100
        print(f"💰 [成長動能]: 最新季營收成長 (QoQ): {rev_growth:.2f}%")

    # 2. 市場共識與目標價
    info = data.get("fundamental_summary", {})
    print(f"📈 [市場共識]: 本益比(前瞻): {info.get('forwardPE', 'N/A')} | 分析師目標價: {info.get('targetMeanPrice', 'N/A')}")
    
    # 3. 最新情報
    news = data.get("news", [])[:2]
    print("📰 [即時情報]:")
    for n in news:
        print(f" - {n.get('title')}")

if __name__ == "__main__":
    # 執行物理隔離讀取
    tw_data = load_json(os.path.join(BASE_PATH, "TW/stocks/4958.json"))
    us_data = load_json(os.path.join(BASE_PATH, "US/stocks/META.json"))
    
    if tw_data: analyze_tw_4958(tw_data)
    if us_data: analyze_us_meta(us_data)
