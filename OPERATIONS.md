# ECO Platform Operations Manual

> **Status**: Production  
> **Owner**: platform-ops  
> **Last Updated**: 2026-02-26

---

## 不可更動規範（Immutable Operational Rules）

> 本段落為平台韌性基線的強制規範。任何修改須經 P0 審批流程，並附完整回歸 drill 報告。  
> 禁止在未完成以下審批程序的情況下，對本段落所定義之架構邊界進行任何形式的降級或繞過。

---

### Rule-01: EventBus Zone Resilience 不得降級

**規範**

任何導致 EventBus JetStream 跨 Zone 分散等級從 `full` 降至 `degraded` 或 `not_supported` 的變更，**必須被視為 P0 風險變更**，並強制執行以下程序：

| 步驟 | 要求 |
|------|------|
| 1. 變更申請 | 提交 PR，標記 `risk:P0` + `zone-resilience-change`，附降級原因與預期持續時間 |
| 2. 審批 | 需要 2 名 platform-ops 成員 approve，且至少 1 名為 on-call |
| 3. 回歸 drill | 變更後必須立即執行 `tests/drill-eventbus-zone.sh`，報告須作為 PR artifact 附上 |
| 4. 監控窗口 | 變更後 72 小時內持續監控 EventBus 健康狀態 |
| 5. 恢復計畫 | PR 內必須附明確的回復至 `full` 的時間表與操作步驟 |

**zone_resilience 等級定義**

| 等級 | 條件 | 允許狀態 |
|------|------|----------|
| `full` | Z≥3，3 pods 分散至 3 個不同 zone | 正常生產狀態 |
| `degraded(two_zones)` | Z=2，2:1 分布，maxSkew=1 | 僅允許短暫維護窗口（≤72h），需 P0 審批 |
| `not_supported` | Z=1，單 zone 叢集 | 禁止用於生產；僅允許非生產環境 |

**驗證指令**

```bash
bash tests/drill-eventbus-zone.sh
# 預期輸出: gate_result=PASS, zone_resilience=full
```

**當前基線**（2026-02-26 驗證）

- js-0 → asia-east1-b
- js-1 → asia-east1-a
- js-2 → asia-east1-c（PV: `eventbus-js2-pv-zone-c`，GCE PD: `eventbus-js2-zone-c`）

---

### Rule-02: PersistentVolume Zone 綁定不得靜默變更

**規範**

StatefulSet 的 PVC/PV zone 綁定決定了 pod 可排程的 zone。任何 PVC 刪除/重建操作，**必須明確指定目標 zone**，並驗證新 PV 的 `nodeAffinity.required` 符合預期。

禁止行為：
- 直接刪除 PVC 後讓 StorageClass 自動選擇 zone（可能破壞 zone 分散）
- 使用 `volume.kubernetes.io/selected-node` annotation 而不等待 PVC 進入 Pending 狀態再綁定

強制操作流程：
1. Scale down StatefulSet replicas
2. 刪除目標 PVC
3. 手動建立 PV（指定 `nodeAffinity` 至目標 zone）+ PVC（指定 `volumeName`）
4. Scale up StatefulSet
5. 執行 `drill-eventbus-zone.sh` 驗證

---

### Rule-03: Kyverno PolicyException 不得無限期存在

**規範**

所有 PolicyException 必須包含以下 annotations：

```yaml
eco.policy/expires: "YYYY-MM-DD"   # 必填，最長 90 天
eco.policy/owner: "<team>"          # 必填
eco.policy/issue: "<issue-url>"     # 必填
```

CI gate（`.github/workflows/policy-exception-expiry-gate.yml`）在每次 PR 時自動檢查到期日。過期 exception 導致 CI 失敗，阻斷 merge。

禁止行為：
- 無 `eco.policy/expires` annotation 的 PolicyException
- 延長到期日超過 90 天（需重新審批）
- 以大範圍 namespace exclude 取代 PolicyException

---

### Rule-04: Flagger Canary SLI 閾值不得放寬

**規範**

以下 SLI 閾值為生產最低標準，不得在未完成回歸 drill 的情況下放寬：

| 指標 | 閾值 | 方向 |
|------|------|------|
| `request-success-rate` | ≥99% | 不得降低 |
| `request-duration` (p99) | ≤200ms | 不得提高 |
| `failure_threshold` | 3 次 | 不得增加 |
| `analysis_interval` | 10s | 不得延長 |

任何閾值變更需附 `drill-flagger-rollback.sh` 執行報告，確認回滾機制在新閾值下仍然有效。

---

### Rule-05: 週期性演練不得停用或跳過

**規範**

`.github/workflows/weekly-chaos-drill.yml` 的 cron 排程（每週一 02:00 UTC）不得被停用、刪除或長期跳過。

若因叢集維護需要暫停：
- 最長暫停期：2 週
- 暫停期間必須建立 tracking issue（label: `drill-suspended`）
- 恢復後第一次手動觸發 `workflow_dispatch` 並確認 PASS

若 drill 連續 2 週失敗（GitHub Issues 顯示 2 張以上未關閉），自動升級為 P0 incident。

---

## 週期性演練排程

| Drill | 腳本 | 排程 | 報告 |
|-------|------|------|------|
| EventBus Cross-Zone Distribution | `tests/drill-eventbus-zone.sh` | 每週一 02:00 UTC | `tests/reports/drill-summary.json` + artifacts |
| Flagger Rollback | `tests/drill-flagger-rollback.sh` | 每週一 02:00 UTC | `tests/reports/drill-summary.json` + artifacts |

完整報告為 GitHub Actions artifacts（90 天保留）。`drill-summary.json` 保留最近 10 筆摘要，提交至 repo。

---

## 變更審批等級

| 等級 | 觸發條件 | 審批要求 |
|------|----------|----------|
| P0 | zone_resilience 降級、SLI 閾值放寬、drill 停用 | 2x platform-ops approve + 回歸 drill |
| P1 | PolicyException 新增/延長、PVC zone 變更 | 1x platform-ops approve + CI gate PASS |
| P2 | 一般配置變更 | 標準 PR review |
