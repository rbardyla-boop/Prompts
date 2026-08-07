# Live benchmark acceptance gate

A `research-contradiction-001` live development run is judgeable only when all of the following hold:

- 5 repetitions exist for each of arms A, B and C;
- all 15 generation calls expose positive input/output token counts;
- all 15 blinded evaluations exist before unblinding;
- no generation call emits a tool event;
- all A/B/C generation calls resolve to one identical model identifier;
- all evaluation calls resolve to one identical model identifier;
- fixture and evaluator-package hashes match across arms;
- arm prompt hashes remain distinct;
- raw generations, JSONL-derived evidence, evaluations, unblinding map and comparison report are retained;
- the report remains marked public development evidence and `final_validation_eligible: false`.

Any provider, entitlement, parser, tool-use or model-drift failure is retained as a negative execution result and is not converted into a PROMPTS v2 quality verdict.
