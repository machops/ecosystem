# Security Policy — infra-base

## Reporting Vulnerabilities

If you discover a security vulnerability in this repository, please report it responsibly:

1. **DO NOT** create a public GitHub issue
2. Email: security@codevantaos.io
3. Include: repository name, description, reproduction steps, impact assessment

## Security Standards

| Standard | Status |
|---|---|
| SLSA Level | L3+ |
| SBOM Format | CycloneDX |
| Signing | Sigstore |
| Secret Scanning | Enabled |
| Dependency Scanning | Enabled |
| Container Scanning | Enabled |

## Compliance Frameworks

- SOC2-Type2
- ISO27001
- CIS-Benchmark
- NIST-CSF

## Supported Versions

| Version | Supported |
|---|---|
| Latest (main) | ✅ |
| Previous release | ✅ (security patches) |
| Older | ❌ |

## Response SLA

| Severity | Response Time | Resolution Target |
|---|---|---|
| Critical (P0) | 15 minutes | 4 hours |
| High (P1) | 1 hour | 24 hours |
| Medium (P2) | 4 hours | 7 days |
| Low (P3) | 24 hours | 30 days |

## Governance

This repository is governed by the [CodeVantaOS Governance Framework](https://github.com/codevantaos/.github/blob/main/GOVERNANCE.md).

- **Risk Level**: critical
- **URN**: `urn:codevantaos:repo:infra:base:v1`
- **Owner**: @infra-team
- **Security Contact**: @devsecops-team
