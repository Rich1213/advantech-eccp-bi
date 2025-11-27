import pandas as pd
import os

# --- 設定區 ---
# Rich 的 Mac 黃金路徑
base_path = "/Users/rich/我的雲端硬碟/eCCP/01_RawData"
file_name = "POS_all.csv"
# -------------

def run_ignition_test():
    full_path = os.path.join(base_path, file_name)
    print(f"🚀 [系統啟動] 正在連線至資料庫: {full_path} ...")

    if not os.path.exists(full_path):
        print(f"❌ [錯誤] 找不到檔案！請檢查路徑或檔名。")
        return

    try:
        # 讀取 CSV (這裡設定 low_memory=False 以防警告)
        df = pd.read_csv(full_path, low_memory=False)
        
        print("\n" + "="*40)
        print("✅ [連線成功] 數據輸送帶正常運作中")
        print("="*40)
        print(f"📊 數據概況 (Data Profile):")
        print(f"   - 總筆數 (Rows):    {df.shape[0]:,}")
        print(f"   - 總欄位 (Cols):    {df.shape[1]}")
        print("-" * 40)
        print("🔎 數據快照 (Snapshot):")
        # 只顯示幾個關鍵欄位確認內容正確
        cols_to_show = ['POS_ShpDate', 'DistName', 'CustName', 'ResExt']
        print(df[cols_to_show].head(3).to_string(index=False))
        print("="*40 + "\n")

    except Exception as e:
        print(f"❌ [嚴重錯誤] 讀取失敗: {e}")

if __name__ == "__main__":
    run_ignition_test()