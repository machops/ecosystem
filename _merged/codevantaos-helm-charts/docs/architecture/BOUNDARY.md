# Boundary Definition: CodeVantaOS－Helm Charts

## Core Responsibility
基礎設施即代碼 (IaC) 與 GitOps 部署定義。

## Boundary Context
- **ID**: codevantaos-helm-charts
- **URN**: urn:codevantaos:kb:code:infra:helm-charts:v1
- **Domain**: infra

## Interface Specification
### Inputs
- 雲端憑證
- 部署清單

### Outputs
- 雲端資源實體
- K8s 叢集狀態

## Governance Constraints
- 必須符合 Machine-First 治理規範。
- 所有變更必須通過 URN 驗證。
- 數據流必須具備證據鏈簽章。