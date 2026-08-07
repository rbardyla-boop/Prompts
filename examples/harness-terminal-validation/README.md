# False-Completion Terminal Validation

This example reproduces the mandatory reliability test.

## Scenario

A worker receives five required checks. It reports `DONE` while Requirement 5 is false.

The harness must:

1. reject completion;
2. record `req-5` as the first failed requirement;
3. transition `VERIFYING → REPAIRING`;
4. recover in a fresh process from repository and `agent/` state only;
5. reject an attempt to remove the completion checks without human approval;
6. accept completion only after all five checks pass;
7. verify the complete trace hash chain.

## Reproduce

```bash
python -m pip install -e '.[test]'
python -m promptctl --root . self-test
```

Expected governing fields:

```json
{
  "result": "PASS",
  "false_completion_rejected": true,
  "failed_requirement_persisted": true,
  "recovery_passed": true,
  "repaired_completion_accepted": true,
  "material_amendment_auto_approval_rejected": true
}
```

Then run the complete regression suite:

```bash
python -m unittest discover -s tests -v
```

The verified CI receipt is stored in `receipt.json`.

## Meaning

This proves the internal mechanism against the supplied deterministic fixture. It does not prove that every model, tool adapter or host sandbox is reliable.
