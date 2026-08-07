# Origins and Attribution

PROMPTS v2 is a synthesis. It preserves the distinct origin of its major mechanisms rather than presenting the complete system as one person’s isolated invention.

## Ryan Bardyla

Ryan Bardyla created and maintained the legacy prompt repository, including the Alpha, APEX, VAL, creative and meta-science adaptations preserved under `legacy/`.

PROMPTS v2 adds Ryan’s project-completion architecture:

- explicit terminal states;
- scope lock until terminal resolution;
- frontier exhaustion before retiring a concept;
- reproducible sealed negative results;
- modular task packs and precedence rules;
- evidence-preserving completion reports;
- integration of legacy specialist methods into one model-independent operating system.

## Matt Shumer — Gauntlet Loop

Matt Shumer publicly described the Gauntlet Loop as an agent-led process that decomposes a goal, assigns specialist builders and ruthless fresh-context critics, and passes work only when the artifact beats a real-world equivalent.

PROMPTS v2 uses that mechanism for artifact improvement:

```text
plan
→ specialist builder
→ fresh-context critic
→ adversarial comparison
→ repair
→ verify
→ retain the stronger artifact
```

PROMPTS v2 does not claim authorship of that core builder–critic mechanism.

## Misato — long-horizon agent reliability principles

Misato’s article “Your AI Agent Works for 10 Minutes. Then It Starts Lying” described a practical reliability architecture based on:

- task contracts established before execution;
- durable state outside conversation context;
- bounded work cycles;
- mechanical completion checks;
- independent evaluation;
- least-privilege permissions;
- reconstructable traces;
- recovery and stopping rules;
- converting real failures into permanent evaluations.

PROMPTS v2 uses those principles in its Agent Reliability Harness. The worker may propose; the harness remembers, constrains, checks, rejects and terminates.

## Austin Kleon

`legacy/KLEON_CREATIVE_LAYER_v1.1.md` adapts ideas associated with Austin Kleon’s creative work, particularly influence mapping, remix, attribution, routine and transformation.

PROMPTS v2 retains only bounded modules derived from that adaptation and preserves Kleon’s attribution. It does not claim ownership of Kleon’s original concepts, text or published works.

## Legacy frameworks

The original repository also contains model- and domain-specific adaptations made during 2025–2026. They are preserved byte-for-byte under `legacy/` with SHA-256 hashes.

Preservation does not mean every historical claim, threshold or example is endorsed as current fact. PROMPTS v2 separately records:

- retained mechanisms in `modules/legacy-extracted/MODULE_CATALOG.json`;
- conflicts in `CONFLICT_LEDGER.md`;
- deprecated and quarantined content in `DEPRECATION_LEDGER.md`;
- precedence in `PRECEDENCE_POLICY.yaml`.

## Contribution rule

Contributors must distinguish:

1. the origin of an idea;
2. an adaptation of that idea;
3. a new implementation;
4. evidence that the implementation works.

Attribution is not validation. Validation is not ownership. Both must be recorded.
