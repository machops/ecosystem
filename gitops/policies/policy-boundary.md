# ECO Base — Policy Engine Responsibility Boundary

## Division of Responsibility

### Kyverno (Native K8s mutate/validate/generate)

**Scope**: Simple, single-resource validation and mutation for ECO platform namespaces.

| Policy | Mode | Rule |
|--------|------|------|
| `disallow-latest-tag` | Enforce | No `:latest` image tag |
| `require-resource-limits` | Enforce | CPU + memory limits required |
| `require-non-root-user` | Audit → Enforce (30d) | `runAsNonRoot: true` |
| `require-eco-labels` | Audit → Enforce (60d) | `app`, `version`, `eco.platform` labels |
| `mutate-default-labels` | Mutate | Auto-inject `eco.platform` label |

### OPA Gatekeeper (Complex Rego logic, cross-resource, exception lists)

**Scope**: Complex conditional logic, cross-resource validation, exception allowlists.

| ConstraintTemplate | Mode | Rule |
|-------------------|------|------|
| `K8sPSPPrivilegedContainer` | Deny | No privileged containers (with exception namespace allowlist) |
| `K8sRequiredProbes` | Warn → Deny (30d) | liveness + readiness probes required |
| `K8sAllowedRepos` | Deny | Only approved registries (harbor, ghcr.io/indestructibleorg) |
| `K8sBlockNodePort` | Deny | No NodePort services in production namespaces |

## Audit → Enforce Progression

```
Day 0:   Deploy as Audit (measure violation rate)
Day 7:   Review violations, fix workloads
Day 14:  Switch to Warn (visible but non-blocking)
Day 30:  Switch to Enforce (blocking)
```

## Exception Mechanism

All Enforce policies support namespace-level exception via label:
```yaml
metadata:
  labels:
    policy.eco.platform/exempt: "true"
    policy.eco.platform/exempt-reason: "legacy-migration"
    policy.eco.platform/exempt-expires: "2026-04-01"
```

## Anti-Overlap Rules

1. If a rule can be expressed as simple pattern match → **Kyverno**
2. If a rule requires Rego logic, library reuse, or cross-resource → **Gatekeeper**
3. Never implement the same check in both engines
4. Privileged container check: **Gatekeeper only** (removed from Kyverno)
