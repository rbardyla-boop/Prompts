# PROMPTS V2 Deprecation Ledger

Source checkpoint: `PROMPTS_V2_CHECKPOINT_0003`

Deprecation does not delete history. All original bytes remain under `legacy/` and are protected by the frozen hash manifest.

## Status meanings

- `ACTIVE`: transferable mechanism eligible for deterministic selection.
- `PROFILE_SPECIFIC`: available only when a task pack or explicit contract selects it.
- `ADAPTER_ONLY`: platform syntax or capability translation; never kernel authority.
- `PROVENANCE_ONLY`: retained to document lineage but not loaded during task execution.
- `DEPRECATED`: known mechanism or rule that should not be selected for new work.
- `QUARANTINED`: factual, contaminated or unsafe content excluded until independently repaired.
- `ARCHIVE_ONLY`: historical example preserved without active use.

## Deprecated universal rules

| ID | Legacy rule | Source | New status | Reason | Replacement |
|---|---|---|---|---|---|
| D-001 | GPU utilization must exceed 80% whenever computation is available | GROK APEX HR-R1 | `PROFILE_SPECIFIC` | Not meaningful for document, CPU-bound or small tasks | Compute profile selected by task requirements |
| D-002 | Every performance claim requires at least three seeds | GROK APEX HR-R4 | `PROFILE_SPECIFIC` | Deterministic and non-stochastic tasks need different uncertainty treatment | Task-pack replication policy |
| D-003 | Every cross-domain correlation requires DSR at `N >= 200` | Alpha frameworks | `PROFILE_SPECIFIC` | Deflated Sharpe Ratio is not a universal correction | Metric-appropriate multiple-testing module |
| D-004 | Crisis gating uses fixed probability `0.65` | Alpha frameworks | `DEPRECATED` as universal default | Historical threshold lacks general authority | Preregistered or sensitivity-tested task threshold |
| D-005 | Physical sources receive fixed weight 1.0 and official sources 0.3 in crisis | Alpha frameworks | `DEPRECATED` | Source weights cannot be universal | Provenance and measurement-quality assessment |
| D-006 | Official statistics, reports or narratives inherently lie | Alpha and Meta-Science rhetoric | `DEPRECATED` | Introduces reverse-confirmation bias | Source-neutral authority and failure-mode audit |
| D-007 | Bodies, shipments, trauma records or other physical proxies cannot lie | Alpha rhetoric | `DEPRECATED` | Physical measurements also have coverage and classification errors | Proxy validation and triangulation |
| D-008 | Python is always the prototype language and Rust always production | VAL language lock | `PROFILE_SPECIFIC` | Conflicts with repository, team and task constraints | Task-pack language decision |
| D-009 | Every project must ship within one week and every feature within three days | VAL speed targets | `HEURISTIC` | Speed goals can incentivize false completion | Explicit budget plus mechanical terminal gates |
| D-010 | Test coverage above 80% proves quality | VAL quality benchmark | `DEPRECATED` as universal gate | Coverage does not prove behavior or correctness | Behavior, property, integration and regression checks |
| D-011 | One test per public function | APEX HR-D4 | `DEPRECATED` as universal gate | Encourages test-count gaming | Risk- and behavior-based test plan |
| D-012 | Every external call requires retry and circuit breaker | APEX HR-D3 | `PROFILE_SPECIFIC` | Some operations must fail closed or must not retry | Risk-profiled bounded resilience policy |
| D-013 | Daily shipping is always desirable | APEX and VAL | `HEURISTIC` | Can contaminate sealed evaluations and destabilize frozen artifacts | Phase-aware publication policy |
| D-014 | Vibe score directly determines SHIP, PIVOT or KILL | VAL | `DEPRECATED` as authority | Subjective motivation cannot define factual success | Sustainability suggestions subordinate to contract |
| D-015 | Creation-to-consumption ratio is a universal productivity metric | Kleon adaptation | `ARCHIVE_ONLY` | Personal routine heuristic, not validated construct | User-defined cadence and output evidence |

## Adapter-only material

| ID | Material | Source | Ruling |
|---|---|---|---|
| A-001 | `/grok-*` commands | GROK APEX | Translate through Grok adapter only |
| A-002 | `web_search`, `x_semantic_search`, `x_keyword_search`, `browse_page`, `code_execution` names | Grok files | Discover current tools in adapter; never hard-code into kernel |
| A-003 | Grok-versus-Claude comparisons | GROK prompting guide | Historical and time-sensitive; exclude from selection logic |
| A-004 | Tool counts and knowledge-cutoff claims | GROK prompting guide | Must be checked against current official platform documentation |
| A-005 | Claimed speed or efficiency multipliers | GROK prompting guide | Quarantined until reproduced under a defined benchmark |

## Provenance-only material

| ID | Material | Ruling |
|---|---|---|
| P-001 | `THE ALPHA SUITE v1.0.md` umbrella duplication | Documents lineage; narrow domain modules provide executable rules |
| P-002 | Legacy README framework sequence | Historical navigation; PROMPTS v2 composer owns selection |
| P-003 | ASCII art, branding and slogans | May remain in historical files but cannot affect decisions |
| P-004 | Legacy “God Prompt” wording | Examples only; composer generates current task contracts and rubrics |

## Quarantined factual and contaminated content

| ID | Content | Source | Reason | Release condition |
|---|---|---|---|---|
| Q-001 | Trailing assistant response beginning “Sure, I can help you with that” | `legacy/GEOPOL_ALPHA v1.md` | Generated contamination embedded in framework file | Permanent exclusion from extraction; byte-preserved for audit |
| Q-002 | Canada crime, trauma, laundering and construction figures | CRIME, COMPARE and Alpha Suite | Precise claims lack attached evidence ledgers in the repository | Separate sourced case-study ledger and current verification |
| Q-003 | Tariff event returns, pass-through values and chapter-specific examples | GEOPOL and Alpha Suite | Historical, time-sensitive and unsourced in the prompt corpus | Primary-source reconstruction and statistical reproduction |
| Q-004 | UAP counts, investigation summaries and funding claims | Meta-Science | Dated and incomplete case-study assertions | Independent evidence ledger representing supporting and contrary evidence |
| Q-005 | Darkness scores and topic rankings | Meta-Science | Subjective scoring presented with numerical appearance | Validated rubric, inter-rater testing and bounded purpose—or remain archived |
| Q-006 | Claims that institutions suppress, reclassify or launder narratives | Multiple legacy files | Incentive inference is not proof of deliberate action | Direct evidence or qualified hypothesis language |
| Q-007 | Embedded synthetic TVP-VAR code as evidence of working regime detection | Alpha Suite | Example code is not a validated implementation or empirical result | Tested module with fixtures, baselines and sensitivity analysis |
| Q-008 | SHAP target signs and expected feature dominance | Alpha domain files | Predetermined explanation can force agreement | Model-specific leakage audit without expected-answer enforcement |

## Release blockers created by this audit

1. Add a canonical root `LICENSE` file; the README statement alone is insufficient.
2. Add `ORIGINS_AND_ATTRIBUTION.md` preserving Matt Shumer, Misato, Ryan Bardyla and Austin Kleon lineage as applicable.
3. Implement a contamination regression proving `Q-001` cannot enter a composed prompt.
4. Keep all `PROFILE_SPECIFIC` modules opt-in.
5. Require evidence ledgers before any quarantined case study can be published as current fact.
6. Preserve this ledger in every release archive.

## No-deletion rule

Nothing in this ledger authorizes editing or deleting the frozen legacy corpus. Deprecation affects selection and claims, not preservation.
