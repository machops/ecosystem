# Central Repair Factory

This repository acts as a centralized CI/CD sandbox for Dependabot PRs from other repositories.

## Workflow

1. **Stuck PR Detection**: Client repos detect stuck Dependabot PRs and dispatch an event here.
2. **Isolation & Repair**: This repo checks out the PR, runs full validation (Trivy, Cosign, etc.).
3. **Outcome**:
   - **Success**: Pushes an empty commit to the original PR to trigger checks.
   - **Failure**: Notifies the original repo to close the PR.

## Setup

Ensure `REPAIR_FACTORY_PAT` is set in this repo's secrets with `repo` and `workflow` scopes.
