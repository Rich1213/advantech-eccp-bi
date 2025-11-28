# POS 數據字典 (Data Dictionary)

## 核心欄位
* **POS_ShpDate**: 出貨日期 (關鍵的時間維度)，由於本POS data無真正下定單日期，統一用這個當訂單日期
* **DistName**: 經銷商名稱 (例如 MOUSER, DIGI-KEY)
* **CustName**: 終端客戶名稱 (我們想分析的目標)
* **ResExt**: **[關鍵指標]** 總銷售金額 (Resale Extended)。公式通常是 Qty * UnitResale。這是我們認定「業績」的主要欄位。
* **Qty**: 銷售數量
* **AdjPtNo**: 原廠料號 (Part Number)

## 產品階層架構 (Product Hierarchy) - 由高至低 (Level 1 -> Level 4)

### Level 1: 策略事業群 (SBU / Group Roll-UP)
* **對應欄位**: `Group Roll-UP`
* **定義**: 研華組織架構的最高層級，四大 SBU。
* **主要值 (Values)**:
    * **IIoT**: Industrial-IoT (工業物聯網)
    * **EIoT**: Embedded-IoT (嵌入式物聯網)
    * **SIoT**: Service-IoT (服務物聯網)
    * **ACG**: Applied Computing Group (應用電腦)

### Level 2: 產品群 (Product Group)
* **對應欄位**: `Product Group`
* **定義**: 隸屬於 SBU 之下的次級集團或功能性組織。
* **範例**: 
    * `Embedded Computing Group` (歸屬 EIoT)
    * `Industrial Automation Group` (歸屬 IIoT)
    * `Advantech Service+` (歸屬 SIoT)

### Level 3: 產品事業處 (Product Division)
* **對應欄位**: `Product Division`
* **定義**: 具體的產品研發與管理部門，負責特定領域的產品策略。
* **範例**: 
    * `Edge AI Platform`
    * `Industrial HMI`
    * `Intelligent Systems`

### Level 4: 產品線 (Product Line)
* **對應欄位**: `Product Line`
* **定義**: 最細顆粒度的產品分類，通常為 3-4 碼英文縮寫。
* **範例**: 
    * `EAIM` (Edge AI Modules)
    * `TERM`
    * `AIMB`

## 地理與組織
* **TerrNo**: 美國的區域代碼 (例如 CA, NY)，若寫 INTERNATIONAL 意思是指美國之外
* **CustZIP**: 客戶郵遞區號，美國之外的則顯示國家名稱 (用於熱點地圖分析)
* **CustSt**: 若是美國本土則用兩個英文字元顯示州別縮寫，美國之外的則顯示國家名稱(用於熱點地圖分析)
* **Channel District**: 市場區域劃分 (銷售管轄區)
    * **美國本土 (US Domestic)**: 
        * 數據被拆分為三大區，分析「美國總業績」時需加總以下三者：
        * `WEST` (美西)
        * `CENTRAL` (美中)
        * `EAST` (美東)
    * **國際市場 (International)**:
        * `CANADA` (加拿大 - 雖在北美但通常獨立計算)
        * `LATAM` (拉丁美洲)
        * `EUROPE` (歐洲)
        * `ASIA` / `CN` / `TW` ... (亞洲及其他特定國家區域)
    * **分析洞察**: 
        * 若要計算 NAM (North America) 總業績，通常公式為：(WEST + CENTRAL + EAST + CANADA)。
        * 若要抓跨境電商訊號，需觀察 `DistName` 為美國電商 (如 MOUSER) 但 `Channel District` 為 `EUROPE` 或 `ASIA` 的訂單。
* **Channel GeoGroup**: 大地理區域
* **異常狀態 (Exception Handling)**:
        * `Unknown` / `(Blank)`: 未歸類區域。
        * **業務意義**: 這代表「無主業績」或「系統未正確對應」。
        * **分析策略**: 在計算區域滲透率時，需先確認這部分佔比。若佔比過高 (>5%)，則需回頭修正原始資料；若低，可暫時歸類為 "Others"。
* **Channel Manager**: 負責該經銷商的業務經理

## 成本與定價 (選用分析)
* **UnitCst**: 單位成本(意即我們賣給經銷商價格)
* **CstExt**: 總成本
* **UnitResale**: 單位建議售價
* **ResExt**: 總建議售價

---
**備註：**
1. 分析時主要依據 `ResExt` 作為業績總金額 (`Amount`)。
2. `CustName` 經常會有髒資料 (例如同一家公司有多種拼法及後綴)，後續可能需要清洗。


## 衍生欄位
* **時間欄位 (Derived Fields)**:
    * *注意：以下欄位為原始資料預先計算好的，使用前需注意與 `POS_ShpDate` 的一致性。*
    * **Fiscal Year**: 財政年度 (用於計算年度業績目標)。
    * **Fiscal Quarter**: 財政季度 (Q1, Q2, Q3, Q4)。
    * **Fiscal Month**: 財政月份 (格式通常為 YYYY_MM)。
    * **Calendar Month**: 曆月份名稱 (如 October, November)。

* **分析策略**: 
    * 短期分析直接使用衍生欄位 (方便 Groupby)。
    * 建立 Star Schema 時，將以此區塊資訊建立獨立的 `Dim_Time` 資料表。