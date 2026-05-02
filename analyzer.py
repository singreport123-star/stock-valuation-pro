import json
import os
import pandas as pd
from datetime import datetime

# --- 配置區 ---
TW_STOCK_PATH = "data/TW/stocks/4958.json"
US_STOCK_PATH = "data/US/stocks/META.json"
MACRO_PATH = "data/US/macro/macro_indicators.json"

def load_data(path):
    if not os.path.exists(path):
        print(f"⚠️ 找不到路徑: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 讀取 JSON 出錯 ({path}): {e}")
        return None

def run_diagnosis_4958():
    data = load_data(TW_STOCK_PATH)
    macro = load_data(MACRO_PATH)
    
    print(f"\n{'='*20} 4958 (臻鼎-KY) 診斷報表 {'='*20}")
    if not data: return

    # 1. 可轉債 (CB)
    cb_data = data.get("chip_union", {}).get("cb_transaction", [])
    if cb_data:
        df_cb = pd.DataFrame(cb_data)
        last_cb = df_cb.iloc[-1].to_dict()
        print(f"📊 [CB 監控]: 最新日期 {last_cb.get('date')} | 成交量: {last_cb.get('Trade_Volume')} | 價格: {last_cb.get('Closing_Price')}")
    
    # 2. 匯率背景
    if macro and "USD_TWD" in macro:
        usd_twd = macro["USD_TWD"]
        latest_rate = list(usd_twd.values())[-1].get("Close")
        print(f"💵 [匯率背景]: USD/TWD 目前約 {latest_rate:.2f}")

    # 3. 新聞
    print("📰 [最新新聞摘要]:")
    for n in data.get("news", [])[:2]:
        print(f" - {n.get('title')} ({n.get('publisher')})")

def run_diagnosis_meta():
    data = load_data(US_STOCK_PATH)
    
    print(f"\n{'='*20} META (Meta Platforms) 診斷報表 {'='*20}")
    if not data: return

    # 1. 內部人交易
    insider = data.get("holders", {}).get("insider_transactions", {})
    if insider:
        df_insider = pd.DataFrame(insider).head(3)
        print(f"👥 [內部人動向]: 最新交易摘要:")
        for _, row in df_insider.iterrows():
            print(f" - {row.get('Text')}")

    # 2. 分析師預期
    estimates = data.get("fmp_ext", {}).get("estimates", [])
    if estimates:
        latest = estimates[0]
        print(f"📈 [分析師預期]: 預估營收: {latest.get('estimatedRevenueAverage'):,.0f} | 預估 EPS: {latest.get('estimatedEpsAverage')}")

    # 3. 新聞
    print("📰 [最新美股新聞]:")
    for n in data.get("news", [])[:2]:
        print(f" - {n.get('title')} ({n.get('publisher')})")

if __name__ == "__main__":
    run_diagnosis_4958()
    run_diagnosis_meta()
