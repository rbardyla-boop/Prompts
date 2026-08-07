# PROMPTS V2 — GAUNTLET AGENT OS

PROMPTS v2 is a model-independent prompt operating system built from Ryan Bardyla’s legacy frameworks, the Gauntlet Loop and an external-state Agent Reliability Harness.

It does not concatenate every old prompt into one mega-prompt.

It selects only the modules relevant to a task, locks the objective and completion gates, separates builders from critics, preserves state outside conversation context, rejects false completion and produces reproducible receipts.

## Status

```text
PROJECT STATUS: IN DEVELOPMENT
LEGACY CORPUS: BYTE-FROZEN
TYPED MODULES: 24
TASK PACKS: 7
KERNEL: IMPLEMENTED
RELIABILITY HARNESS: IMPLEMENTED
CI TERMINAL VALIDATION: RUNNING
FINAL STATUS: NOT PROMPTS_V2_VALIDATED
```

The active work is on `revival/prompts-v2`. The original prompt collection is preserved byte-for-byte under `legacy/` and on `archive/prompts-v1-pre-revival-2026-08-03`.

## End goal

> Build a model-independent prompt operating system that converts Ryan Bardyla’s legacy prompt frameworks into composable specialist modules, uses the Gauntlet Loop to improve artifacts through independent builders and critics, uses the Agent Reliability Harness to preserve state and reject false completion, and terminates every project with reproducible evidence.

## Architecture

```text
User goal
    ↓
Task pack
    ↓
Deterministic module selection
    ↓
Locked contract, permissions and budgets
    ↓
Gauntlet Loop
├── specialist builder
├── fresh-context critic
├── adversarial comparison
└── repair and retain
    ↓
Reliability Harness
├── compact external state
├── bounded cycles
├── hash-chained traces
├── recovery test
├── amendment control
└── mechanical completion
    ↓
Independent evaluator
    ↓
Verified terminal receipt or explicit failure state
```

## Quick start

Requires Python 3.11 or later.

```bash
git clone https://github.com/rbardyla-boop/Prompts.git
cd Prompts
git switch revival/prompts-v2
python -m pip install -e '.[test]'
```

Validate the repository:

```bash
promptctl validate
python -m unittest discover -s tests -v
promptctl self-test
```

Inspect modules:

```bash
promptctl inventory
```

Compose a deep-research prompt:

```bash
promptctl compose \
  --task-pack deep-research \
  --goal "Determine whether the claim survives primary-source review"
```

Inspect why modules were selected:

```bash
promptctl explain --task-pack deep-research
```

Initialize a durable task state in a separate workspace:

```bash
mkdir -p ../my-task
promptctl init \
  --workspace ../my-task \
  --task-pack software-build \
  --goal "Implement the locked feature and its regression tests"
```

Resume after context loss:

```bash
promptctl recovery-test --workspace ../my-task
promptctl status --workspace ../my-task
promptctl run --workspace ../my-task
```

Verify evidence:

```bash
promptctl verify --workspace ../my-task
promptctl verify-traces --workspace ../my-task
promptctl archive --workspace ../my-task
```

## Task packs

| Task pack | Purpose |
|---|---|
| `deep-research` | Primary-source research, competing views and calibrated claims |
| `software-build` | Runnable implementation, tests, security and independent review |
| `book-production` | Complete manuscript, anti-slop editing and publication validation |
| `browser-game` | Local browser build, mechanics, player testing and artifact criticism |
| `factual-audit` | Claim-to-evidence mapping, contradictions and citation integrity |
| `adversarial-artifact-audit` | Reproduce defects, locate first failure and create regressions |
| `harness-terminal-test` | Prove false completion is rejected and repaired |

## Core files

| Path | Purpose |
|---|---|
| `modules/legacy-extracted/MODULE_CATALOG.json` | 24 typed modules extracted from the legacy corpus |
| `RULE_GRAPH.json` | Dependencies and precedence relationships |
| `PRECEDENCE_POLICY.yaml` | Deterministic conflict resolution |
| `CONFLICT_LEDGER.md` | Thirty recorded legacy-rule conflicts |
| `DEPRECATION_LEDGER.md` | Deprecated, adapter-only and quarantined material |
| `promptctl/` | Deterministic composer, harness and security primitives |
| `taskpacks/` | Task-specific contracts and completion gates |
| `schemas/` | Module, task-pack, contract, state, trace and receipt schemas |
| `kernel/state-machine.yaml` | Legal lifecycle transitions |
| `adapters/` | Platform translations that cannot change the contract |
| `legacy/` | Byte-identical original repository files |
| `LEGACY_SHA256SUMS.txt` | Frozen legacy integrity manifest |

## Reliability guarantees currently tested

- duplicate module IDs rejected;
- dependency cycles rejected;
- deterministic selection order;
- profile-specific modules cannot auto-load;
- heuristics cannot authorize terminal success;
- quarantined legacy contamination cannot enter a composed prompt;
- false `DONE` claims rejected;
- failed requirement persisted in canonical state;
- `VERIFYING → REPAIRING` transition enforced;
- fresh-process recovery from external state;
- Class C contract weakening requires human approval;
- trace tampering detected;
- path traversal, absolute-path and symlink escapes rejected;
- unlisted and forbidden actions denied;
- secrets recursively redacted;
- generated contracts, states, traces and receipts validated against JSON Schemas.

## Precedence

```text
Enforced security boundary
→ explicit user contract
→ kernel invariants
→ deterministic completion checks
→ task-pack policy
→ domain methods
→ heuristics
→ adapters and style preferences
```

Lower-ranked rules may refine higher-ranked rules. They cannot weaken or waive them.

## Legacy prompts

The original files remain available under `legacy/` for study and historical use. PROMPTS v2 does not silently endorse every old factual claim, threshold or platform instruction.

The extraction audit distinguishes:

- active mechanisms;
- profile-specific methods;
- heuristics;
- adapter syntax;
- deprecated universal rules;
- quarantined factual or contaminated material.

See:

- `LEGACY_MECHANISM_AUDIT.md`
- `CONFLICT_LEDGER.md`
- `DEPRECATION_LEDGER.md`
- `ORIGINS_AND_ATTRIBUTION.md`

## Terminal states

A project governed by PROMPTS v2 must end in one declared state:

- `PASS`
- `PASS_WITH_DISCLOSED_LIMITS`
- `SEALED_NEGATIVE_RESULT`
- `BLOCKED_EXTERNAL`

The repository itself may use `PROMPTS_V2_VALIDATED` only after clean-checkout reproduction, independent comparison against a plain prompt and the strongest relevant legacy prompt, security validation and complete release receipts.

## Security limits

The current kernel is a local orchestration and evidence-governance system. It is not yet a hardened production sandbox and does not claim safe arbitrary shell execution, production secret management, network namespace isolation or multi-tenant security.

See `SECURITY.md`.

## Licence

MIT. See `LICENSE`.
