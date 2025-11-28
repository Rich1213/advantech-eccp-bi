graph TD
    %% --- 樣式定義 (Style Definitions) ---
    classDef storage fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#000,rx:5,ry:5;
    classDef process fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#000,rx:5,ry:5;
    classDef decision fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000,rhombus;
    classDef manual fill:#ffccbc,stroke:#d84315,stroke-width:2px,stroke-dasharray: 5 5,color:#000,rx:5,ry:5;
    classDef bi fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px,color:#000,rx:5,ry:5;
    classDef api fill:#e0f7fa,stroke:#006064,stroke-width:2px,color:#000,circle;

    %% --- 流程開始 ---
    Start((Start)) --> InputData

    subgraph "Phase 1: 資料前處理 (Data Pre-processing)"
        InputData[("📂 01_RawData/<br>POS_all.csv")]:::storage
        CleanScript["⚡️ 執行腳本:<br>03_Analysis/clean_data.py"]:::process
        CleanedData[("📂 02_ProcessedData/<br>POS_Cleaned.parquet")]:::storage
        
        InputData --> CleanScript
        CleanScript --> CleanedData
    end

    %% --- 關鍵分岔點 ---
    CleanedData --> Decision{{"❓ 判斷:<br>有無新增陌生客戶?<br>(New Customers?)"}}:::decision

    subgraph "Phase 2: 黃金帳本維護 (Master Data Management)"
        Decision -- "YES (有新客戶)" --> MapScript["⚡️ 執行腳本:<br>03_Analysis/generate_mapping.py"]:::process
        
        MapScript <--> Gemini(("☁️ Google<br>Gemini API")):::api
        
        MapScript --> ExcelDB[("📂 99_Config/<br>Customer_Parent_Mapping.xlsx")]:::storage
        
        HumanTask{{"👤 人工介入:<br>1. 確認 Tag/Group<br>2. 修改 Source='Manual'<br>3. 存檔"}}:::manual
        
        ExcelDB <--> HumanTask
    end

    %% --- 匯流點 ---
    HumanTask --> SchemaScript
    Decision -- "NO (無新客戶/僅更新數據)" --> SchemaScript

    subgraph "Phase 3: 資料倉儲與建模 (Data Warehousing)"
        SchemaScript["⚡️ 執行腳本:<br>03_Analysis/create_star_schema.py"]:::process
        
        BITables[("📂 02_ProcessedData/BI_Tables/<br>(Fact_Sales.parquet, Dim_*.parquet)")]:::storage
        
        SchemaScript -- "讀取 Parquet + Excel" --> BITables
    end

    subgraph "Phase 4: 商業智慧 (Business Intelligence)"
        BITables --> PowerBI["📊 Power BI Desktop:<br>05_Dashboards/Advantech_Sales_Analysis.pbip"]:::bi
        PowerBI --> Refresh("🔄 按下 Refresh"):::bi
    end

    %% --- 連結線 ---
    linkStyle default stroke:#333,stroke-width:1.5px;