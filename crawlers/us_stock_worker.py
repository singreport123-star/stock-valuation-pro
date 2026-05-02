import os
import json
import yfinance as yf
import pandas as pd
from datetime import datetime

# --- 美股全量聯集：yfinance 極限解鎖版 V9 ---
TARGET = "META"
BASE_DATA_DIR = "data/US/stocks"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [US-Extreme] {msg}")

def safe_to_dict(df):
    """將 yfinance 的 DataFrame 安全轉為字典，若為空則回傳空列表"""
    try:
        if df is not None and not df.empty:
            return json.loads(df.to_json(orient="index"))
        return []
    except:
        return []

def harvest_us_v9():
    log(f"🚀 啟動 {TARGET} 全量數據提取 (切換 yfinance 深度路徑)...")
    
    try:
        stock = yf.Ticker(TARGET)
        
        # 1. 基礎指標與新聞
        log("🧵 提取基礎指標與新聞...")
        info = stock.info
        news = stock.news
        
        # 2. 法定財務報表 (替代 FMP 403 區)
        log("🧵 提取法定財報 (損益/資產/現金流)...")
        financials = safe_to_dict(stock.quarterly_financials) # 季報
        balance_sheet = safe_to_dict(stock.quarterly_balance_sheet)
        cashflow = safe_to_dict(stock.quarterly_cashflow)
        
        # 3. 分析師預期與評價 (缺失補齊)
        log("🧵 提取分析師評價與預估...")
        recommendations = safe_to_dict(stock.recommendations)
        calendar = stock.calendar # 財報日
        
        # 封裝全量聯集
        full_payload = {
            "metadata": {"ticker": TARGET, "ts": datetime.now().isoformat(), "ver": "V9-YF-Extreme"},
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

        os.makedirs(BASE_DATA_DIR, exist_ok=True)
        with open(f"{BASE_DATA_DIR}/{TARGET}.json", "w", encoding="utf-8") as f:
            json.dump(full_payload, f, ensure_ascii=False, indent=2)
        
        log(f"✅ {TARGET} 入庫成功。財報項目數: {len(financials) if isinstance(financials, dict) else 0}")

    except Exception as e:
        log(f"💥 採集過程發生災難性錯誤: {e}")

if __name__ == "__main__":
    harvest_us_v9()
