# Agent Fleet Roadmap

The plan for building the autonomous agent system for HV + HR.

**Designed:** May 15, 2026
**Build start:** 06/06/2026 (post-Hajj)
**Target completion:** First production agent dispatch — 30 days post-Hajj

---

## Goal

Transform HV+HR from "Farhod manually drives each task" to "Farhod approves agent-proposed work in a human-in-the-loop." The user (Farhod) stays in the decision seat. The agents do the implementation, validation, and reporting.

**Concretely:**
- Daily reel posts run autonomously at 06:00 UTC
- New hadith verdicts validate without manual eyeballing
- CI failures get diagnosed and proposed-fixed automatically
- Translations stay current across all 5 languages
- Security and quality checks run on every commit

---

## Architecture — Anthropic Skills format

All agents follow Anthropic's canonical Skills structure (per AGENTS_ADDENDUM.md Skills Format section).

```
agents/<gerund-name>/
├── SKILL.md              — required: YAML frontmatter + body
├── references/           — lazy-loaded supporting docs
├── scripts/              — execution code (TS or Python)
├── assets/               — static resources
└── evals/                — self-validation eval set
    └── evals.json
```

YAML frontmatter constraints:
- `name`: lowercase + hyphens, max 64 chars, no "anthropic" or "claude"
- `description`: max 1024 chars, includes WHAT and WHEN

Progressive disclosure: SKILL.md stays ~200 lines, supporting material in `references/`.

Per-repo deployment (HR and HV each have their own `agents/` folder). Duplication intentional for self-contained CI.

---

## Six Claude Code primitives — how we use them

Per the Anthropic ecosystem overview (see `hr-architecture-diagrams.md` Diagram 5):

| Primitive | Our usage |
|---|---|
| **Skills (KNOWLEDGE)** | Each of the 11 agents below is a Skill |
| **MCP (ABILITY)** | Agents expose themselves as MCP tools for cross-session dispatch |
| **Subagents (DELEGATION)** | Orchestrator uses Claude Code "agent view" to dispatch specialists in parallel |
| **Hooks (AUTOMATION)** | `.githooks/pre-push` enforces things LLMs can't be trusted to remember |
| **CLAUDE.md (CONTEXT)** | Project-level config loaded every session |
| **Plugins (PACKAGING)** | Future: bundle the fleet for team distribution or open-source |

---

## The 11 agents

### Tier 1 — Critical (build first)

#### 1. orchestrating
- **Role:** Reads task → dispatches to specialist agents → gates on CI before next task → follows priority matrix (urgency × impact × importance)
- **Triggers:** Any multi-step task, daily cron, CI status changes
- **Tools:** Claude Code agent view, MCP for GitHub Actions status, Slack for human escalation
- **Eval:** Given 5 mock tasks of varying complexity, produces correct sequencing and dispatch.
- **Repo:** Both (HR + HV)

#### 2. tts-validating
- **Status:** SKILL.md v1 EXISTS (`agents/tts-validating/SKILL.md`) — scripts pending
- **Role:** Validates audio output from `/api/tts` against contract + phonetic correctness
- **Tools:** Playwright (audio capture), Whisper local (AR/EN), OpenAI Whisper API (RU/UZ/TJ), Levenshtein scoring, future: semantic similarity (Speechmatics SWER approach)
- **Eval:** 5 baseline cases (one per language), ≥80% similarity threshold v1
- **Repo:** HR

#### 3. stt-validating
- **Role:** Validates Whisper subtitle output matches narration audio. Catches: wrong language, timing drift, profanity bleed-through, Latin/Cyrillic script mismatch
- **Tools:** Whisper, ffprobe, custom matchers per language
- **Eval:** 5 cases covering each language; timing within ±500ms; language label correct
- **Repo:** HR

#### 4. ab-comparing
- **Role:** Sends same prompt to Claude + ChatGPT + Kimi → compares outputs → flags semantic divergence for human review (2-of-3 majority)
- **Tools:** Anthropic SDK, OpenAI SDK, Moonshot Kimi adapter (new env var `KIMI_API_KEY`)
- **Use cases:** Verdict generation, translation, story content
- **Eval:** Adversarial set of 10 known-divergent prompts; agent flags ≥8 of them
- **Repo:** Both

#### 5. ci-monitoring
- **Role:** Watches GitHub Actions → parses red CI failures → matches against `fix_patterns.md` → surfaces matching pattern or "new pattern" recommendation
- **Tools:** GitHub Actions API (via MCP), text matching against pattern catalog
- **Eval:** Replay 10 historical CI failures; agent matches ≥8 to correct fix pattern
- **Repo:** Both

#### 6. pre-push-validating
- **Role:** Runs smart pre-push v3 file→test mapping. Blocks push if any mapped test fails or `tsc --noEmit` errors
- **Tools:** Already exists as `.githooks/pre-push`; agent wraps it for Claude Code dispatch
- **Eval:** Tests file mapping correctness against `fix_patterns_P060_P061_final.md` documented map
- **Repo:** Both

### Tier 2 — Important (build round 2)

#### 7. code-writing
- **Role:** Writes code to specs. Currently Farhod+chat-Claude do this; promote to versioned agent
- **Tools:** All file tools, MCP for repo access
- **Boundary:** Does NOT decide architecture — only implements approved specs
- **Repo:** Both

#### 8. test-writing
- **Role:** Writes Playwright/pytest specs matching fix patterns + ISTQB CT-AI rules
- **Inputs:** Spec from code-writing or human direction
- **Output:** Test file + appropriate tags (@real-api, etc.)
- **Repo:** Both

#### 9. doc-writing
- **Role:** Keeps CLAUDE.md, AGENTS_ADDENDUM.md, fix_patterns.md, README.md consistent. Updates after each agent or feature ships
- **Trigger:** Code or architecture change merged to main
- **Repo:** Both

#### 10. git-managing
- **Role:** Validates ci.yml (line 1 check, forbidden patterns), enforces atomic commits, never mixes HV/HR in same commit
- **Tools:** Git CLI, pattern matchers from CI_WORKFLOW_TEMPLATE.md
- **Repo:** Both

#### 11. upskilling
- **Role:** Reads `self_upskilling.md` watchlist → surfaces matches when current tasks align → never unsolicited
- **Tools:** Pattern matching, web search for cited resources
- **Watchlist source:** AGENTS_ADDENDUM.md Self-Upskilling section
- **Repo:** Both

---

## Build sequence (post-Hajj)

**Phase A — Foundation (week 1 of return, ~06/06–06/12)**
1. orchestrating agent skeleton (no dispatch yet, just reads tasks)
2. tts-validating scripts (SKILL.md already exists)
3. ci-monitoring agent (the immediate productivity win)

**Phase B — Validation layer (week 2, ~06/13–06/19)**
4. stt-validating
5. ab-comparing
6. pre-push-validating (wrap existing hook)

**Phase C — Implementation layer (week 3, ~06/20–06/26)**
7. code-writing
8. test-writing

**Phase D — Maintenance layer (week 4, ~06/27–07/03)**
9. doc-writing
10. git-managing

**Phase E — Growth (week 5+, ~07/04 onward)**
11. upskilling

**First production dispatch:** target 07/04/2026 — first agentic daily reel post via orchestrator at 06:00 UTC.

---

## Agent-to-agent contracts

Each agent has a defined input schema and output schema. Contracts live in `agents/<name>/references/contract.md`.

**Example — tts-validating output schema:**
```json
{
  "agent": "tts-validating",
  "version": "v1",
  "case_id": "string",
  "result": "pass | fail",
  "failed_step": "step_1_contract | ... | null",
  "diagnostics": { ... },
  "warnings": []
}
```

Orchestrator reads `result` field. If `fail`, applies escalation policy from `agents/orchestrating/references/escalation-matrix.md`.

---

## Self-improvement loop

Per Self-Upskilling pattern in AGENTS_ADDENDUM.md:

1. Each agent runs `evals/` on its own changes (Anthropic Skills convention)
2. Failure surfaces patterns → fix patterns get added → `doc-writing` agent updates `fix_patterns.md`
3. `upskilling` agent surfaces external resources matching current task → human approves integration → SKILL.md gets updated
4. Eval set grows with each fixed bug → regression coverage compounds

End state: the agent system gets demonstrably more reliable each month as the eval corpus and pattern catalog grow.

---

## Risks + mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Agent produces wrong code → CI catches, doc-writing flags pattern | High | CI Green Gate (already enforced) |
| Agent costs spiral (parallel dispatch × API calls) | Medium | Cost alerts; orchestrator throttles parallelism |
| Agent hallucinates a "fix" that breaks unrelated code | Medium | pre-push-validating + ci-monitoring both gate |
| Two agents make conflicting changes | Low | git-managing serializes commits |
| Agent leaks secrets in commit | Low | git-managing + gitleaks pre-push |
| Agent generates religiously incorrect content | **Critical** | ab-comparing (Claude+ChatGPT+Kimi) flags divergence; human approval required for hadith content always |

---

## Human-in-the-loop principles

This is sadaqa jariyah work. Religious correctness depends on human judgment.

**Hard rules (no agent autonomy):**
- ANY new hadith verdict requires human approval before publishing
- ANY new translation requires native speaker review (or trusted source)
- ANY public reel content requires human listen-test before posting
- ANY Telegram channel post requires human approval
- ANY security fix touches a human reviewer

**Soft rules (agent autonomous, human notified):**
- CI failure diagnosis
- Code refactoring within existing tests
- Doc updates following code changes
- Test generation from specs
- Eval set expansion

**Human-only (no agent involvement):**
- Architecture decisions
- New hadith sourcing
- Channel branding
- Monetization strategy
- Hiring or external partnerships

---

## Open questions for post-Hajj design session

- Does Claude Code "agent view" support cross-session state? (Email implied yes — verify)
- Should agents share a common Supabase `agent_log` table for cross-agent observability?
- What's the rate limit policy for parallel agent dispatch on the $20 Agent SDK credit?
- Should agents have read access to each other's eval results for shared learning?
- When does the Kimi adapter get built — does Moonshot have a TS SDK or do we wrap HTTP directly?

---

## References

- Anthropic Skills documentation: https://docs.claude.com (verify post-Hajj)
- *30 Agents Every AI Engineer Must Build* — Imran Ahmad (book + GitHub repo)
- Speechmatics SWER paper — referenced in tts-validating SKILL.md
- AGENTS_ADDENDUM.md — universal agent rulebook
- HR-AGENTS.md, AGENTS.md — per-project orchestration rules
- fix_patterns.md (HV + HR) — pattern catalog the ci-monitoring agent uses

