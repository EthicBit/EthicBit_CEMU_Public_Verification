# Independent Reproduction Checklist

## Reviewer Preparation
- [ ] I am using an environment separate from the original EthicBit development environment.
- [ ] I cloned the public repository independently.
- [ ] I checked out the declared branch, commit, or release tag.
- [ ] I inspected declared subjects.
- [ ] I inspected expected hashes.
- [ ] I inspected the reproducibility guide.
- [ ] I inspected the reproducibility extension receipt.

## Execution
- [ ] I ran `scripts/reproducibility/run_reproducibility_extension_e2e.sh`.
- [ ] The script completed without manual modification.
- [ ] The comparison status was PASS.
- [ ] The declared subject count matched the expected count.
- [ ] All declared subjects matched expected hashes.
- [ ] No mismatches were reported.
- [ ] I recorded environment fingerprint output.

## Reporting
- [ ] I completed `assurance/reproducibility/independent_reproduction_report.json`.
- [ ] I completed or signed `assurance/reproducibility/third_party_reproduction_attestation_template.json`.
- [ ] I recorded any deviations, dependencies, or local changes.
- [ ] I preserved the comparison report.
- [ ] I preserved the environment fingerprint.

## Claim Boundary
- [ ] I understand this process does not imply regulatory approval.
- [ ] I understand this process does not imply patent grant.
- [ ] I understand this process does not imply universal reproducibility.
- [ ] I understand this process applies only to declared subjects.

