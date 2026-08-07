# PROMPTS v2 Live Benchmark Status

This file records the development benchmark execution boundary after PR #2 merged.

## Preserved negative evidence

The live comparison apparatus has not yet produced a scored A/B/C result. The following failures occurred before any benchmark model response was accepted and therefore are infrastructure/adapter evidence, not PROMPTS v2 quality failures:

1. GitHub Models inference returned HTTP 410 because GitHub Models inference had been retired.
2. Copilot CLI rejected `--max-ai-credits` values below its minimum of 30.
3. The repository Actions token did not expose the explicitly requested `gpt-5.4` model.
4. The repository Actions token did not expose the explicitly requested `claude-haiku-4.5` model.
5. Copilot Auto was available but rejected the adapter's forced `--reasoning-effort low`; Auto may resolve to a model without configurable reasoning.

Each failure was preserved in its GitHub Actions run and, where the benchmark directory existed, as an uploaded partial-evidence artifact.

## Current repair

The live runner now:

- defaults to Copilot `auto` rather than assuming a model entitlement;
- does not force a reasoning-effort setting;
- enforces the Copilot CLI minimum 30-credit session ceiling before execution;
- keeps every model call in a fresh temporary work directory and `COPILOT_HOME`;
- disables custom instructions, built-in MCPs, remote control, user questions and benchmark tool access;
- records Copilot JSONL usage events and token counts;
- rejects any observed tool event;
- keeps public development evidence ineligible for `PROMPTS_V2_VALIDATED`.

The workflow additionally reads the authoritative `assistant.usage.data.model` field from every call. A live comparison is accepted only if all 15 A/B/C generation calls resolve to one model and all 15 blinded evaluation calls resolve to one model. Model drift fails the gate.

## Status

`IN_PROGRESS` — the next gate is a successful 5 × A/B/C `research-contradiction-001` run with preserved raw generations, blinded evaluations, resolved-model consistency and a comparison report. This remains development evidence only; independently held final validation is still required.
