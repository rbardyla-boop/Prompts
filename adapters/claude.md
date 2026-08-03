# Claude Adapter

Adapter ID: `anthropic.claude`  
Status: specification; discover current tools and context controls before use.

## Translation

- Supply the task contract and current state as explicit project files.
- Use fresh-context workers or separate sessions for builder and critic roles.
- Prefer compact evidence packages over long inherited conversations.
- Treat plans and summaries as navigation aids, not verification evidence.
- Store decisions and checkpoints outside the conversation.

## Long-context rule

A large context window does not replace durable state. Before context compaction or handoff, the worker must update:

- current phase;
- completed components;
- next action;
- failed requirement;
- latest verified checkpoint;
- remaining budget.

## Evaluator prompt boundary

The evaluator receives the contract, artifact and evidence package. It does not receive the worker’s private analysis, self-critique or persuasive completion summary.

## Completion boundary

Claude may propose a verdict. Deterministic checks and the PROMPTS v2 harness authorize the terminal transition.
