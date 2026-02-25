# Phase 3 Deployment — OPA/Kyverno + Prometheus/Grafana/Loki + KEDA/Flagger

**Deployed**: 2026-02-26T06:20 (UTC+8)  
**Cluster**: eco-production | asia-east1 | GKE v1.34.3

---

## Layer 3 — Policy & Admission Control

### Kyverno v1.17.1 (kyverno/kyverno v3.7.1)
| Pod | Status |
|-----|--------|
| `kyverno-admission-controller` | Running |
| `kyverno-background-controller` | Running |
| `kyverno-cleanup-controller` | Running |
| `kyverno-reports-controller` | Running |
| CRDs | 20 |

### OPA Gatekeeper v3.21.1
| Pod | Status |
|-----|--------|
| `gatekeeper-audit` | Running |
| `gatekeeper-controller-manager` | Running |
| CRDs | 17 |

---

## Layer 4 — Observability Stack

### kube-prometheus-stack v0.89.0 (chart 82.4.0)
| Component | Pods | Status |
|-----------|------|--------|
| Prometheus | 1 | Running (2/2) |
| Grafana | 1 | Running (3/3) |
| AlertManager | 1 | Running (2/2) |
| Node Exporter | 6 (DaemonSet) | Running |
| kube-state-metrics | 1 | Running |
| Operator | 1 | Running |
| Admin Password | `Eco@Grafana2026` (GitHub Secret: `GRAFANA_ADMIN_PASSWORD`) |
| Retention | 15d |
| Storage | 20Gi (standard-rwo) |

### Loki 3.6.5 (chart 6.53.0)
| Component | Status |
|-----------|--------|
| `loki-0` (SingleBinary) | Running (2/2) |
| `loki-gateway` | Running |
| `loki-results-cache` | Running |
| Storage | 10Gi (standard-rwo) |
| Grafana URL | `http://loki-gateway.monitoring.svc.cluster.local/` |

### Promtail 3.5.1 (chart 6.17.1)
| Component | Status |
|-----------|--------|
| DaemonSet (6 nodes) | Running |
| Push URL | `http://loki-gateway.monitoring.svc.cluster.local/loki/api/v1/push` |

---

## Layer 5 — Autoscaling & Progressive Delivery

### KEDA 2.19.0
| Pod | Status |
|-----|--------|
| `keda-operator` | Running |
| `keda-operator-metrics-apiserver` | Running |
| `keda-admission-webhooks` | Running |
| CRDs | 6 (ScaledObject, ScaledJob, TriggerAuthentication, etc.) |

### Flagger 1.42.0
| Pod | Status |
|-----|--------|
| `flagger` | Running |
| Mesh Provider | kubernetes |
| Metrics Server | `http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090` |
| CRDs | 3 (Canary, MetricTemplate, AlertProvider) |

---

## Helm Releases Summary (All Deployed)

| Release | Namespace | Chart | App Version |
|---------|-----------|-------|-------------|
| argocd | argocd | argo-cd-9.4.4 | v3.3.2 |
| harbor | harbor | harbor-1.18.2 | 2.14.2 |
| kyverno | kyverno | kyverno-3.7.1 | v1.17.1 |
| gatekeeper | gatekeeper-system | gatekeeper-3.21.1 | v3.21.1 |
| prometheus | monitoring | kube-prometheus-stack-82.4.0 | v0.89.0 |
| loki | monitoring | loki-6.53.0 | 3.6.5 |
| promtail | monitoring | promtail-6.17.1 | 3.5.1 |
| keda | keda | keda-2.19.0 | 2.19.0 |
| flagger | flagger-system | flagger-1.42.0 | 1.42.0 |
