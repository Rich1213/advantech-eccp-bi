# 程式碼版本維護 SOP (Pure Git Workflow)

```mermaid
flowchart TD
    %% --- 樣式定義 ---
    classDef state fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#795548;
    classDef gitCommand fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
    classDef decision fill:#ffcdd2,stroke:#f44336,stroke-width:2px,color:#b71c1c;
    classDef final fill:#a5d6a7,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;

    %% 起點
    Start((開始：程式碼已修改)):::state --> A1

    %% --- Phase 1: 本地端儲存 ---
    subgraph Local_1["1. 本地端儲存 (Local Commit)"]
        A1["git status\n檢查變更"]:::gitCommand --> A2["git add .\n加入暫存區"]:::gitCommand
        A2 --> A3["git commit -m 'msg'\n建立本地版本"]:::gitCommand
    end

    %% --- Phase 2: 雲端同步與解決衝突 ---
    subgraph Remote_2["2. 雲端同步與解決衝突 (Remote Sync)"]
        A3 --> B1{雲端是否有分歧？}:::decision

        B1 -- "YES / 有衝突" --> B2["git pull origin main\n拉取遠端更新"]:::gitCommand
        B2 --> C1{手動解決衝突？}:::decision
        C1 -- "已解決" --> A3

        B1 -- "NO / 無分歧" --> B3["git push\n推送到 GitHub"]:::gitCommand
    end

    %% 終點
    B3 --> End((✅ 備份成功)):::final
```

---

### 📋 最終指令參考表 (Git Command Reference)

| 目的 (Purpose) | 終端機指令 (Terminal Command) | 備註 (Note) |
| :--- | :--- | :--- |
| **檢查狀態** | `git status` | 查看哪些檔案已修改但尚未提交。 |
| **暫存變更** | `git add .` | 將所有變更的檔案加入等待提交區。 |
| **提交歷史** | `git commit -m "Add new feature logic"` | 儲存一個不可變的本地版本。 |
| **拉取同步** | `git pull origin main` | **在 Push 失敗時使用**，先下載雲端更新，並解決衝突。 |
| **推送雲端** | `git push` | 將本地提交的進度推送到 GitHub。 |
| **強制推送** | `git push -f origin main` | **危險！** 當你的本地端確定是正確的，用來覆蓋 GitHub 上錯誤或混亂的歷史紀錄。 |

這份文件是你日常 Pure Git Workflow 的標準流程：先本地 commit，再視情況 pull 解決衝突，最後 push 備份到雲端。