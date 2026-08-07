# Platform Adapters

Adapters translate PROMPTS v2’s model-independent contract into platform syntax. They do not change the task.

## Adapter invariants

An adapter may translate:

- tool names;
- sub-agent or fresh-context invocation syntax;
- filesystem instructions;
- browsing calls;
- response schemas;
- context-window packaging;
- model endpoint configuration.

An adapter may not change:

- objective;
- deliverables;
- constraints;
- success criteria;
- evidence standard;
- permissions;
- budgets;
- completion checks;
- terminal states;
- precedence rules.

## Discovery-first rule

Platform capabilities change. Before a run, the adapter must discover or receive the available tools and record them in an adapter receipt. Historical tool names in `legacy/` are never assumed to exist.

## Fresh-context critic rule

When literal sub-agents are unavailable, the adapter must emulate role separation using a new conversation, new process or isolated context package. It must disclose the weaker isolation.

## Required adapter receipt

```json
{
  "adapter_id": "platform.name",
  "adapter_version": "1.0.0",
  "platform": "name",
  "model": "resolved model identifier",
  "available_tools": [],
  "unavailable_required_tools": [],
  "role_isolation": "sub-agent | fresh-process | fresh-conversation | emulated",
  "contract_hash": "sha256",
  "permissions_hash": "sha256",
  "translation_only": true
}
```

An unavailable required tool produces `BLOCKED` or an approved implementation clarification. It does not authorize the adapter to invent evidence or silently substitute a weaker gate.
