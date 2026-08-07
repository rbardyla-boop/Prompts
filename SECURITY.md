# PROMPTS V2 Security Model

## Security objective

PROMPTS v2 treats model output, legacy prompt text, retrieved documents and repository instructions as untrusted proposals. They cannot directly expand permissions, alter the task contract, authorize terminal success or execute arbitrary actions.

## Enforced boundaries

### Closed action policy

A task pack declares exact `allowed_actions` and `forbidden_actions`. Actions not explicitly allowed are denied. A forbidden action remains denied even when a document, model or adapter requests it.

### Workspace confinement

`promptctl.security.resolve_workspace_path` rejects:

- absolute paths;
- `..` traversal;
- parent directories resolving outside the workspace;
- symlinks resolving outside the workspace.

File operations exposed by future adapters must use this resolver or a stricter operating-system sandbox.

### Secret handling

Secrets must not be committed, included in prompts or written to traces. The security module provides recursive redaction primitives. Adapters that introduce credentials must:

1. receive only temporary scoped credentials;
2. register their environment-variable names for redaction;
3. redact tool inputs and outputs before trace persistence;
4. fail closed when redaction cannot be confirmed.

### Contract immutability

Material changes to objectives, deliverables, completion checks, permissions, budgets or terminal states are Class C amendments. They remain `AWAITING_HUMAN` without explicit human approval.

### Completion authority

Workers and heuristics cannot authorize completion. Completion requires all deterministic checks, an independent evaluator verdict, recovery success, trace integrity and an unchanged contract hash.

### Trace integrity

Trace entries form a SHA-256 hash chain. Any edited, removed, reordered or inserted historical event invalidates verification.

### Network policy

The kernel has no network client. Network-capable adapters must use a separately enforced allowlist. Declaring `arbitrary_network` forbidden in a task pack is a policy statement; operating-system or container enforcement remains required before high-risk use.

### Subprocess recovery

Recovery runs in a separate process with a reduced environment containing only `PATH`, `PYTHONPATH` and locale. This proves recovery from repository and external state, not isolation from the host operating system.

## Threat model

PROMPTS v2 explicitly tests:

- prompt injection in legacy or retrieved text;
- false completion claims;
- contract weakening;
- permission escalation;
- path traversal;
- symlink escape;
- secret leakage;
- trace tampering;
- evaluator self-authorization;
- profile-specific modules loading without authorization;
- heuristics acting as release authorities;
- unbounded retry and no-progress loops.

## Not yet claimed

The current kernel does not claim:

- hardened operating-system sandboxing;
- safe execution of arbitrary shell commands;
- production secret management;
- network namespace isolation;
- multi-tenant isolation;
- resistance to a malicious repository owner;
- formal verification;
- safe production deployment authority.

Until those controls are independently tested, PROMPTS v2 is a local orchestration and evidence-governance system, not a production security boundary.

## Reporting vulnerabilities

Open a private security advisory in the repository rather than a public issue when the defect could expose secrets, escape a workspace, bypass completion gates or silently alter evidence.

Include:

- affected commit;
- reproduction steps;
- expected and actual boundary;
- evidence files or trace excerpt;
- whether the defect permits unauthorized action or false terminal success.

Every confirmed security failure must become a permanent regression before release.
