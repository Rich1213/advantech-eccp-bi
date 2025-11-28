import pandas as pd
import os

# --- 1. 路徑設定 ---
BASE_PATH = "/Users/rich/我的雲端硬碟/eCCP"
INPUT_FILE = os.path.join(BASE_PATH, "02_ProcessedData", "POS_Cleaned.parquet")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "02_ProcessedData", "BI_Tables")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def create_star_schema():
    print("🌟 [Star Schema 引擎 V2.0] 啟動中 (強制大寫標準化)...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 錯誤: 找不到輸入檔 {INPUT_FILE}")
        return

    df = pd.read_parquet(INPUT_FILE)
    print(f"   - 讀取來源資料: {len(df):,} 筆")

    # 欄位名稱對齊資料字典
    rename_map = {
        'CustCty': 'CustCity',
        'Adj PtNo': 'AdjPtNo'
    }
    available_map = {k: v for k, v in rename_map.items() if k in df.columns}
    if available_map:
        df = df.rename(columns=available_map)

    # ==========================================
    # 0. 全局標準化：Key 值強制轉大寫 (解決 Power BI 多對多問題)
    # ==========================================
    print("   - 🔄 正在執行 Key 值大寫標準化...")
    key_cols = ['AdjPtNo', 'PtNo', 'DistName', 'CustName', 'CustCity', 'CustSt', 'CustZIP']
    for col in key_cols:
        if col in df.columns:
            # 轉字串 -> 去空白 -> 轉大寫
            df[col] = df[col].astype(str).str.strip().str.upper()
            # 處理空值字串
            df[col] = df[col].replace({'NAN': 'UNKNOWN', 'NONE': 'UNKNOWN', '': 'UNKNOWN'})
        else:
            print(f"     ⚠️ 欄位 {col} 不存在，略過大寫標準化")
    
    # ==========================================
    # 1. 建立 Dim_Product (產品維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Product...")
    product_key = 'AdjPtNo' if 'AdjPtNo' in df.columns else 'PtNo'
    prod_cols = [c for c in ['AdjPtNo', 'PtNo', 'Product Line', 'Product Division', 'Product Group', 'Group Roll-UP'] if c in df.columns]
    if product_key not in df.columns:
        raise KeyError("缺少產品鍵欄位 AdjPtNo / PtNo，無法建立產品維度")
    df[product_key] = df[product_key].fillna('UNKNOWN')
    
    # 去重
    dim_prod = df[prod_cols].drop_duplicates(subset=[product_key])
    dim_prod = dim_prod.fillna('Unknown')
    
    dim_prod.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Product.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_prod):,} 個唯一產品")

    # ==========================================
    # 2. 建立 Dim_Distributor (通路維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Distributor...")
    dist_cols = ['DistName', 'Channel Manager', 'TerrNo', 'DIST TYPE']
    df['DistName'] = df['DistName'].fillna('UNKNOWN')
    
    dim_dist = df[dist_cols].drop_duplicates(subset=['DistName'])
    dim_dist = dim_dist.fillna('Unknown')
    
    dim_dist.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Distributor.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_dist):,} 個經銷商")

    # ==========================================
    # 3. 建立 Dim_Customer (客戶維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Customer...")
    cust_cols = ['CustName', 'CustCity', 'CustSt', 'CustZIP', 'Channel District', 'Channel GeoGroup']
    available_cust_cols = [c for c in cust_cols if c in df.columns]
    missing_cust_cols = sorted(set(cust_cols) - set(available_cust_cols))
    if missing_cust_cols:
        print(f"     ⚠️ 以下客戶欄位缺失: {', '.join(missing_cust_cols)}，將以現有欄位產出")

    dim_cust = df[available_cust_cols].drop_duplicates()
    dim_cust = dim_cust.reset_index(drop=True)
    dim_cust['Customer_Key'] = dim_cust.index + 10000 
    
    dim_cust.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Customer.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_cust):,} 個唯一客戶")

    # ==========================================
    # 4. 建立 Dim_Date (時間維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Date...")
    if 'POS_ShpDate' in df.columns:
        min_date = df['POS_ShpDate'].min()
        max_date = df['POS_ShpDate'].max()
        start_date = pd.to_datetime(f"{min_date.year}-01-01")
        end_date = pd.to_datetime(f"{max_date.year}-12-31")
        
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        dim_date = pd.DataFrame({'Date': date_range})
        
        dim_date['Year'] = dim_date['Date'].dt.year
        dim_date['Month'] = dim_date['Date'].dt.month
        dim_date['Month_Name'] = dim_date['Date'].dt.month_name()
        dim_date['Quarter'] = dim_date['Date'].dt.quarter
        dim_date['YearQuarter'] = dim_date['Year'].astype(str) + "-Q" + dim_date['Quarter'].astype(str)
        dim_date['YearMonth'] = dim_date['Date'].dt.strftime('%Y-%m')
        
        dim_date.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Date.parquet"), index=False)
        print(f"     ✅ 完成: {len(dim_date):,} 天的日曆資料")

    # ==========================================
    # 5. 建立 Fact_Sales (事實表)
    # ==========================================
    print("   - 🔨 正在建立 Fact_Sales...")
    
    # 關聯 Customer_Key
    merge_cols = [col for col in ['CustName', 'CustCity', 'CustSt', 'CustZIP'] if col in dim_cust.columns]
    fact_df = df.merge(dim_cust[merge_cols + ['Customer_Key']], 
                       on=merge_cols, 
                       how='left')
    
    fact_cols = [
        'POS_ShpDate', 'AdjPtNo', 'PtNo', 'DistName', 'Customer_Key', 
        'ResExt', 'Qty', 'UnitResale', 'UnitCst', 'CstExt'
    ]
    
    final_fact_cols = [c for c in fact_cols if c in fact_df.columns]
    fact_table = fact_df[final_fact_cols]
    
    fact_table.to_parquet(os.path.join(OUTPUT_FOLDER, "Fact_Sales.parquet"), index=False)
    print(f"     ✅ 完成: {len(fact_table):,} 筆交易資料")
    
    print("\n" + "="*50)
    print("🚀 [修正完成] 所有 Key 值已轉為大寫，請重新整理 Power BI")
    print("="*50)

if __name__ == "__main__":
    create_star_schema()