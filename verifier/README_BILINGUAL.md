# ETHICBIT / CEERV / CEMU — Verifier Pack v10.0 (Bilingual)

**Purpose / Propósito:** one-command baseline verification adapted to the current factual repo tree. / verificación baseline en un comando adaptada al árbol factual actual del repo.

## Expected output / Salida esperada

**EN:** the verifier should produce explicit PASS_BASELINE / ALLOW_BASELINE / FAIL markers.  
**ES:** el verificador debe producir marcadores explícitos PASS_BASELINE / ALLOW_BASELINE / FAIL.

## Minimum expected baseline lines / Líneas mínimas baseline esperadas
- `PASS_BASELINE: SLSA_L4_BASELINE_EXECUTABLE`
- `ALLOW_BASELINE: RUNTIMEGUARD_L4_BASELINE_EXECUTABLE`
- `PASS_BASELINE: MULTI_JURISDICTION_BASELINE_EXECUTABLE`
- `PASS_BASELINE: DISTRIBUTED_READINESS_BASELINE_EXECUTABLE`
- `PASS_BASELINE: CEERV_PACKAGE_INTEGRITY_STRUCTURE_PRESENT`
- `PASS_BASELINE: CANONICAL_PUBLICATION_STRUCTURE_PRESENT`

## Fail-closed direction / Dirección fail-closed

**EN**
- Missing required baseline artifact -> FAIL
- Missing required assurance reference -> FAIL
- Missing RuntimeGuard L4 baseline references -> FAIL
- Missing multi-jurisdiction baseline references -> FAIL
- Missing distributed readiness baseline references -> FAIL

**ES**
- Falta artefacto baseline requerido -> FAIL
- Falta referencia de assurance requerida -> FAIL
- Faltan referencias baseline de RuntimeGuard L4 -> FAIL
- Faltan referencias baseline multi-jurisdiccionales -> FAIL
- Faltan referencias baseline de readiness distribuido -> FAIL

## Run / Ejecución

bash verifier/verify_all.sh
