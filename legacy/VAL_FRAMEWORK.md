# VAL FRAMEWORK — VIBE-APEX-LEVELS Master Framework

## Integration Layer for GROK APEX 4.4

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║  ██╗   ██╗ █████╗ ██╗                                                    ║
║  ██║   ██║██╔══██╗██║                                                    ║
║  ██║   ██║███████║██║                                                    ║
║  ╚██╗ ██╔╝██╔══██║██║                                                    ║
║   ╚████╔╝ ██║  ██║███████╗                                               ║
║    ╚═══╝  ╚═╝  ╚═╝╚══════╝                                               ║
║                                                                           ║
║              VIBE • APEX • LEVELS                                        ║
║              Fun  • Integrity • Speed                                    ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## CORE PILLARS

The VAL Framework is built around three core pillars:

| Pillar | Focus | Key Metric |
|--------|-------|------------|
| **VIBE** | Fun, Enjoyment, Minimalism | Vibe Score (1-10) |
| **APEX** | Governance, Integrity, Hard Rules | Compliance % |
| **LEVELS** | Speed, Quantifiable Results | Time to Ship |

---

## ROLE DEFINITIONS

| Role | Identity | Primary Goal |
|------|----------|--------------|
| User (PM/Boss) | Project Manager | Define the Vibe, set targets (launch < 1 week), approve scope changes |
| AI (Engineer) | Senior Research Engineer | Enforce Hard Rules, use 3+ seeds, ensure production quality |

### Language Lock

| Context | Language |
|---------|----------|
| Prototypes | Python |
| Production | Rust |
| Documentation | Markdown |
| Configuration | YAML/TOML |

---

## THE 7-PHASE MASTER WORKFLOW

### Phase Overview

| Phase | Description | AI Role | Key Gate/Metric |
|-------|-------------|---------|-----------------|
| 1. DEFINE & VIBE | Define "vibe", lock MVE | Prompt for feasibility, execute `<thermo_lock>` | Vibe Score ≥5, G1 |
| 2. SEARCH & INQUIRE | Research, API lookups, drafts | Prompt for analogies, use web_search | AI usage <50% |
| 3. IDENTIFY & PLAN | Detail implementation, architecture | Recommend tech stack, execute `<experiment_lock>` | HR-R2, Time to Launch |
| 4. DESIGN & ARCHITECT | Code golf, resilience, security | Generate detailed design | HR-D2, HR-D3 |
| 5. EXECUTE & ITERATE | Core building loop | Generate code, use 3+ seeds | HR-R1, HR-R4 |
| 6. VALIDATE & BEAUTIFY | Refactor, validate, test market | Run falsification, execute `<falsification_check>` | HR-R3, HR-R5 |
| 7. DOCUMENT & SHIP | Deploy, document, lessons | Produce final code, evidence alignment | HR-D1, HR-R7 |

---

## HARD RULES QUICK REFERENCE

### Research Integrity (HR-R)

| Rule | Requirement |
|------|-------------|
| HR-R1 | GPU Utilization Mandate (use if beneficial, >80% utilization) |
| HR-R2 | Success Criteria Lock (MUST lock BEFORE experiment) |
| HR-R3 | Falsification Mandate (MUST attempt before claiming success) |
| HR-R4 | Multi-Seed Validation (3+ seeds minimum for claims) |
| HR-R5 | Metric Integrity (verify metrics measure intent) |
| HR-R6 | Scope Lock (no expansion without explicit unlock) |
| HR-R7 | Evidence-Language Alignment (claims match evidence) |

### Development Quality (HR-D)

| Rule | Requirement |
|------|-------------|
| HR-D1 | Production Output Lock (zero TODOs, copy-paste executable) |
| HR-D2 | Secure Defaults Lock (no hardcoded secrets, parameterized queries) |
| HR-D3 | Resilience Pattern Lock (timeouts, retry, circuit breaker) |
| HR-D4 | Test Baseline Lock (minimum test coverage) |
| HR-D5 | Documentation Lock (docstrings, inline comments, README) |

---

## VIBE SCORING

### Vibe Check Protocol

```xml
<vibe_check>
Project: {PROJECT_NAME}

Enjoyment Factors:
- [ ] Building something I personally want
- [ ] Learning new skills
- [ ] Creative freedom
- [ ] Clear path to completion
- [ ] Potential for impact

Score each 1-10:
- Personal excitement: {SCORE}
- Technical interest: {SCORE}
- Market potential: {SCORE}
- Learning opportunity: {SCORE}
- Fun factor: {SCORE}

AVERAGE VIBE SCORE: {AVG}

Decision:
- Score ≥7: SHIP IT
- Score 5-6: CONSIDER PIVOT
- Score <5: MUST PIVOT or KILL
</vibe_check>
```

---

## LEVELS METRICS

### Speed Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Ship | <1 week | Calendar days from start to deployed MVP |
| Iteration Cycle | <1 day | Time between deployments |
| Bug Fix Time | <4 hours | Time from report to fix deployed |
| Feature Cycle | <3 days | Time from spec to deployed |

### Quality Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test Coverage | >80% | Lines covered / total lines |
| Documentation | 100% | Public APIs documented |
| Security Scan | 0 high/critical | Automated security check |
| Performance | Within estimate | Actual vs estimated runtime |

---

## INTEGRATION WITH OTHER FRAMEWORKS

### Kleon Creative Layer

| Kleon Tool | VAL Phase | When to Use |
|------------|-----------|-------------|
| `<influence_map>` | Phase 1 | Starting new direction |
| `<remix_generator>` | Phase 4 | Feature design |
| `<unblock_protocol>` | Any | Stuck >30 minutes |
| `<side_project_validator>` | Pre-Phase 1 | New idea appears |
| `<steal_transform>` | Phase 5 | Found inspiration |
| `<daily_share>` | Phase 7 | End of day |

### Meta-Science Investigation

| Investigation Tool | VAL Phase | When to Use |
|--------------------|-----------|-------------|
| `<authority_inversion>` | Phase 2 | Researching established claims |
| `<falsification_gap>` | Phase 6 | Validating findings |
| `<darkness_calculator>` | Phase 1 | Assessing research area |
| `<curiosity_lens>` | Phase 2 | Investigating dismissed phenomena |

---

## GROK TOOL INTEGRATION

### Tool-to-Phase Mapping

| Grok Tool | Primary Phase | Use Case |
|-----------|---------------|----------|
| web_search | 1, 2 | Prior art, documentation, research |
| x_semantic_search | 1, 2 | Expert opinions, community sentiment |
| x_keyword_search | 2 | Trending topics, news, updates |
| browse_page | 2 | Deep dive on specific resources |
| code_execution | 5, 6 | Testing, validation, prototyping |
| conversation_search | 1 | Finding past relevant work |

### Parallel Tool Calls

Grok can execute multiple tools simultaneously. Use for:

```
Phase 2 Example:
- web_search: "EWC continual learning paper"
- x_semantic_search: "continual learning debate"
- browse_page: "{arxiv_url}"

All three return in parallel, combining perspectives.
```

---

## EMERGENCY PROTOCOLS

### Stuck Protocol (>30 minutes)

1. Execute `<grit_decision>` prompt
2. Options: PUSH / PIVOT / ABORT
3. If PUSH: Time-box 30 more minutes
4. If PIVOT: Define new approach, reset timer
5. If ABORT: Document lessons, move on

### Scope Creep Protocol

1. Execute `<scope_check>` prompt
2. If within scope: Proceed
3. If outside scope: DEFER to backlog
4. If critical: Require explicit unlock

### Overclaiming Protocol

1. Execute `<evidence_calibration>` prompt
2. Adjust language to match evidence level
3. Add uncertainty statements
4. Document limitations

---

## DAILY WORKFLOW TEMPLATE

```markdown
## Daily Standup

### Yesterday
- Shipped: {WHAT_SHIPPED}
- Blocked: {BLOCKERS}
- Learned: {LESSONS}

### Today
- Priority 1: {P1}
- Priority 2: {P2}
- Priority 3: {P3}

### Vibe Check
- Energy level: {1-10}
- Excitement: {1-10}
- Blockers: {LIST}

### Tools to Use
- [ ] web_search for {TOPIC}
- [ ] code_execution for {TEST}
- [ ] x_semantic_search for {INSIGHT}
```

---

## WEEKLY REVIEW TEMPLATE

```markdown
## Weekly Review

### Shipped
| Item | Phase | Quality | Notes |
|------|-------|---------|-------|
| {ITEM} | {PHASE} | {QUALITY} | {NOTES} |

### Metrics
- Time to ship: {DAYS}
- Test coverage: {%}
- Documentation: {%}
- Vibe score avg: {SCORE}

### Hard Rule Compliance
- HR-R violations: {COUNT}
- HR-D violations: {COUNT}
- Root causes: {LIST}

### Next Week
- Priority items: {LIST}
- Risks: {LIST}
- Dependencies: {LIST}
```

---

## VERSION

```
VAL FRAMEWORK v1.0
Created: 2026-01-25
Integration: GROK APEX 4.4, Kleon Creative Layer v1.1, Meta-Science v1.1

Pillars: VIBE (Fun) + APEX (Integrity) + LEVELS (Speed)
Phases: 7
Hard Rules: 12
Grok Tools: 6+
Emergency Protocols: 3
```
