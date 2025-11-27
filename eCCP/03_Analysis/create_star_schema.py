import pandas as pd
import os
import numpy as np

# --- 1. 路徑設定 ---
BASE_PATH = "/Users/rich/我的雲端硬碟/eCCP"
INPUT_FILE = os.path.join(BASE_PATH, "02_ProcessedData", "POS_Cleaned.parquet")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "02_ProcessedData", "BI_Tables")

# 建立輸出資料夾
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def create_star_schema():
    print("🌟 [Star Schema 引擎] 啟動中...")
    
    # 讀取清洗後的 Parquet
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 錯誤: 找不到輸入檔 {INPUT_FILE}")
        return

    df = pd.read_parquet(INPUT_FILE)
    print(f"   - 讀取來源資料: {len(df):,} 筆")

    # ==========================================
    # 1. 建立 Dim_Product (產品維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Product...")
    # 選取產品相關欄位
    prod_cols = ['PtNo', 'Product Line', 'Product Division', 'Product Group', 'Group Roll-UP']
    # 去除重複，只留唯一的產品資料
    dim_prod = df[prod_cols].drop_duplicates(subset=['PtNo'])
    
    # 處理可能的缺失值
    dim_prod = dim_prod.fillna('Unknown')
    
    # 儲存
    dim_prod.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Product.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_prod):,} 個唯一產品")

    # ==========================================
    # 2. 建立 Dim_Distributor (通路維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Distributor...")
    dist_cols = ['DistName', 'Channel Manager', 'TerrNo', 'DIST TYPE']
    # 確保這些欄位存在 (防呆)
    valid_dist_cols = [c for c in dist_cols if c in df.columns]
    
    dim_dist = df[valid_dist_cols].drop_duplicates(subset=['DistName'])
    dim_dist = dim_dist.fillna('Unknown')
    
    dim_dist.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Distributor.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_dist):,} 個經銷商")

    # ==========================================
    # 3. 建立 Dim_Customer (客戶維度) - 關鍵!
    # ==========================================
    print("   - 🔨 正在建立 Dim_Customer (並產生 Customer_Key)...")
    # 定義什麼算是一個「唯一客戶」：名字 + 郵遞區號 (避免同名不同地)
    cust_cols = ['CustName', 'CustCity', 'CustSt', 'CustZIP', 'Channel District', 'Channel GeoGroup']
    valid_cust_cols = [c for c in cust_cols if c in df.columns]
    
    # 去重
    dim_cust = df[valid_cust_cols].drop_duplicates()
    
    # 【關鍵步驟】產生 Customer_Key (整數 ID)
    # 這讓我們在 Fact Table 可以只存 ID，節省空間並加速
    dim_cust = dim_cust.reset_index(drop=True)
    dim_cust['Customer_Key'] = dim_cust.index + 10000 # 從 10000 開始編號
    
    # 儲存
    dim_cust.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Customer.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_cust):,} 個唯一客戶")

    # ==========================================
    # 4. 建立 Dim_Date (時間維度)
    # ==========================================
    print("   - 🔨 正在建立 Dim_Date (日曆表)...")
    # 找出資料中的最小與最大日期
    min_date = df['POS_ShpDate'].min()
    max_date = df['POS_ShpDate'].max()
    
    # 往前往後多抓一點緩衝 (例如年底要預測明年)
    start_date = pd.to_datetime(f"{min_date.year}-01-01")
    end_date = pd.to_datetime(f"{max_date.year}-12-31")
    
    # 產生連續日期序列
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    dim_date = pd.DataFrame({'Date': date_range})
    
    # 豐富化時間欄位
    dim_date['Year'] = dim_date['Date'].dt.year
    dim_date['Month'] = dim_date['Date'].dt.month
    dim_date['Month_Name'] = dim_date['Date'].dt.month_name()
    dim_date['Quarter'] = dim_date['Date'].dt.quarter
    dim_date['YearQuarter'] = dim_date['Year'].astype(str) + "-Q" + dim_date['Quarter'].astype(str)
    dim_date['YearMonth'] = dim_date['Date'].dt.strftime('%Y-%m')
    
    # 儲存
    dim_date.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Date.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_date):,} 天的日曆資料")

    # ==========================================
    # 5. 建立 Fact_Sales (事實表)
    # ==========================================
    print("   - 🔨 正在建立 Fact_Sales (回填 Key 值)...")
    
    # 這裡需要把 Customer_Key Join 回來
    # 根據我們剛剛定義的唯一鍵 (Name + City + State + ZIP ...)
    # 為了簡化，我們先用 merge
    fact_df = df.merge(dim_cust[['CustName', 'CustZIP', 'Customer_Key']], 
                       on=['CustName', 'CustZIP'], 
                       how='left')
    
    # 選取 Fact Table 需要的欄位 (Key + Metrics)
    fact_cols = [
        'POS_ShpDate',      # Date Key
        'PtNo',             # Product Key
        'DistName',         # Distributor Key
        'Customer_Key',     # Customer Key (我們剛產生的)
        'ResExt',           # Metric: 金額
        'Qty',              # Metric: 數量
        'UnitResale',       # Metric: 單價
        'UnitCst',          # Metric: 成本
        'CstExt'            # Metric: 總成本
    ]
    
    # 只保留存在的欄位
    final_fact_cols = [c for c in fact_cols if c in fact_df.columns]
    fact_table = fact_df[final_fact_cols]
    
    # 儲存
    fact_table.to_parquet(os.path.join(OUTPUT_FOLDER, "Fact_Sales.parquet"), index=False)
    
    print(f"     ✅ 完成: {len(fact_table):,} 筆交易資料")
    
    print("\n" + "="*50)
    print("🚀 [任務完成] 所有 BI 資料表已輸出至:")
    print(f"📂 {OUTPUT_FOLDER}")
    print("="*50)
    print("請確認以下檔案是否產生：")
    print("1. Fact_Sales.parquet")
    print("2. Dim_Product.parquet")
    print("3. Dim_Customer.parquet")
    print("4. Dim_Distributor.parquet")
    print("5. Dim_Date.parquet")

if __name__ == "__main__":
    create_star_schema()