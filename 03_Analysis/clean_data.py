import pandas as pd
import os
import numpy as np # 引入 numpy 處理空值

# --- 設定路徑 ---
BASE_PATH = "/Users/rich/我的雲端硬碟/eCCP"
RAW_DATA_PATH = os.path.join(BASE_PATH, "01_RawData", "POS_all.csv")
PROCESSED_FOLDER = os.path.join(BASE_PATH, "02_ProcessedData")

# 確保輸出資料夾存在
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

def clean_and_transform():
    print("🚀 [ETL 啟動] V5.0 最終融合版...")
    print(f"   - 讀取路徑: {RAW_DATA_PATH}")
    
    # 讀取 CSV
    df = pd.read_csv(RAW_DATA_PATH, low_memory=False)
    
    # 1. 欄位名稱標準化 (去除前後空白)
    df.columns = df.columns.str.strip()
    print(f"   - 原始資料筆數: {len(df):,}")

    # 2. 數值欄位清洗 (金額與數量)
    # 定義要清洗的欄位
    money_cols = ['UnitCst', 'CstExt', 'UnitResale', 'ResExt']
    qty_cols = ['Qty']
    
    # 清洗金額 (去 $ , 空白)
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('$', '', regex=False) \
                                         .str.replace(',', '', regex=False) \
                                         .str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # 清洗數量 (去 , 空白)
    for col in qty_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    print("   - ✅ 數值與金額欄位已標準化")

    # 3. 日期格式化
    if 'POS_ShpDate' in df.columns:
        df['POS_ShpDate'] = pd.to_datetime(df['POS_ShpDate'], errors='coerce')
    print("   - ✅ 日期欄位已標準化")

    # 4. 文字欄位去除雜質
    text_cols = ['DistName', 'CustName', 'Product Group', 'Product Division', 'Channel District']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # 把字串 'nan' 或空字串轉回真正的空值
            df[col] = df[col].replace({'nan': np.nan, '': np.nan, 'None': np.nan})

    # 5. [核心商業邏輯] 產品階層修復 (Hierarchy Repair)
    print("   - 🌳 正在執行 SBU 架構修復 (Level 1~4 Mapping)...")
    
    # A. 名稱標準化 (SYS -> Systems)
    if 'Product Division' in df.columns:
        df['Product Division'] = df['Product Division'].replace({'SYS': 'Systems'})

    # B. Level 2 (Product Group) -> Level 1 (Group Roll-UP)
    l2_to_l1_map = {
        'Embedded Computing Group': 'EIoT',
        'Embedded IoT': 'EIoT',
        'Industrial Automation Group': 'IIoT',
        'Industrial Cloud & Video Group': 'IIoT',
        'Service IoT Group': 'SIoT',
        'Advantech Service+ (AS+)': 'SIoT',
        'Applied Computing Group': 'ACG'
    }

    # C. Level 3 (Division) -> Level 1 (Group Roll-UP) (備用)
    l3_to_l1_map = {
        'Edge AI Platform': 'EIoT',
        'Industrial HMI': 'IIoT',
        'Intelligent Systems': 'IIoT',
        'Systems': 'IIoT'
    }

    # 執行修復
    if 'Group Roll-UP' in df.columns:
        # 先用 L2 補
        if 'Product Group' in df.columns:
            df['Group Roll-UP'] = df['Group Roll-UP'].fillna(df['Product Group'].map(l2_to_l1_map))
        
        # 再用 L3 補
        if 'Product Division' in df.columns:
            df['Group Roll-UP'] = df['Group Roll-UP'].fillna(df['Product Division'].map(l3_to_l1_map))
            
        # 剩下的填 Unknown
        df['Group Roll-UP'] = df['Group Roll-UP'].fillna('Unknown')
        
    print("   - ✅ SBU 架構修復完成")

    # 6. 輸出為 Parquet (高效能格式)
    output_file = "POS_Cleaned.parquet"
    output_path = os.path.join(PROCESSED_FOLDER, output_file)
    
    # 儲存
    df.to_parquet(output_path, index=False)
    
    print("\n" + "="*40)
    print(f"✨ [ETL 完成] 資料已輸出為 Parquet")
    print(f"📂 路徑: {output_path}")
    print("="*40)

    # 7. [Cursor 貢獻] 資料品質快報
    print("\n🔎 [資料品質驗證報告]")
    print(f"   - 總業績 (ResExt): ${df['ResExt'].sum():,.2f}")
    if 'Channel District' in df.columns:
        unknown_pct = (df['Channel District'] == 'Unknown').mean() * 100
        print(f"   - Channel District Unknown 佔比: {unknown_pct:.2f}%")
        if unknown_pct > 5: print("     ⚠️ 警告: 超過 5% 門檻，需注意！")
    
    print("\n📸 前 3 筆資料預覽:")
    cols_to_show = ['POS_ShpDate', 'Group Roll-UP', 'Product Division', 'ResExt', 'Qty']
    print(df[[c for c in cols_to_show if c in df.columns]].head(3).to_string(index=False))
    print("="*40)

if __name__ == "__main__":
    clean_and_transform()