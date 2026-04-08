cat > docs/canonical/Authority_Matrix.case_003.md <<'EOF'
# Authority Matrix – Case 003

**Documento:** Authority_Matrix.case_003.md  
**Versión:** v1.1  
**Fecha:** 2026-04-01  
**Estado:** vigente  
**Naturaleza:** matriz de autoridad decisoria para la ruta interna Caso 003 dentro de EthicBit / CEMU

## I. Objeto

La presente matriz distribuye la autoridad decisoria, el modo de decisión y la necesidad de escalación aplicable a cada operación crítica del Caso 003 dentro del ecosistema EthicBit / CEMU.

## II. Regla general

Toda operación crítica deberá identificar:

- autoridad competente;
- modo de decisión;
- necesidad de supervisión humana;
- y obligación de escalación cuando aplique.

## III. Valores oficiales de Decision Mode

- `HUMAN_REQUIRED`
- `HUMAN_SUPERVISED`
- `AUTONOMOUS_WITH_AUDIT`
- `AUTONOMOUS_BLOCK_ONLY`
- `AUTONOMOUS_NOT_ALLOWED`

## IV. Matriz operativa

| Operación | Autoridad | Decision Mode | Escalación requerida | Notas |
|---|---|---|---|---|
| Entity Classification | Entity Classification Logic | AUTONOMOUS_WITH_AUDIT | No | Clasificación inicial con trazabilidad obligatoria |
| Threat Model Mapping | Threat Mapping Logic | AUTONOMOUS_WITH_AUDIT | No | Mapeo de amenaza sujeto a auditoría |
| Constitutional Assessment | RuntimeGuard v2 | AUTONOMOUS_WITH_AUDIT | No | Evaluación constitucional con audit trail |
| Freeze Decision | Freeze Authority Logic | AUTONOMOUS_BLOCK_ONLY | No | El sistema puede bloquear autónomamente |
| Swarm Containment | Sovereign Containment Layer | AUTONOMOUS_BLOCK_ONLY | No | Contención autónoma permitida, certificación no |
| Post-Event Isolation Bundle | Post-Event Isolation Bundle Engine | AUTONOMOUS_WITH_AUDIT | No | Bundle automático con trazabilidad preservada |
| Output Classification | Derived Output Classification Logic | AUTONOMOUS_WITH_AUDIT | No | Clasificación de outputs derivados |
| Residual Gap Governance | Residual Gap Governance Engine | AUTONOMOUS_WITH_AUDIT | No | Gobernanza residual automática con trazabilidad |
| Output Elevation Review | Output Elevation Review Authority | HUMAN_SUPERVISED | Sí | Revisión previa a fijación o elevación |
| Artifact Manifest | Artifact Manifest Builder | AUTONOMOUS_WITH_AUDIT | No | Consolidación automática con supervisión documental |
| Collective Pack | Collective Output Consolidation Authority | HUMAN_SUPERVISED | Sí | Consolidación colectiva bajo supervisión |
| Case Bundle | Canonical Bundle Composer | HUMAN_SUPERVISED | Sí | Bundle closure-adjacent |
| Canonical Root Build | Canonical Root Builder | HUMAN_SUPERVISED | Sí | Root supervisado por sensibilidad de cierre |
| Anchor Prepare | Anchor Preparation Bridge | HUMAN_SUPERVISED | Sí | Preparación de anchor bajo control supervisado |
| Anchor Receipt | Anchor Receipt Framework | AUTONOMOUS_WITH_AUDIT | No | Receipt automático tras confirmación verificable |
| Anchor Verification | External Anchor Verification Logic | AUTONOMOUS_WITH_AUDIT | No | Verificación reproducible del evento onchain |
| Verification Environment | Verification Environment Builder | AUTONOMOUS_WITH_AUDIT | No | Entorno reproducible con hashes preservados |
| Verification Pack | Verification Pack Builder | HUMAN_SUPERVISED | Sí | Pack closure-adjacent |
| Pre-Sealing Escalation | Frontier Pre-Sealing Governance Framework | HUMAN_REQUIRED | Sí | Obligatoria para HIGH_CRITICALITY |
| Closure State | Closure State Machine | HUMAN_REQUIRED | Sí | Estado canónico de cierre |
| Formal Closure Certificate | Formal Closure Registry | HUMAN_REQUIRED | Sí | Emisión final del certificado |
| Emergency Freeze | Emergency Freeze Authority | HUMAN_REQUIRED | Sí | Activación de reversión o freeze de emergencia |
| Status Reporting | Status Reporting Layer | AUTONOMOUS_WITH_AUDIT | No | Dashboard y estado trazable |

## V. Regla de High-Criticality

Cuando el estado operativo alcance `HIGH_CRITICALITY_PRE_SEALABLE`, toda elevación hacia pre-sealing, closure state o certificado formal requerirá intervención humana obligatoria.

## VI. Regla de no equivalencia

La captura, fijación o aislamiento de un output no equivale por sí sola a elevación, anchor o clausura formal.

## VII. Determinación final

La presente matriz queda fijada como instrumento rector de autoridad para el Caso 003 dentro de EthicBit / CEMU.
