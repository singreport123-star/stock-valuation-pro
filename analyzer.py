# --- 追加美股分析邏輯 ---
US_STOCK_PATH = "data/US/stocks/META.json"

def run_diagnosis_meta():
    data = load_data(US_STOCK_PATH)
    
    if not data:
        print("\n❌ 找不到 META 資料檔，請確認採集是否成功。")
        return

    print(f"\n=== META (Meta Platforms) 自動化診斷報表 [{datetime.now().strftime('%Y-%m-%d')}] ===")
    
    # 1. 機構與內部人籌碼掃描
    holders = data.get("holders", {})
    insider = holders.get("insider_transactions", {})
    if insider:
        df_insider = pd.DataFrame(insider).head(5)
        print(f"👥 [內部人動向]: 近期前 5 筆交易類型摘要:")
        for idx, row in df_insider.iterrows():
            print(f" - {row.get('Text')}")
    
    # 2. 分析師預期 (FMP 聯集)
    fmp_ext = data.get("fmp_ext", {})
    estimates = fmp_ext.get("estimates", [])
    if estimates:
        latest_est = estimates[0]
        print(f"📈 [分析師預期]: 預估營收(中位數): {latest_est.get('estimatedRevenueAverage'):,.0f} | 預估 EPS: {latest_est.get('estimatedEpsAverage')}")

    # 3. 財務快照
    info = data.get("info", {})
    print(f"💰 [財務快照]: P/E: {info.get('trailingPE', 'N/A')} | 股價/營收比: {info.get('priceToSalesTrailing12Months', 'N/A'):.2f} | 現金流: {info.get('freeCashflow', 'N/A'):,.0f}")

    # 4. 美股新聞標題
    print("\n📰 [最新美股新聞]:")
    news_list = data.get("news", [])[:3]
    for n in news_list:
        print(f" - {n.get('title')} ({n.get('publisher')})")

if __name__ == "__main__":
    # 同時執行台美雙軌分析
    run_diagnosis_4958()
    run_diagnosis_meta()
