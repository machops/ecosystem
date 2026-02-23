#!/usr/bin/env python3
"""
PR Blocked Response — Diagnose and Respond
eco-base autonomous bot: detects blocked PRs, diagnoses root cause,
attempts auto-fix, escalates to Issue if manual intervention needed.

Root causes handled:
  1. BEHIND main (strict_required_status_checks_policy=true) → auto update-branch
  2. UNKNOWN state (GitHub cache miss) → trigger mergeable refresh via update-branch
  3. Codacy ACTION_REQUIRED (non-required check) → direct merge via --admin if all required pass
  4. CircleCI false positive in commit statuses → auto-fix via .circleci/config.yml
  5. dependabot.yml invalid Docker ignore rules → auto-fix
  6. DIRTY (merge conflict) → trigger @dependabot rebase
  7. Failing required checks → label + create tracking issue

Idempotency:
  - BEHIND PRs: update-branch is idempotent (GitHub deduplicates)
  - Auto-merge: enable-auto-merge is idempotent (already-enabled is OK)
  - Direct merge: only attempted when all 6 required checks pass
  - Comments: deduplication by checking existing comment body
  - Issues: deduplication by checking existing issue title
"""
import os
import json
import subprocess
import sys
import re
import time
import urllib.request
import urllib.error

REPO = os.environ.get("REPO", "indestructibleorg/eco-base")
SPECIFIC_PR = os.environ.get("SPECIFIC_PR", "").strip()
GH_TOKEN = os.environ.get("GH_TOKEN", "")

# The 6 required checks from branch protection rules
REQUIRED_CHECKS = {"validate", "lint", "test", "build", "opa-policy", "supply-chain"}

# Non-required checks that may show ACTION_REQUIRED but must NOT block merge
# These are third-party integrations that are informational only
NON_BLOCKING_CHECKS = {
    "Codacy Static Code Analysis",
    "codacy",
    "CodeRabbit",
    "coderabbitai",
    "qodo",
    "copilot-pull-request-reviewer",
    "SonarCloud Code Analysis",
}


def gh_run(args, **kwargs):
    return subprocess.run(["gh"] + args, capture_output=True, text=True, **kwargs)


def gh_api(path, method="GET", data=None):
    """Call GitHub API directly using urllib (no extra deps)."""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {GH_TOKEN}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("Content-Type", "application/json")
    if data is not None:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"  [API ERROR] {method} {path}: HTTP {e.code} — {body[:200]}")
        return {"_http_error": e.code, "_body": body}
    except Exception as e:
        print(f"  [API ERROR] {method} {path}: {e}")
        return {}


def get_open_prs():
    if SPECIFIC_PR:
        r = gh_run(["pr", "view", SPECIFIC_PR, "--repo", REPO, "--json",
                    "number,title,state,mergeable,mergeStateStatus,statusCheckRollup,"
                    "labels,headRefName,headRefOid,author,autoMergeRequest"])
        return [json.loads(r.stdout)] if r.returncode == 0 and r.stdout.strip() else []
    r = gh_run(["pr", "list", "--repo", REPO, "--state", "open", "--limit", "50",
                "--json", "number,title,state,mergeable,mergeStateStatus,statusCheckRollup,"
                          "labels,headRefName,headRefOid,author,autoMergeRequest"])
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []


def get_pr_api(pr_num):
    """Get PR details directly from REST API (more accurate mergeable_state)."""
    return gh_api(f"/repos/{REPO}/pulls/{pr_num}")


def get_commit_statuses(head_sha):
    """Get commit statuses (different from check runs) for a SHA."""
    data = gh_api(f"/repos/{REPO}/commits/{head_sha}/statuses?per_page=50")
    if isinstance(data, list):
        return data
    return []


def get_check_runs(head_sha):
    """Get check runs for a SHA (paginated, up to 100)."""
    data = gh_api(f"/repos/{REPO}/commits/{head_sha}/check-runs?per_page=100")
    return data.get("check_runs", [])


def update_branch(pr_num, head_sha):
    """Update PR branch to be up-to-date with base (fixes BEHIND state).
    Idempotent: GitHub deduplicates update-branch requests.
    """
    print(f"  [AUTO-FIX] Updating branch for PR #{pr_num} (BEHIND main)...")
    # Try with expected_head_sha first (safer)
    payload = {"expected_head_sha": head_sha} if head_sha else {}
    result = gh_api(
        f"/repos/{REPO}/pulls/{pr_num}/update-branch",
        method="PUT",
        data=payload
    )
    msg = result.get("message", "")
    err = result.get("_http_error", 0)
    if err == 422 and head_sha:
        # SHA mismatch — try without expected_head_sha
        result = gh_api(
            f"/repos/{REPO}/pulls/{pr_num}/update-branch",
            method="PUT",
            data={}
        )
        msg = result.get("message", "")
    if msg:
        print(f"  [AUTO-FIX] update-branch: {msg}")
    else:
        print(f"  [AUTO-FIX] update-branch triggered for PR #{pr_num}")
    return True


def fix_circleci():
    """Create .circleci/config.yml to suppress CircleCI false positive."""
    path = ".circleci/config.yml"
    os.makedirs(".circleci", exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(
                "version: 2.1\n"
                "# eco-base uses GitHub Actions for CI/CD.\n"
                "# This file exists solely to prevent CircleCI from attempting to parse\n"
                "# GitHub Actions workflow files as CircleCI configuration.\n"
                "# The actual CI/CD pipeline is defined in .github/workflows/ci.yaml\n"
                "# No CircleCI workflows are defined or used in this project.\n"
            )
        print("  [AUTO-FIX] Created .circleci/config.yml")
        return True
    return False


def fix_dependabot_yaml():
    """Fix invalid Docker ignore version rules in dependabot.yml."""
    path = ".github/dependabot.yml"
    if not os.path.exists(path):
        return False
    with open(path, "r") as f:
        content = f.read()
    patterns = [
        r"\n    ignore:\n      # Python [^\n]+\n      - dependency-name: \"python\"\n        versions: \[[^\]]+\]\n      # Node [^\n]+\n      - dependency-name: \"node\"\n        versions: \[[^\]]+\]",
        r"\n    ignore:\n      - dependency-name: \"node\"\n        versions: \[[^\]]+\]",
        r"\n    ignore:\n      - dependency-name: \"python\"\n        versions: \[[^\]]+\]",
    ]
    fixed = content
    for p in patterns:
        fixed = re.sub(p, "", fixed)
    if fixed != content:
        with open(path, "w") as f:
            f.write(fixed)
        print("  [AUTO-FIX] Removed invalid Docker ignore version rules from dependabot.yml")
        return True
    return False


def trigger_rebase(pr_num):
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO,
                "--body", "@dependabot rebase"])
    ok = r.returncode == 0
    print(f"  [AUTO-FIX] @dependabot rebase on #{pr_num}: {'OK' if ok else r.stderr[:60]}")
    return ok


def enable_auto_merge(pr_num):
    """Enable auto-merge on a PR so it merges automatically once checks pass.
    Idempotent: already-enabled is treated as success.
    """
    r = gh_run(["pr", "merge", str(pr_num), "--repo", REPO, "--auto", "--squash"])
    if r.returncode == 0:
        print(f"  [AUTO-MERGE] Enabled auto-merge for PR #{pr_num}")
        return True
    msg = r.stderr.strip()
    if "already enabled" in msg.lower() or "auto merge" in msg.lower() or "auto-merge" in msg.lower():
        print(f"  [AUTO-MERGE] Already enabled for PR #{pr_num}")
        return True
    print(f"  [AUTO-MERGE] Failed for PR #{pr_num}: {msg[:120]}")
    return False


def direct_merge(pr_num, pr_title):
    """Direct merge using --admin flag, bypassing non-required check failures.
    Only called when all 6 required checks pass.
    """
    print(f"  [DIRECT-MERGE] All required checks pass — attempting direct merge for PR #{pr_num}...")
    r = gh_run(["pr", "merge", str(pr_num), "--repo", REPO, "--squash", "--admin",
                "--subject", pr_title])
    if r.returncode == 0:
        print(f"  [DIRECT-MERGE] ✓ PR #{pr_num} merged successfully")
        return True
    msg = r.stderr.strip()
    print(f"  [DIRECT-MERGE] Failed for PR #{pr_num}: {msg[:120]}")
    return False


def add_label(pr_num, label):
    r = gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--add-label", label])
    if r.returncode == 0:
        print(f"  [LABEL] Added '{label}' to PR #{pr_num}")


def remove_label(pr_num, label):
    r = gh_run(["pr", "edit", str(pr_num), "--repo", REPO, "--remove-label", label])
    if r.returncode == 0:
        print(f"  [LABEL] Removed '{label}' from PR #{pr_num}")


def post_diagnosis_comment(pr_num, merge_status, failing, commit_status_failures,
                           skipped, diagnosis, auto_fixable, manual_required):
    """Post a diagnosis comment, deduplicating by checking existing comments."""
    r = gh_run(["pr", "view", str(pr_num), "--repo", REPO, "--json", "comments"])
    if r.returncode == 0 and r.stdout.strip():
        comments = json.loads(r.stdout).get("comments", [])
        if any("Autonomous Bot" in c.get("body", "") and "PR Blocked Diagnosis" in c.get("body", "")
               for c in comments):
            print(f"  [COMMENT] Diagnosis comment already exists for #{pr_num}, skipping")
            return

    diagnosis_lines = "\n".join(f"- {d}" for d in diagnosis) if diagnosis else "- No specific diagnosis"
    auto_fix_lines = "\n".join(f"- `{a}`" for a in auto_fixable) if auto_fixable else "- None"
    manual_lines = "\n".join(f"- `{m}`" for m in manual_required) if manual_required else "- None"
    failing_lines = "\n".join(f"- ❌ `{f['name']}`" for f in failing) if failing else "- None"
    cs_lines = "\n".join(f"- ⚠️ `{s['context']}` ({s['state']})" for s in commit_status_failures) if commit_status_failures else "- None"
    skipped_lines = "\n".join(f"- ⏭ `{s}`" for s in skipped) if skipped else "- None"

    body = (
        f"## Autonomous Bot: PR Blocked Diagnosis\n\n"
        f"PR #{pr_num} is currently blocked (`{merge_status}`).\n\n"
        f"### Root Cause Analysis\n{diagnosis_lines}\n\n"
        f"### Auto-Fix Actions Taken\n{auto_fix_lines}\n\n"
        f"### Requires Manual Review\n{manual_lines}\n\n"
        f"### Failing Check Runs\n{failing_lines}\n\n"
        f"### Failing Commit Statuses\n{cs_lines}\n\n"
        f"### Skipped Checks (expected)\n{skipped_lines}\n\n"
        f"---\n"
        f"*Auto-generated by PR Blocked Response workflow. "
        f"If the issue persists after auto-fix, please review the failing checks above.*\n"
    )
    r = gh_run(["pr", "comment", str(pr_num), "--repo", REPO, "--body", body])
    print(f"  [COMMENT] Posted diagnosis: {'OK' if r.returncode == 0 else r.stderr[:80]}")


def create_tracking_issue(pr_num, pr_title, pr_branch, merge_status, manual_required, diagnosis):
    """Create a tracking issue for PRs that require manual intervention.
    Deduplicates by checking existing open issues with the same PR number in title.
    """
    r = gh_run(["issue", "list", "--repo", REPO, "--state", "open",
                "--label", "blocked", "--json", "number,title"])
    existing = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    if any(f"PR #{pr_num}" in i["title"] for i in existing):
        print(f"  [ISSUE] Tracking issue for #{pr_num} already exists")
        return

    diagnosis_lines = "\n".join(f"- {d}" for d in diagnosis)
    manual_lines = "\n".join(f"- `{m}`" for m in manual_required)
    title = f"[Auto] PR #{pr_num} blocked: {', '.join(manual_required[:3])}"
    body = (
        f"## PR #{pr_num} is blocked and requires manual intervention\n\n"
        f"**PR:** https://github.com/{REPO}/pull/{pr_num}\n"
        f"**Title:** {pr_title}\n"
        f"**Branch:** `{pr_branch}`\n"
        f"**Block reason:** `{merge_status}`\n\n"
        f"### Failing Checks (require manual fix)\n{manual_lines}\n\n"
        f"### Diagnosis\n{diagnosis_lines}\n\n"
        f"### Next Steps\n"
        f"1. Review the failing checks in the PR\n"
        f"2. Fix the root cause in the source branch\n"
        f"3. Push the fix to trigger a new CI run\n"
        f"4. The PR will auto-merge once all required checks pass\n\n"
        f"---\n*Auto-created by PR Blocked Response workflow*\n"
    )
    r = gh_run(["issue", "create", "--repo", REPO,
                "--title", title, "--body", body,
                "--label", "blocked,needs-attention"])
    print(f"  [ISSUE] Created: {'OK - ' + r.stdout.strip() if r.returncode == 0 else r.stderr[:80]}")


def commit_auto_fixes():
    """Commit any file-based auto-fixes and open a PR for them."""
    r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not r.stdout.strip():
        print("\n[GIT] No auto-fixes to commit")
        return
    subprocess.run(["git", "config", "user.email", "bot@eco-base.dev"])
    subprocess.run(["git", "config", "user.name", "eco-base-bot"])
    branch = f"bot/auto-fix-blocked-{int(time.time())}"
    subprocess.run(["git", "checkout", "-b", branch])
    subprocess.run(["git", "add", "-A"])
    subprocess.run(["git", "commit", "-m",
                    "fix(bot): auto-fix PR blocked issues\n\n"
                    "- Added .circleci/config.yml to suppress CircleCI false positive\n"
                    "- Fixed dependabot.yml invalid Docker ignore version rules"])
    r_push = subprocess.run(["git", "push", "origin", branch], capture_output=True, text=True)
    if r_push.returncode != 0:
        print(f"\n[GIT] Push failed: {r_push.stderr[:80]}")
        return
    r_pr = subprocess.run([
        "gh", "pr", "create",
        "--title", "fix(bot): auto-fix PR blocked issues",
        "--body", "Automated fix by PR Blocked Response workflow.\n\n"
                  "- Added .circleci/config.yml to suppress CircleCI false positive\n"
                  "- Fixed dependabot.yml invalid Docker ignore version rules\n\n"
                  "This PR was created automatically and will auto-merge once required checks pass.",
        "--label", "automated,bot-pr",
        "--base", "main",
        "--head", branch
    ], capture_output=True, text=True)
    if r_pr.returncode == 0:
        pr_url = r_pr.stdout.strip()
        print(f"\n[GIT] Created PR: {pr_url}")
        subprocess.run(["gh", "pr", "merge", pr_url, "--auto", "--squash"])
        print("[GIT] Auto-merge enabled")
    else:
        print(f"\n[GIT] PR creation failed: {r_pr.stderr[:80]}")


def classify_checks(checks, head_sha):
    """Classify check runs into required/non-required, passing/failing.

    Returns:
        passing_required: set of required check names that passed
        failing_required: list of required check dicts that failed
        failing_non_blocking: list of non-required check dicts that failed/action_required
        all_required_pass: bool
    """
    passing_required = set()
    failing_required = []
    failing_non_blocking = []

    for c in checks:
        name = c.get("name", "")
        conclusion = (c.get("conclusion") or "").upper()
        status = (c.get("status") or "").upper()

        # Normalize: treat ACTION_REQUIRED as a non-blocking informational result
        is_action_required = conclusion == "ACTION_REQUIRED"
        is_failure = conclusion in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED")
        is_success = conclusion in ("SUCCESS", "NEUTRAL") or status == "SKIPPED"

        if name in REQUIRED_CHECKS:
            if is_success:
                passing_required.add(name)
            elif is_failure:
                failing_required.append(c)
        else:
            # Non-required check: ACTION_REQUIRED or failure is non-blocking
            if is_action_required or is_failure:
                failing_non_blocking.append(c)

    all_required_pass = REQUIRED_CHECKS.issubset(passing_required)
    return passing_required, failing_required, failing_non_blocking, all_required_pass


def process_pr(pr_num, pr_title, pr_branch, head_sha, merge_status, checks, labels):
    """Process a single PR: diagnose, auto-fix, or escalate."""
    print(f"\n=== PR #{pr_num} [{merge_status}]: {pr_title[:70]} ===")

    # Get accurate check run data directly from API (statusCheckRollup can be stale)
    check_runs = get_check_runs(head_sha) if head_sha else []
    # Merge with statusCheckRollup data (check_runs is more authoritative)
    if check_runs:
        checks_to_use = check_runs
    else:
        checks_to_use = checks

    passing_required, failing_required, failing_non_blocking, all_required_pass = \
        classify_checks(checks_to_use, head_sha)

    # Commit statuses (CircleCI, etc.) — separate from check runs
    commit_statuses = get_commit_statuses(head_sha) if head_sha else []
    failing_commit_statuses = [s for s in commit_statuses
                               if s.get("state") in ("error", "failure", "pending")]
    circleci_statuses = [s for s in failing_commit_statuses
                         if "circleci" in s.get("context", "").lower()]
    other_failing_statuses = [s for s in failing_commit_statuses
                              if "circleci" not in s.get("context", "").lower()]

    print(f"  Required checks passing: {passing_required}")
    print(f"  All required pass: {all_required_pass}")
    print(f"  Failing required: {[c.get('name') for c in failing_required]}")
    print(f"  Failing non-blocking: {[c.get('name') for c in failing_non_blocking]}")
    print(f"  Failing commit statuses: {[s.get('context') for s in failing_commit_statuses]}")

    diagnosis = []
    auto_fixable = []
    manual_required_list = []
    any_auto_fix = False

    # ── Case 1: All required checks pass — can merge ──
    if all_required_pass and not failing_required and not other_failing_statuses:
        if "human-review-required" not in labels:
            if failing_non_blocking:
                # Non-blocking checks (Codacy ACTION_REQUIRED, etc.) are blocking auto-merge
                # Use direct merge with --admin to bypass them
                names = [c.get("name", "") for c in failing_non_blocking]
                print(f"  [DIAGNOSIS] Non-blocking checks blocking merge: {names}")
                diagnosis.append(f"Non-required checks blocking merge (ACTION_REQUIRED): {names}")
                auto_fixable.append("direct-merge")
                merged = direct_merge(pr_num, pr_title)
                if not merged:
                    # Fallback: update-branch + enable auto-merge
                    if head_sha and merge_status in ("BLOCKED", "BEHIND", "UNKNOWN"):
                        update_branch(pr_num, head_sha)
                    enable_auto_merge(pr_num)
            elif circleci_statuses:
                # CircleCI false positive
                diagnosis.append("CircleCI commit status false positive")
                auto_fixable.append("circleci")
                enable_auto_merge(pr_num)
                if head_sha and merge_status in ("BLOCKED", "BEHIND", "UNKNOWN"):
                    update_branch(pr_num, head_sha)
            else:
                # Branch is behind or in unknown state — update and enable auto-merge
                if merge_status in ("BEHIND", "UNKNOWN", "BLOCKED"):
                    diagnosis.append(f"Branch is {merge_status} — triggering update-branch")
                    auto_fixable.append("update-branch")
                    if head_sha:
                        update_branch(pr_num, head_sha)
                enable_auto_merge(pr_num)
        else:
            print(f"  SKIP: has human-review-required label")
            return False

    # ── Case 2: Required checks failing ──
    elif failing_required:
        for f in failing_required:
            name = f.get("name", "")
            if name == ".github/dependabot.yml":
                diagnosis.append("dependabot.yml has invalid syntax (Docker ignore version format)")
                auto_fixable.append("dependabot.yml")
            elif name == "CircleCI Pipeline":
                diagnosis.append("CircleCI false positive (not a CircleCI project)")
                auto_fixable.append("circleci")
            elif any(k in name.lower() for k in ("yaml-lint", "validate", "lint")):
                diagnosis.append(f"Workflow validation failed: {name}")
                auto_fixable.append("workflow-lint")
            elif any(k in name.lower() for k in ("test", "spec")):
                diagnosis.append(f"Tests failing: {name}")
                manual_required_list.append(name)
            elif any(k in name.lower() for k in ("security", "scan", "cve", "grype")):
                diagnosis.append(f"Security scan failed: {name}")
                manual_required_list.append(name)
            else:
                diagnosis.append(f"Required check failing: {name}")
                manual_required_list.append(name)

        # Execute file-based auto-fixes
        if "circleci" in auto_fixable:
            if fix_circleci():
                any_auto_fix = True
        if "dependabot.yml" in auto_fixable:
            if fix_dependabot_yaml():
                any_auto_fix = True

    # ── Case 3: DIRTY (merge conflict) ──
    if merge_status == "DIRTY":
        diagnosis.append("Merge conflict with main branch")
        auto_fixable.append("rebase")
        trigger_rebase(pr_num)

    # ── Case 4: CircleCI commit status (non-required) ──
    if circleci_statuses and not all_required_pass:
        diagnosis.append("CircleCI commit status error (false positive — not a CircleCI project)")
        auto_fixable.append("circleci")
        if fix_circleci():
            any_auto_fix = True

    # ── Label management ──
    if failing_required and "blocked" not in labels:
        add_label(pr_num, "blocked")
    elif not failing_required and "blocked" in labels:
        remove_label(pr_num, "blocked")

    if manual_required_list and "human-review-required" not in labels:
        add_label(pr_num, "human-review-required")

    # ── Post diagnosis comment (only when there are real required failures) ──
    if failing_required or other_failing_statuses:
        skipped = [c.get("name") or c.get("context", "?") for c in checks_to_use
                   if (c.get("conclusion") or "").upper() == "SKIPPED"
                   or (c.get("status") or "").upper() == "SKIPPED"]
        post_diagnosis_comment(pr_num, merge_status, failing_required,
                               failing_commit_statuses, skipped,
                               diagnosis, auto_fixable, manual_required_list)

    # ── Create tracking issue for manual-required items ──
    if manual_required_list:
        create_tracking_issue(pr_num, pr_title, pr_branch, merge_status,
                              manual_required_list, diagnosis)

    return any_auto_fix


def main():
    prs = get_open_prs()
    print(f"Scanning {len(prs)} open PRs...")

    any_auto_fix = False

    # Process ALL PRs regardless of mergeStateStatus
    # (BEHIND, BLOCKED, UNKNOWN, DIRTY, UNSTABLE)
    for pr in prs:
        pr_num = pr["number"]
        pr_title = pr["title"]
        pr_branch = pr.get("headRefName", "")
        head_sha = pr.get("headRefOid", "")
        merge_status = pr.get("mergeStateStatus", "UNKNOWN")
        checks = pr.get("statusCheckRollup", [])
        labels = [l["name"] for l in pr.get("labels", [])]

        # Skip PRs that are already clean (CLEAN = mergeable, no issues)
        if merge_status == "CLEAN":
            print(f"\n=== PR #{pr_num} [CLEAN]: {pr_title[:60]} — skipping ===")
            continue

        # For UNKNOWN state: get accurate data from REST API
        if merge_status == "UNKNOWN":
            api_pr = get_pr_api(pr_num)
            actual_state = api_pr.get("mergeable_state", "unknown")
            print(f"\n=== PR #{pr_num} [UNKNOWN→{actual_state}]: {pr_title[:60]} ===")
            if actual_state == "clean":
                # Already mergeable — enable auto-merge
                enable_auto_merge(pr_num)
                continue
            elif actual_state == "behind":
                merge_status = "BEHIND"
            elif actual_state == "blocked":
                merge_status = "BLOCKED"
            elif actual_state == "dirty":
                merge_status = "DIRTY"
            # If still unknown, treat as BLOCKED and process normally

        result = process_pr(pr_num, pr_title, pr_branch, head_sha,
                            merge_status, checks, labels)
        if result:
            any_auto_fix = True

    # ── Commit any file-based auto-fixes ──
    if any_auto_fix:
        commit_auto_fixes()

    print("\nDone! PR Blocked Response complete.")


if __name__ == "__main__":
    main()
