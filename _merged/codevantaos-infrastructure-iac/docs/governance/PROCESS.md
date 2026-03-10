# Standard Operating Procedure: Incident to Merge

## 1. 發生問題 (Incident)
- **Action**: 系統監控工具偵測異常。
- **Owner**: @MON

## 2. 評估問題 (Assessment)
- **Action**: 分析 Root Cause，評估影響範圍。
- **Owner**: @SRE

## 3. 執行初步應對 (Mitigation)
- **Action**: 隔離問題，啟動 Break-Glass。
- **Owner**: @OPS

## 4. 稽核問題 (Audit)
- **Action**: 審核證據鏈 (Run-Manifest, SBOM)。
- **Owner**: @SEC

## 5. 修復問題 (Remediation)
- **Action**: 產生修復 Patch，生成新 PR。
- **Owner**: @DEV

## 6. 驗證修復 (Verification)
- **Action**: 驗證簽章與 SLSA L3+ 合規性。
- **Owner**: @QA

## 7. 同意合併 (Approval)
- **Action**: 審核 PR 並自動合併。
- **Owner**: @CAB