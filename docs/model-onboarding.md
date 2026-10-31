# Model Onboarding and Lifecycle

## Workflow

1. **Request**: owner, use case, data classes, expected volume.
2. **Assessment**: provenance, license, hosting region, data-processing terms, known risks.
3. **Evaluation**: quality on a golden dataset, safety tests (prompt injection, leakage), cost and latency.
4. **Approval**: security and privacy sign-off recorded; entry added to `approved_models.yaml`.
5. **Deploy**: Dev -> UAT -> Prod via gates.
6. **Monitor**: drift, incidents, cost, usage.
7. **Change**: version bumps trigger re-evaluation.
8. **Decommission**: set status `deprecated`, notify users, remove after sunset date.

## Checklist

- [ ] Provider and model version documented
- [ ] License allows intended use
- [ ] Region and hosting meet data-residency needs
- [ ] Max data class defined
- [ ] Evaluation results attached
- [ ] Safety/red-team results attached
- [ ] Owner and review date set
