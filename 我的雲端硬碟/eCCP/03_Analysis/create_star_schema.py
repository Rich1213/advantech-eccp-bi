import pandas as pd
import os

# --- 1. 路徑設定 ---
# 動態抓取路徑，避免寫死
current_dir = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.dirname(current_dir)

INPUT_FILE = os.path.join(BASE_PATH, "02_ProcessedData", "POS_Cleaned.parquet")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "02_ProcessedData", "BI_Tables")
CONFIG_FILE = os.path.join(BASE_PATH, "99_Config", "Customer_Parent_Mapping.xlsx")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def create_star_schema():
    print("🌟 [Star Schema 引擎 V3.1 - Fix Mapping] 啟動中...")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 錯誤: 找不到輸入檔 {INPUT_FILE}")
        return

    df = pd.read_parquet(INPUT_FILE)
    print(f"   - 讀取來源資料: {len(df):,} 筆")

    # 欄位名稱對齊
    rename_map = {'CustCty': 'CustCity', 'Adj PtNo': 'AdjPtNo'}
    available_map = {k: v for k, v in rename_map.items() if k in df.columns}
    if available_map: df = df.rename(columns=available_map)

    # 0. 全局標準化
    print("   - 🔄 Key 值大寫標準化...")
    key_cols = ['AdjPtNo', 'PtNo', 'DistName', 'CustName', 'CustCity', 'CustSt', 'CustZIP']
    for col in key_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            df[col] = df[col].replace({'NAN': 'UNKNOWN', 'NONE': 'UNKNOWN', '': 'UNKNOWN'})

    # 1. Dim_Product
    print("   - 🔨 建立 Dim_Product...")
    product_key = 'AdjPtNo' if 'AdjPtNo' in df.columns else 'PtNo'
    prod_cols = [c for c in ['AdjPtNo', 'PtNo', 'Product Line', 'Product Division', 'Product Group', 'Group Roll-UP'] if c in df.columns]
    df[product_key] = df[product_key].fillna('UNKNOWN')
    dim_prod = df[prod_cols].drop_duplicates(subset=[product_key]).fillna('Unknown')
    dim_prod.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Product.parquet"), index=False)

    # 2. Dim_Distributor
    print("   - 🔨 建立 Dim_Distributor...")
    dist_cols = ['DistName', 'Channel Manager', 'TerrNo', 'DIST TYPE']
    df['DistName'] = df['DistName'].fillna('UNKNOWN')
    dim_dist = df[dist_cols].drop_duplicates(subset=['DistName']).fillna('Unknown')
    dim_dist.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Distributor.parquet"), index=False)

    # 3. Dim_Customer (含集團歸戶)
    print("   - 🔨 建立 Dim_Customer (整合集團歸戶)...")
    cust_cols = ['CustName', 'CustCity', 'CustSt', 'CustZIP', 'Channel District', 'Channel GeoGroup']
    available_cust_cols = [c for c in cust_cols if c in df.columns]
    
    # 3.1 基礎清單
    dim_cust = df[available_cust_cols].drop_duplicates().reset_index(drop=True)

    # 3.2 讀取 Excel 黃金帳本
    if os.path.exists(CONFIG_FILE):
        print("     📖 讀取 Mapping Table...")
        try:
            map_df = pd.read_excel(CONFIG_FILE)
            
            # [Fix] 去除欄位名稱的空白 (以防萬一)
            map_df.columns = map_df.columns.str.strip()
            
            # 檢查關鍵欄位是否存在
            if 'Original_CustName' in map_df.columns:
                # 標準化 Key
                map_df['Original_CustName'] = map_df['Original_CustName'].astype(str).str.strip().str.upper()
                
                # 去重 (確保 Excel 裡沒有重複的 Key)
                map_df = map_df.drop_duplicates(subset=['Original_CustName'])
                
                # 合併
                dim_cust = dim_cust.merge(
                    map_df[['Original_CustName', 'Parent_Group', 'Category', 'Source']], # 這裡讀取 Category, Source
                    left_on='CustName',
                    right_on='Original_CustName',
                    how='left'
                )
                
                # 填補空值
                dim_cust['Parent_Group'] = dim_cust['Parent_Group'].fillna(dim_cust['CustName'])
                dim_cust['Category'] = dim_cust['Category'].fillna('Uncategorized')
                dim_cust['Source'] = dim_cust['Source'].fillna('Auto-Generated')
                
                # 移除多餘欄位
                dim_cust = dim_cust.drop(columns=['Original_CustName'])
            else:
                print("     ⚠️ Excel 缺少 'Original_CustName' 欄位，跳過合併")
                dim_cust['Parent_Group'] = dim_cust['CustName']
                dim_cust['Category'] = 'Uncategorized'
        except Exception as e:
            print(f"     ⚠️ 讀取 Excel 失敗: {e}")
            dim_cust['Parent_Group'] = dim_cust['CustName']
            dim_cust['Category'] = 'Uncategorized'
    else:
        print("     ⚠️ 找不到 Mapping Excel，使用預設值")
        dim_cust['Parent_Group'] = dim_cust['CustName']
        dim_cust['Category'] = 'Uncategorized'

    # 產生 Key
    dim_cust = dim_cust.reset_index(drop=True)
    dim_cust['Customer_Key'] = dim_cust.index + 10000 
    dim_cust.to_parquet(os.path.join(OUTPUT_FOLDER, "Dim_Customer.parquet"), index=False)
    print(f"     ✅ 完成: {len(dim_cust):,} 個唯一客戶")

    # 4. Dim_Date
    print("   - 🔨 建立 Dim_Date...")
    if 'POS_ShpDate' in df.columns:
        min_date = df['POS_ShpDate'].min()
        max_date = df['POS_ShpDate'].max()
        # 避免空值日期導致報錯
        if pd.isna(min_date) or pd.isna(max_date):
             start_date = pd.to_datetime("2023-01-01")
             end_date = pd.to_datetime("2025-12-31")
        else:
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

    # 5. Fact_Sales
    print("   - 🔨 建立 Fact_Sales...")
    merge_cols = [col for col in ['CustName', 'CustCity', 'CustSt', 'CustZIP'] if col in dim_cust.columns]
    fact_df = df.merge(dim_cust[merge_cols + ['Customer_Key']], on=merge_cols, how='left')
    
    fact_cols = ['POS_ShpDate', 'AdjPtNo', 'PtNo', 'DistName', 'Customer_Key', 'ResExt', 'Qty', 'UnitResale', 'UnitCst', 'CstExt']
    final_fact_cols = [c for c in fact_cols if c in fact_df.columns]
    fact_table = fact_df[final_fact_cols]
    
    fact_table.to_parquet(os.path.join(OUTPUT_FOLDER, "Fact_Sales.parquet"), index=False)
    print(f"     ✅ 完成: {len(fact_table):,} 筆交易資料")
    print("\n🚀 [ETL 完成] 所有檔案已輸出至 BI_Tables")

if __name__ == "__main__":
    create_star_schema()