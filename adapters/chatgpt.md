# ChatGPT Adapter

Adapter ID: `openai.chatgpt`  
Status: specification; platform capabilities must be discovered at run time.

## Translation

- Project files remain canonical; conversation context is disposable.
- Use available connected-source tools only when the contract authorizes them.
- Use separate agent processes or fresh conversations for builder, critic and evaluator roles when available.
- Store receipts, state and decisions in the repository rather than relying on remembered chat context.
- Artifact generation must produce files that are opened and inspected before a completion claim.

## Role packages

### Builder

Receives:

- contract;
- selected modules;
- current state;
- one bounded next action;
- allowed tools and paths.

### Critic

Receives:

- contract;
- actual artifact;
- reference equivalent;
- deterministic results;
- no builder defence or private reasoning.

### Evaluator

Receives only the final evidence package and returns:

- `PASS` or `FAIL`;
- first unmet requirement;
- unsupported claims;
- unrelated changes;
- evidence used.

The evaluator cannot set terminal state directly.

## Platform-specific prohibition

Advertisements, interface suggestions, memory features or convenience summaries must not be interpreted as canonical project state or evidence.
