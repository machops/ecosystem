# Boundary Definition: CodeVantaOS－Security Scan Service

## Core Responsibility
安全、審計、策略驗證與合規性監控。

## Boundary Context
- **ID**: codevantaos-security-scan-service
- **URN**: urn:codevantaos:kb:code:governance:security-scan-service:v1
- **Domain**: governance

## Interface Specification
### Inputs
- 操作日誌
- 策略定義

### Outputs
- 合規報告
- 准入決策

## Governance Constraints
- 必須符合 Machine-First 治理規範。
- 所有變更必須通過 URN 驗證。
- 數據流必須具備證據鏈簽章。