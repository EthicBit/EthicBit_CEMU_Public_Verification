# Contributing to EthicBit_CEMU

## Branch governance

- `main` is the only canonical branch for delivery, audit, and release claims.
- `master` is frozen and must not receive pull requests.
- If a pull request is opened against `master`, close it and reopen against `main`.

## Pull request target

- Base branch must be `main`.
- Use feature branches (for example: `codex/<topic>`).

## Required checks

- The constitutional gate check must pass before merge:
  - Check name: `production-distributed-ready-final`
  - Workflow file: `.github/workflows/production-distributed-ready-final.yml`

## Minimal PR expectations

- Explain what changed and why.
- Link the affected artifact(s) or evidence file(s) when governance/audit behavior changes.
- Keep claims aligned with current state artifacts in `results/` and `artifacts/history/swarm/`.
