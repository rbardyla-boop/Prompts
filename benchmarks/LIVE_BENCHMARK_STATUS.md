# PROMPTS v2 Live Benchmark Status

This file records the development benchmark execution boundary after PR #2 merged.

## Preserved negative evidence

The live comparison apparatus has not yet produced a scored A/B/C result. The following failures occurred before any benchmark model response was accepted and therefore are infrastructure/adapter evidence, not PROMPTS v2 quality failures:

1. GitHub Models inference returned HTTP 410 because GitHub Models inference had been retired.
2. Copilot CLI rejected `--max-ai-credits` values below its minimum of 30.
3. Explicit model requests for `gpt-5.4` and `claude-haiku-4.5` were rejected in the Actions execution path used by the first probes.
4. Copilot Auto rejected the adapter's forced `--reasoning-effort low`; that override has been removed.
5. After the adapter repairs, Copilot Auto successfully routed the Actions request. It reported `gpt-5-mini` as the selected model and `gpt-5-mini` plus `claude-haiku-4.5` as the currently available Auto candidates, then the actual model call was refused with HTTP 402 `quota_exceeded` before producing an assistant answer.

The decisive probe is GitHub Actions run `31226101171`, job `93020602790`, on PR #3. Its structured Copilot event stream reported:

- Auto-selected model: `gpt-5-mini`;
- available Auto models: `gpt-5-mini`, `claude-haiku-4.5`;
- model transport reached `/responses`;
- failure: HTTP 402, `quota_exceeded`;
- chat entitlement: 200 requests;
- chat used: 200 requests;
- chat remaining: 0%;
- reported reset: `2026-09-01T00:00:00Z`;
- accepted benchmark generations: 0;
- scored A/B/C comparisons: 0.

This is now classified as `BLOCKED_EXTERNAL`. The repository must not reinterpret the provider quota failure as either a PROMPTS v2 pass or failure.

## Repository gate status

The companion clean-checkout workflow run `31226101179` passed on the same PR candidate:

- 49/49 unit and adversarial tests passed;
- kernel validation passed;
- terminal false-completion/recovery harness passed;
- deterministic direct and task-pack selection passed;
- quarantined legacy-tail exclusion passed;
- all 15 A/B/C benchmark packages reproduced;
- fixture hashes matched across arms;
- evaluator-package hashes matched across arms;
- prompt hashes remained distinct across arms;
- tracked checkout was clean after generated build artifacts were removed;
- candidate evidence artifact ID: `9012138157`.

## Current runner contract

The live runner now:

- defaults to Copilot `auto` rather than assuming a model entitlement;
- does not force a reasoning-effort setting;
- enforces the Copilot CLI minimum 30-credit session ceiling before execution;
- keeps every model call in a fresh temporary work directory and `COPILOT_HOME`;
- disables custom instructions, built-in MCPs, remote control, user questions and benchmark tool access;
- records Copilot JSONL events and token counts;
- rejects any observed tool event;
- keeps public development evidence ineligible for `PROMPTS_V2_VALIDATED`.

The workflow reads the resolved model identity from Copilot's structured event stream. A live comparison is accepted only if all 15 A/B/C generation calls resolve to one model and all 15 blinded evaluation calls resolve to one model. Model drift fails the gate.

## Status

`BLOCKED_EXTERNAL` for live comparison execution. No repository repair is presently known that can manufacture the missing provider quota. Once an execution surface with available quota is supplied, the existing `workflow_dispatch` path can rerun the frozen 5 × A/B/C `research-contradiction-001` gate without changing the benchmark task, rubric or decision rule.

Overall project status remains `IN_PROGRESS`, not `PROMPTS_V2_VALIDATED`. Even a successful public-fixture development run would still require independently held final validation.
