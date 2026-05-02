import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime, date

# --- 美股全量聯集：JSON 序列化修正版 V10 ---
TARGET = "META"
BASE_DATA_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Fix] {msg}")

def json_serial(obj):
    """處理 JSON 無法序列化的日期與時間物件"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_to_dict(df):
    """將 yfinance 的 DataFrame 安全轉為字典"""
    try:
        if df is not None and not df.empty:
            return json.loads(df.to_json(orient="index", date_format='iso'))
        return {}
    except:
        return {}

def harvest_us_v10():
    log(f"🚀 啟動 {TARGET} 全量數據提取 (修復序列化問題)...")
    
    try:
        stock = yf.Ticker(TARGET)
        
        # 1. 基礎指標與新聞
        log("🧵 提取基礎指標與新聞...")
        info = stock.info
        news = stock.news if hasattr(stock, 'news') else []
        
        # 2. 法定財務報表 (損益/資產/現金流)
        log("🧵 提取法定財報數據...")
        financials = safe_to_dict(stock.quarterly_financials)
        balance_sheet = safe_to_dict(stock.quarterly_balance_sheet)
        cashflow = safe_to_dict(stock.quarterly_cashflow)
        
        # 3. 分析師評價與行事曆
        log("🧵 提取分析師評價與預估...")
        recommendations = safe_to_dict(stock.recommendations)
        # 行事曆通常是 dict，內部可能含 date
        calendar = stock.calendar if stock.calendar is not None else {}
        
        # 封裝全量聯集
        full_payload = {
            "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "ver": "V10-Final-Union"},
            "fundamental_summary": info,
            "financial_statements": {
                "income": financials,
                "balance": balance_sheet,
                "cash_flow": cashflow
            },
            "market_consensus": {
                "recommendations": recommendations,
                "calendar": calendar
            },
            "news": news if news else []
        }

    except Exception as e:
        log(f"💥 採集過程發生錯誤: {e}")
        return

    # 執行物理存檔
    try:
        os.makedirs(BASE_DATA_DIR, exist_ok=True)
        with open(f"{BASE_DIR_PATH if 'BASE_DIR_PATH' in locals() else BASE_DATA_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
            json.dump(full_payload, f, ensure_ascii=False, indent=2, default=json_serial)
        log(f"✅ {TARGET} 入庫成功。")
    except Exception as e:
        log(f"💥 存檔失敗: {e}")

if __name__ == "__main__":
    harvest_us_v10()
