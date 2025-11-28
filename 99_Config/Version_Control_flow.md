# 程式碼版本維護 SOP (Pure Git Workflow)

```mermaid
graph TD
    %% --- 樣式定義 ---
    classDef action fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef gitCommand fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px;
    classDef decision fill:#ffcdd2,stroke:#f44336,stroke-width:2px;
    classDef final fill:#a5d6a7,stroke:#2e7d32;

    Start((開始: 程式碼已修改)) --> A1;

    subgraph Local [1. 本地端儲存]
        A1["git status <br>(檢查變更)"]:::gitCommand --> A2["git add . <br>(全部加入暫存區)"]:::gitCommand;
        A2 --> A3["git commit -m '描述修改'"]:::gitCommand;
    end

    subgraph Remote [2. 雲端同步與解決衝突]
        A3 --> B1{雲端是否有分歧?};:::decision

        B1 -- YES (有衝突) --> B2["git pull origin main <br>(拉取遠端最新版本)"]:::gitCommand;
        
        B2 --> C1{手動解決衝突?};:::decision
        C1 -- YES --> A3;
        
        B1 -- NO / 衝突已解 --> B3["git push"]:::gitCommand;
    end

    B3 --> End((✅ 備份成功));:::final
```

---

### 📋 最終指令參考表 (Git Command Reference)

| 目的 (Purpose) | 終端機指令 (Terminal Command) | 備註 (Note) |
| :--- | :--- | :--- |
| **檢查狀態** | `git status` | 查看哪些檔案已修改但尚未提交。 |
| **暫存變更** | `git add .` | 將所有變更的檔案加入等待提交區。 |
| **提交歷史** | `git commit -m "Add new feature logic"` | 儲存一個不可變的本地版本。 |
| **拉取同步** | `git pull origin main` | **在 Push 失敗時使用**，先下載雲端更新。 |
| **推送雲端** | `git push` | 將本地提交的進度推送到 GitHub。 |
| **強制推送** | `git push -f origin main` | **危險！** 當你的本地端確定是正確的，用來覆蓋 GitHub 上錯誤或混亂的歷史紀錄。 |

這份文件已經將流程管理和程式碼維護分開。請使用這份最簡潔的指南來維護你的專案！