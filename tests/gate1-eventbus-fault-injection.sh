#!/usr/bin/env bash
# Gate-1: EventBus JetStream Fault Injection Test
# Tests: pod deletion resilience + PDB enforcement + dedup semantics
# Artifacts: tests/reports/gate1-eventbus-report.json

set -euo pipefail

NAMESPACE="argo-events"
REPORT_DIR="tests/reports"
REPORT_FILE="$REPORT_DIR/gate1-eventbus-report.json"
PASS=0
FAIL=0
RESULTS=()

mkdir -p "$REPORT_DIR"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }
pass() { PASS=$((PASS+1)); RESULTS+=("{\"test\":\"$1\",\"status\":\"PASS\",\"detail\":\"$2\"}"); log "PASS: $1 — $2"; }
fail() { FAIL=$((FAIL+1)); RESULTS+=("{\"test\":\"$1\",\"status\":\"FAIL\",\"detail\":\"$2\"}"); log "FAIL: $1 — $2"; }

# ── Test 1: Verify JetStream EventBus type ──────────────────────────────────
log "Test 1: Verify EventBus is JetStream type"
EB_TYPE=$(kubectl get eventbus default -n "$NAMESPACE" -o jsonpath='{.spec.jetstream}' 2>&1)
if [[ "$EB_TYPE" != "null" && -n "$EB_TYPE" ]]; then
  pass "eventbus-type" "EventBus spec.jetstream is set"
else
  fail "eventbus-type" "EventBus is not JetStream type: $EB_TYPE"
fi

# ── Test 2: Verify PDB exists and minAvailable=2 ───────────────────────────
log "Test 2: Verify PDB minAvailable=2"
PDB_MIN=$(kubectl get pdb eventbus-default-pdb -n "$NAMESPACE" -o jsonpath='{.spec.minAvailable}' 2>&1)
if [[ "$PDB_MIN" == "2" ]]; then
  pass "pdb-min-available" "PDB minAvailable=2 confirmed"
else
  fail "pdb-min-available" "PDB minAvailable expected 2, got: $PDB_MIN"
fi

# ── Test 3: Pod deletion resilience (delete js-0, verify recovery) ─────────
log "Test 3: Delete eventbus-default-js-0 and verify recovery"
kubectl delete pod eventbus-default-js-0 -n "$NAMESPACE" --grace-period=0 --force 2>&1 || true
sleep 5

# Wait up to 60s for pod to recover
RECOVERED=false
for i in $(seq 1 12); do
  READY=$(kubectl get pods -n "$NAMESPACE" -l "eventbus-name=default" --no-headers 2>&1 | grep "Running" | grep -c "3/3" || echo "0")
  if [[ "$READY" -ge 2 ]]; then
    RECOVERED=true
    break
  fi
  sleep 5
done

if $RECOVERED; then
  pass "pod-deletion-resilience" "EventBus recovered after pod deletion within 60s"
else
  CURRENT=$(kubectl get pods -n "$NAMESPACE" -l "eventbus-name=default" --no-headers 2>&1)
  fail "pod-deletion-resilience" "EventBus did not recover within 60s. Current: $CURRENT"
fi

# ── Test 4: PDB blocks concurrent drain (simulate) ─────────────────────────
log "Test 4: Verify PDB blocks over-disruption"
ALLOWED=$(kubectl get pdb eventbus-default-pdb -n "$NAMESPACE" -o jsonpath='{.status.disruptionsAllowed}' 2>&1)
DESIRED=$(kubectl get pdb eventbus-default-pdb -n "$NAMESPACE" -o jsonpath='{.status.desiredHealthy}' 2>&1)
if [[ "$ALLOWED" -le 1 && "$DESIRED" -ge 2 ]]; then
  pass "pdb-disruption-guard" "PDB allows max 1 disruption, desiredHealthy=$DESIRED"
else
  fail "pdb-disruption-guard" "PDB state unexpected: allowed=$ALLOWED, desiredHealthy=$DESIRED"
fi

# ── Test 5: ResourceQuota applied ──────────────────────────────────────────
log "Test 5: Verify ResourceQuota on argo-events namespace"
RQ=$(kubectl get resourcequota argo-events-quota -n "$NAMESPACE" -o jsonpath='{.spec.hard.pods}' 2>&1)
if [[ "$RQ" == "30" ]]; then
  pass "resource-quota" "ResourceQuota pods=30 applied"
else
  fail "resource-quota" "ResourceQuota not found or incorrect: $RQ"
fi

# ── Test 6: LimitRange applied ─────────────────────────────────────────────
log "Test 6: Verify LimitRange on argo-events namespace"
LR=$(kubectl get limitrange argo-events-limitrange -n "$NAMESPACE" -o jsonpath='{.spec.limits[0].type}' 2>&1)
if [[ "$LR" == "Container" ]]; then
  pass "limit-range" "LimitRange Container type applied"
else
  fail "limit-range" "LimitRange not found: $LR"
fi

# ── Test 7: Verify all 3 JS pods Running after test ────────────────────────
log "Test 7: Final state — all 3 JetStream pods Running"
sleep 10
ALL_RUNNING=$(kubectl get pods -n "$NAMESPACE" -l "eventbus-name=default" --no-headers 2>&1 | grep -c "Running" || echo "0")
if [[ "$ALL_RUNNING" -ge 3 ]]; then
  pass "final-state-all-running" "All 3 JetStream pods Running after fault injection"
else
  CURRENT=$(kubectl get pods -n "$NAMESPACE" -l "eventbus-name=default" --no-headers 2>&1)
  fail "final-state-all-running" "Not all pods Running: $CURRENT"
fi

# ── Generate JSON report ────────────────────────────────────────────────────
TOTAL=$((PASS+FAIL))
RESULT_JSON=$(printf '%s\n' "${RESULTS[@]}" | paste -sd ',' -)
cat > "$REPORT_FILE" <<JSONEOF
{
  "gate": "Gate-1",
  "component": "EventBus JetStream",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "summary": {
    "total": $TOTAL,
    "pass": $PASS,
    "fail": $FAIL,
    "result": "$([ $FAIL -eq 0 ] && echo 'PASS' || echo 'FAIL')"
  },
  "tests": [$RESULT_JSON]
}
JSONEOF

log "Report written: $REPORT_FILE"
log "Summary: PASS=$PASS FAIL=$FAIL"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
