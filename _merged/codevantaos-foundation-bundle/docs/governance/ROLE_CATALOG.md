# Role Catalog: DevOps & Supply Chain Security

| Role ID | Role Name | Responsibility | Tools |
|---------|-----------|----------------|-------|
| @MON | 監控告警工程師 | 偵測異常、自動觸發 Alert | Prometheus, Grafana, Loki |
| @SRE | 事件響應工程師 | Root Cause 分析、影響評估 | Jaeger, Tempo, Incident-Report |
| @OPS | DevOps 工程師 | 隔離問題、執行初步應對、Rollback | retry.mjs, automation-break-glass.yml |
| @SEC | 安全合規工程師 | 審核證據鏈、驗證簽章、Audit Log | Sigstore, Rekor, Dependency-Track |
| @DEV | 開發安全工程師 | 產生修復 Patch、生成新 PR、VEX | cosign, trivy, vex-generator |
| @QA | 測試與 QA 工程師 | 重新跑 CI/CD、驗證 SLSA L3+ | Gatekeeper, Kyverno, slsa-generator |
| @CAB | 變更諮詢委員會 | 審核 PR、同意合併、更新 Changelog | GitHub Branch Protection, CODEOWNERS |