# AEM-EVOLVE™ v1.4 Independent Reproduction Challenge

**Version:** v1.4.0
**Tag:** `v1.4.0`
**Date opened:** 2026-05-09
**Status:** OPEN — 0 external reports received

---

## What this is

An open invitation for any external party to independently reproduce the AEM-EVOLVE™ v1.4.0 full-stack verification results and submit a report.

---

## What to reproduce

Run the 14-check full-stack verifier against a fresh clone of `v1.4.0`:

```bash
git clone https://github.com/EthicBit/EthicBit_CEMU.git
cd EthicBit_CEMU
git checkout v1.4.0
pip install cryptography mlkem asyncpg
python3 demos/aem-evolve-multi-agent-api/tools/reproduction/verify_all_v1_4.py
```

Expected output:

```
FULL_STACK_VERIFICATION=PASS  (14/14)
  v1.1: 6/6  ·  v1.2: 2/2  ·  v1.3: 4/4  ·  v1.4: 2/2
```

---

## Optional: Docker reproduction

```bash
docker build -f Dockerfile.reproduction -t aem-evolve-v1-4 .
docker run --rm aem-evolve-v1-4
```

---

## What to include in your report

Use the template at `docs/reproduction/REPRODUCTION_REPORT_TEMPLATE.md`:

- Your name / organization (or pseudonym)
- OS, Python version, dependency versions
- Full output of `verify_all_v1_4.py`
- Any deviation from the expected output
- Any steps you had to add or change

---

## How to submit

Open a GitHub Issue titled: `[v1.4 Reproduction] <your-name-or-org>`

Or submit a pull request adding your report to:
`independent-reproductions/v1_4/<your-name>.md`

---

## Non-claims

```
EthicBit does not claim external reproductions have been received.
This challenge does not constitute a third-party audit.
Submission does not imply endorsement by the submitter.
```
