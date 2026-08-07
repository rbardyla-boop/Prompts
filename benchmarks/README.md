# PROMPTS V2 Comparison Benchmark

This directory contains the public development apparatus for comparing:

- **Arm A:** plain task instruction;
- **Arm B:** strongest preregistered legacy framework;
- **Arm C:** PROMPTS v2 task pack, deterministic module selection and reliability harness.

The public fixtures test apparatus and expose implementation defects. They are not independently held final evidence.

## Prepare matched arm packages

```bash
promptbench \
  --fixture research-contradiction-001 \
  --arm A \
  --output runs/research-contradiction-001/A

promptbench \
  --fixture research-contradiction-001 \
  --arm B \
  --output runs/research-contradiction-001/B

promptbench \
  --fixture research-contradiction-001 \
  --arm C \
  --output runs/research-contradiction-001/C
```

Each package contains:

- `prompt.md`;
- canonical `fixture.json`;
- the shared blinded `evaluator-package.json`;
- `run-manifest.json` with hashes and matched controls.

The fixture and evaluator hashes must be identical across A, B and C. The prompt hashes must differ.

## Run discipline

For every fixture and arm:

1. freeze model, quantization, sampling, context ceiling, tools and permissions;
2. randomize blinded arm labels outside the evaluator;
3. run at least five paired repetitions;
4. preserve raw model output and tool traces;
5. record input/output tokens, wall time, retries and failures;
6. execute the same deterministic checks;
7. submit identical evaluator packages;
8. reveal arm labels only after verdicts are frozen.

## Required output layout

```text
runs/
└── <fixture-id>/
    ├── frozen-config.json
    ├── randomization-commitment.json
    ├── A/
    │   ├── package/
    │   └── repetitions/
    ├── B/
    │   ├── package/
    │   └── repetitions/
    ├── C/
    │   ├── package/
    │   └── repetitions/
    ├── blinded-evaluations/
    ├── deterministic-results.json
    └── comparison-report.json
```

## Invalid runs

Reject rather than average runs with:

- model or quantization mismatch;
- unequal tools or source access;
- missing raw output;
- manual repair after result inspection;
- evaluator exposure to arm identity;
- benchmark-answer leakage;
- parser failure hidden as task failure;
- extra retries or context for Arm C;
- a post-hoc weaker legacy baseline.

## Decision rule

Arm C must beat Arm B on contract satisfaction or artifact quality without obtaining the result mainly through more refusals, extra tools, more context or greater model budget.

Report paired differences and confidence intervals. A positive point estimate with an interval spanning no meaningful benefit is not a win.

## Final validation

`PROMPTS_V2_VALIDATED` requires a separate evaluator-controlled battery that was not used to develop the composer, harness, task packs or evaluator rubrics.
