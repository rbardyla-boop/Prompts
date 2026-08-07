# PROMPTS V2 Conflict Ledger

Source checkpoint: `PROMPTS_V2_CHECKPOINT_0003`  
Precedence policy: `PRECEDENCE_POLICY.yaml`

Every conflict below has an explicit ruling. No original prompt was edited.

| ID | Legacy rules in conflict | Risk | Ruling | Enforced result |
|---|---|---|---|---|
| C-001 | APEX mandatory GPU utilization versus task appropriateness | CPU-bound, document and small tasks could fail a meaningless hardware gate | `PROFILE_SPECIFIC` | GPU requirements move to compute profiles and apply only when the task materially benefits |
| C-002 | APEX universal multi-seed language versus deterministic or non-stochastic work | Seed counts can become ritual rather than evidence | `PROFILE_SPECIFIC` | Task pack defines repetitions, seeds and uncertainty method according to claim type |
| C-003 | Alpha Suite `N >= 200` and Deflated Sharpe Ratio everywhere versus metric integrity | Invalid statistics may be applied outside Sharpe-like selection problems | `PROFILE_SPECIFIC` | Multiple-testing correction must match the construct and selection process |
| C-004 | Alpha fixed crisis threshold and weights versus general regime detection | A historical example becomes an unearned universal constant | `PROFILE_SPECIFIC` | Thresholds and weights must be preregistered or sensitivity-tested per task |
| C-005 | “Official statistics lie” framing versus source neutrality | The system could reverse-bias toward alternative sources | `DEPRECATE_AS_RULE` | All source classes receive provenance, authority, incentive and failure-mode analysis |
| C-006 | “Physical proxies cannot be manipulated” versus measurement integrity | Chosen proxies may contain their own selection and reporting failures | `DEPRECATE_AS_RULE` | Proxy validity and confounders must be demonstrated rather than assumed |
| C-007 | Incentive autopsy versus factual causation | A beneficiary may be accused without causal evidence | `HEURISTIC_ONLY` | Incentives generate competing hypotheses and are labelled observed or inferred |
| C-008 | Meta-Science authority inversion versus neutral investigation | The framework can presuppose suppression before evidence | `HEURISTIC_ONLY` | Curiosity lens requires evidence for, evidence against, unknowns and missing tests |
| C-009 | Darkness scores versus calibrated evidence | Subjective scores can masquerade as measurement | `ARCHIVE_ONLY` | Scores remain historical examples and are not active evidence or gates |
| C-010 | UAP and other case-study counts versus source-ledger requirements | Dated, incomplete or unsourced numbers can contaminate prompts | `QUARANTINE` | Case-study facts require separate evidence ledgers before reuse |
| C-011 | VAL Python-for-prototype/Rust-for-production lock versus model independence | Language choice may be unsuitable and distort architecture | `PROFILE_SPECIFIC` | Language selection belongs to task packs and repository constraints |
| C-012 | VAL fixed launch deadlines versus quality and completion gates | Speed can pressure the worker into false completion | `LOWER_PRECEDENCE` | Time goals are budgets; mandatory completion gates still control release |
| C-013 | VAL vibe score versus scope lock | Excitement could authorize new projects or kill valid work | `HEURISTIC_ONLY` | Vibe may propose cadence or simplification but cannot amend scope or terminal state |
| C-014 | APEX daily ship versus sealed evaluation | Frequent publication can leak or contaminate final tests | `TASK_PACK_CONTROLLED` | Daily shipping is disabled during frozen or sealed evaluation phases |
| C-015 | APEX production-output lock versus minimum viable experiment | Early mechanism tests may be forced into premature production polish | `PHASE_SPECIFIC` | MVE artifacts may be provisional; release artifacts must be complete and validated |
| C-016 | Blanket circuit-breaker/retry requirements versus components without external calls | Boilerplate complexity may reduce reliability | `RISK_PROFILED` | Resilience patterns apply only to relevant failure surfaces and remain bounded |
| C-017 | One test per public function versus outcome-based verification | Test count may improve while real behavior remains untested | `DEPRECATE_AS_UNIVERSAL` | Task packs define behavior, property, integration and regression requirements |
| C-018 | Grok command names versus model-independent kernel | Kernel could become unusable on other platforms | `ADAPTER_ONLY` | Platform commands and tool names live only in adapters |
| C-019 | Grok tool-count and speed claims versus current capabilities | Dated product facts may be false | `QUARANTINE` | Adapters must discover or document current capabilities; legacy counts are not imported |
| C-020 | Creative imitation practice versus originality and licensing | Practice copying may be shipped as original work | `SEPARATE_PHASES` | Practice artifacts are marked non-release; publishable work requires transformation and attribution |
| C-021 | Forced remix versus locked scope | Creative exploration can expand the project indefinitely | `LOWER_PRECEDENCE` | Remix runs only inside a bounded experiment or approved replan |
| C-022 | Side-project validator versus current project constitution | The validator might start another project before terminal state | `SCOPE_LOCK_WINS` | All new project ideas are captured as deferred records until a terminal state exists |
| C-023 | Alternative-proxy preference versus official primary-source requirement | A domain prompt may demote a legally authoritative source | `CONTEXTUAL_AUTHORITY` | Legal and administrative facts use authoritative records; proxies may test measurement completeness but cannot overwrite jurisdictional authority without evidence |
| C-024 | SHAP feature contributions versus causal interpretation | Explanations may be reported as causes | `DIAGNOSTIC_ONLY` | Contribution methods trigger leakage and ablation checks; causal claims require separate design |
| C-025 | Umbrella Alpha Suite versus underlying domain modules | Duplicate rules can be applied twice and overweight a method | `PROVENANCE_ONLY` | The umbrella file documents lineage; executable modules derive from the narrowest source sections |
| C-026 | README MIT statement versus missing licence file | Users may infer legal terms without a canonical licence artifact | `RELEASE_BLOCKER` | Add an actual root `LICENSE` before release; do not alter the frozen legacy README |
| C-027 | Trailing assistant response inside GEOPOL legacy file versus trusted framework content | Generated contamination could become an active instruction | `QUARANTINE` | The byte sequence remains preserved, but extraction and runtime selection must exclude it |
| C-028 | Heuristic improvement loop versus finite terminal states | Critics can create endless polishing | `TERMINAL_POLICY_WINS` | Critics judge locked criteria and return the first major defect; passing artifacts terminate |
| C-029 | Worker self-reflection versus independent evaluation | The same error frame may grade itself generously | `SEPARATE_ROLES` | Worker review is advisory; independent evaluator and deterministic gates control completion |
| C-030 | Weak benchmark improvement versus real-world equivalence | A system may pass by selecting a weak baseline | `FAIR_BASELINE_REQUIRED` | Comparison uses the strongest fair legacy prompt and a plain-prompt baseline under matched resources |

## General precedence decision

The effective order is:

```text
Security boundary
→ explicit user contract
→ kernel invariants
→ deterministic completion checks
→ task-pack policy
→ domain methods
→ heuristics
→ adapters and style preferences
```

A lower layer may refine a higher layer but cannot weaken, waive or redefine it.

## Open validation work

The rulings are specified but not yet proven mechanically. Checkpoint 0004 requires:

1. a machine-readable rule graph;
2. cycle detection;
3. tests showing profile-specific modules do not auto-load;
4. tests showing heuristics cannot authorize completion or permissions;
5. a compiler that produces deterministic selected-module order;
6. a regression for the quarantined GEOPOL tail.
