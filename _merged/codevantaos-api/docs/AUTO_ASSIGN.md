# 自動分配任務 (Automatic Task Assignment)

## 概述 (Overview)

本專案實現了智能化的 Issue 和 Pull Request 自動指派功能。當新的 Issue 或 PR 被建立時，系統會根據一系列規則自動分配給最合適的維護者。

This project implements intelligent automatic assignment for Issues and Pull Requests. When a new Issue or PR is created, the system automatically assigns it to the most appropriate maintainer based on a set of rules.

## 工作原理 (How It Works)

自動指派工作流程 (`.github/workflows/auto-assign.yml`) 在以下情況下觸發：
- 新的 Issue 被建立
- 新的 Pull Request 被建立

The auto-assign workflow (`.github/workflows/auto-assign.yml`) triggers when:
- A new Issue is opened
- A new Pull Request is opened

## 指派規則 (Assignment Rules)

系統按照以下優先順序評估並指派：

### 1. 標籤規則 (Label-based Rules)

根據 Issue/PR 的標籤自動指派：

| 標籤 (Label) | 指派給 (Assigned To) | 說明 (Description) |
|-------------|---------------------|-------------------|
| `bug` | IndestructibleAutoOps | 錯誤修復由核心維護者處理 |
| `enhancement` | IndestructibleAutoOps | 功能增強由核心維護者審核 |
| `documentation` | IndestructibleAutoOps | 文件變更 |
| `question` | IndestructibleAutoOps | 問題諮詢 |

### 2. 檔案變更規則 (File-based Rules for PRs)

根據 PR 修改的檔案類型自動指派：

| 檔案模式 (File Pattern) | 指派給 (Assigned To) | 說明 (Description) |
|------------------------|---------------------|-------------------|
| `.github/workflows/*` | IndestructibleAutoOps | 工作流程變更需要維護者審核 |
| `*.md`, `*.txt` | IndestructibleAutoOps | 文件檔案變更 |
| `*.json`, `*.yml`, `*.yaml` | IndestructibleAutoOps | 設定檔案變更 |

### 3. 關鍵字規則 (Keyword-based Rules)

根據標題或內容中的關鍵字自動指派：

| 關鍵字 (Keywords) | 指派給 (Assigned To) | 說明 (Description) |
|------------------|---------------------|-------------------|
| urgent, 緊急, critical | IndestructibleAutoOps | 緊急事項優先處理 |
| @IndestructibleAutoOps | IndestructibleAutoOps | 明確提及維護者 |

### 4. 預設規則 (Default Rule)

如果沒有任何規則匹配，預設指派給 `IndestructibleAutoOps`。

If no rules match, defaults to `IndestructibleAutoOps`.

## 自動評論 (Automatic Comments)

當 Issue 或 PR 被自動指派後，系統會自動留言說明：
- 指派的維護者
- 決策原因
- 如何重新評估指派

When an Issue or PR is auto-assigned, the system automatically comments with:
- The assigned maintainer
- The reasoning for the decision
- How to request reassignment

## 自訂規則 (Customizing Rules)

要修改指派規則，請編輯 `.github/workflows/auto-assign.yml` 檔案中的決策邏輯。

To customize assignment rules, edit the decision logic in `.github/workflows/auto-assign.yml`.

### 新增團隊成員 (Adding Team Members)

1. 在 `teamMembers` 陣列中新增成員
2. 在 `labelMap` 或其他規則中指定對應的指派邏輯

```javascript
const teamMembers = ['IndestructibleAutoOps', 'NewMember'];

const labelMap = {
  'bug': 'IndestructibleAutoOps',
  'feature': 'NewMember',  // 新增的規則
  // ...
};
```

### 新增標籤規則 (Adding Label Rules)

在 `labelMap` 物件中新增標籤與維護者的對應關係：

```javascript
const labelMap = {
  'bug': 'IndestructibleAutoOps',
  'your-new-label': 'YourMaintainer',
  // ...
};
```

### 新增檔案規則 (Adding File Pattern Rules)

在 `filePatterns` 物件中新增檔案模式：

```javascript
const filePatterns = {
  'workflows': /\.github\/workflows\//,
  'your-pattern': /your-regex-pattern/,
  // ...
};
```

## 權限需求 (Required Permissions)

工作流程需要以下權限：
- `issues: write` - 用於指派 Issue 和新增評論
- `pull-requests: write` - 用於指派 PR 和新增評論

The workflow requires the following permissions:
- `issues: write` - To assign issues and add comments
- `pull-requests: write` - To assign PRs and add comments

## 疑難排解 (Troubleshooting)

### Issue/PR 沒有被自動指派

1. 檢查工作流程是否成功執行（在 Actions 頁面查看）
2. 確認 GITHUB_TOKEN 有正確的權限
3. 檢查指派的使用者是否有專案存取權限

### 想要變更指派

在 Issue 或 PR 中留言提及 @IndestructibleAutoOps 請求重新評估。

Comment on the Issue or PR and mention @IndestructibleAutoOps to request reassignment.

## 參考資料 (References)

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pozil/auto-assign-issue Action](https://github.com/pozil/auto-assign-issue)
- [GitHub Script Action](https://github.com/actions/github-script)
