# 禁用 Kubernetes 多文檔驗證 (--- 分隔符)

如果你想要禁用對 YAML `---` 文檔分隔符的支持（Kubernetes 多文檔格式），按照以下步驟：

## 方案 1: 修改驗證器 (推薦)

編輯 `.claude/hooks/pre-commit-validator.sh`

找到這一部分 (大約在 105-120 行):

```bash
# 使用 Python 驗證 (支持多文檔 YAML，如 Kubernetes)
if ! python3 << EOF 2>&1 > /tmp/yaml_error.tmp
import yaml
import sys
try:
    with open('$file', 'r') as f:
        # 支持多文檔 YAML (Kubernetes 使用 --- 分隔符)
        yaml.safe_load_all(f.read())
except yaml.YAMLError as e:
    print(f"YAML Error: {e}")
    sys.exit(1)
EOF
```

**改為**:

```bash
# 使用 Python 驗證 (禁用多文檔 YAML 支持)
if ! python3 << EOF 2>&1 > /tmp/yaml_error.tmp
import yaml
import sys
try:
    with open('$file', 'r') as f:
        # 單一文檔 YAML 驗證 (禁用 --- 分隔符)
        yaml.safe_load(f.read())
except yaml.YAMLError as e:
    print(f"YAML Error: {e}")
    sys.exit(1)
EOF
```

**改變**: `yaml.safe_load_all()` → `yaml.safe_load()`

## 方案 2: 分離 Kubernetes 文件

將 Kubernetes YAML 文件排除在驗證之外:

編輯 `.claude/config/format-validation.json`:

```json
{
  "excludePaths": [
    "node_modules/**",
    ".git/**",
    ".next/**",
    "dist/**",
    "build/**",
    ".cache/**",
    "coverage/**",
    "infrastructure/kustomize/**",  // 新增: 排除 Kubernetes 文件
    "**/*.k8s.yaml"
  ]
}
```

## 方案 3: 創建獨立的 Kubernetes 驗證器

保持 YAML 驗證簡單，為 Kubernetes 創建單獨的驗證:

```bash
# 新文件: .claude/hooks/validate-k8s-yaml.sh

#!/bin/bash
echo "Validating Kubernetes YAML files..."

find . -path "./infrastructure/kustomize" -name "*.yaml" -o -name "*.yml" | while read file; do
  # Kubernetes 多文檔支持
  python3 << EOF
import yaml
with open('$file') as f:
    yaml.safe_load_all(f.read())
EOF
done

echo "✅ Kubernetes validation complete"
```

## 實施步驟

### 如果你選擇方案 1:
```bash
# 編輯文件
vim .claude/hooks/pre-commit-validator.sh

# 修改 yaml.safe_load_all() 為 yaml.safe_load()

# 重新運行驗證
bash .claude/hooks/pre-commit-validator.sh
```

### 如果你選擇方案 2:
```bash
# 編輯配置
vim .claude/config/format-validation.json

# 添加 "infrastructure/kustomize/**" 到 excludePaths

# 重新運行驗證
bash .claude/hooks/pre-commit-validator.sh
```

### 如果你選擇方案 3:
```bash
# 使用兩個分離的驗證器
bash .claude/hooks/pre-commit-validator.sh     # 通用驗證
bash .claude/hooks/validate-k8s-yaml.sh        # Kubernetes 驗證
```

## 建議

| 方案 | 優點 | 缺點 |
|------|------|------|
| **方案 1** | 簡單，單一驗證器 | 禁用了 K8s 多文檔 |
| **方案 2** | 保持 K8s 文件，簡化驗證 | 不驗證 K8s 文件 |
| **方案 3** | 分離驗證，最靈活 | 需要運行兩個命令 |

**推薦:** 方案 2 - 保持 Kubernetes 文件有效，但不強制驗證 YAML 多文檔格式

## 實施方案 2 (推薦)

```bash
# 1. 備份原配置
cp .claude/config/format-validation.json .claude/config/format-validation.json.bak

# 2. 編輯配置
vim .claude/config/format-validation.json

# 3. 在 excludePaths 中添加:
"infrastructure/kustomize/**"

# 4. 驗證
bash .claude/hooks/pre-commit-validator.sh
```

完成後，Kubernetes YAML 文件將被驗證器跳過，但其他所有文件仍會被驗證。

---

需要幫助? 運行:
```bash
bash .claude/hooks/pre-commit-validator.sh --help
```
