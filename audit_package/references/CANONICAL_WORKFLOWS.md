# CANONICAL WORKFLOWS

## Canonical operational workflows
- .github/workflows/official-periodic-audit.yml
- .github/workflows/verify-ceerv.yml
- .github/workflows/slsa-l4-final.yml
- .github/workflows/slsa-l4-operative-real.yml

## Operative / real support workflows
- .github/workflows/runtimeguard-l4-operative-real.yml
- .github/workflows/distributed-production-operative-real.yml
- .github/workflows/global-deployment-audit-operative-real.yml
- .github/workflows/global-regulatory-certification-operative-real.yml

## Baseline workflows
- .github/workflows/slsa-l4-baseline.yml
- .github/workflows/slsa-l4-operative.yml

## Negative workflows
- .github/workflows/runtimeguard-l4-negative-real.yml
- .github/workflows/production-distributed-ready-negative.yml

## Historical / disabled
- .github/workflows/slsa-build.disabled

## Precedence
1. *-final.yml
2. *-operative-real.yml
3. *-operative.yml
4. *-baseline.yml
5. *-negative.yml
6. disabled / historical
