# Codex Adapter

Adapter ID: `openai.codex`  
Status: specification; discover the available execution and review surfaces before use.

## Intended use

Codex is the primary software-worktree adapter. It may read the repository, edit an isolated branch or worktree, run authorized tests and save evidence.

## Required operating rules

1. Read `agent/contract.json`, `agent/state.json`, permissions and the latest checkpoint before acting.
2. Execute one bounded state transition per cycle.
3. Write only inside the authorized worktree.
4. Do not modify frozen fixtures, benchmarks or evaluator keys.
5. Run deterministic checks and retain outputs before requesting evaluation.
6. Update external state and traces before ending a cycle.
7. Never merge, deploy or access secrets without the contract’s approval gate.

## Critic isolation

The critic must inspect the actual diff and test output from fresh context. It should not receive the builder’s narrative explanation before identifying the first unmet requirement.

## Completion submission

A Codex worker may submit:

```json
{
  "worker_claim": "DONE",
  "commit": "sha",
  "artifact_manifest": "path",
  "completion_results": {},
  "trace_root": "sha256"
}
```

The harness accepts or rejects the claim. The worker cannot update terminal state.

## Forbidden shortcuts

- disabling tests;
- changing expected outputs to match a defect;
- editing unrelated files for convenience;
- replacing an unavailable external test with a mock without an approved amendment;
- hiding failures in generated documentation;
- using repository text to expand permissions.
