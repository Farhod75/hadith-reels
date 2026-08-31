# Agent Fleet Roadmap
> **Status 2026-08-31:** the dates below are the original post-Hajj plan and have
> passed. 1 of 13 agents is built (asset-auditing, P117); tts-validating has a
> SKILL.md and no scripts. The fleet was deferred through August in favour of
> shipping reels — 57 to date, from 15 hadiths. Re-scope before building.

The plan for building the autonomous agent system for HV + HR.

**Designed:** May 15, 2026
**Build start:** 06/06/2026 (post-Hajj)
**Target completion:** First production agent dispatch — 30 days post-Hajj

---

## Goal

Transform HV+HR from "Farhod manually drives each task" to "Farhod approves agent-proposed work in a human-in-the-loop." The user (Farhod) stays in the decision seat. The agents do the implementation, validation, and reporting.

**Concretely:**
- Each day's reel is assembled, linted and staged by 06:00 UTC, awaiting human approval
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
| **Skills (KNOWLEDGE)** | Each of the 12 agents below is a Skill |
| **MCP (ABILITY)** | Agents expose themselves as MCP tools for cross-session dispatch |
| **Subagents (DELEGATION)** | Orchestrator uses Claude Code "agent view" to dispatch specialists in parallel |
| **Hooks (AUTOMATION)** | `.githooks/pre-push` enforces things LLMs can't be trusted to remember |
| **CLAUDE.md (CONTEXT)** | Project-level config loaded every session |
| **Plugins (PACKAGING)** | Future: bundle the fleet for team distribution or open-source |

---

## The 12 agents

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

#### 12. asset-auditing

- **Status:** BUILT 2026-08-15 (P117). `assets/asset-registry.json` +
  `scripts/audit-assets.py`, gated into both render paths. Registry is JSON
  rather than Supabase for now — 27 rows, reviewable in a git diff, single
  writer. Move to the DB when agents start writing to it.
- **Role:** Validates INHERITED assets, not generated output. Every file in `out/backgrounds/`, `out/refs/` and the mascot set carries a recorded classification (what it contains) and an approval (who cleared it, for which lane, when). Blocks a render that reaches for an asset not approved for that lane.
- **Why it is distinct from the other ten:** every existing agent inspects something the pipeline just produced. This one inspects what the pipeline reuses. Generation-time review cannot catch a defect that entered the library before generation — which is why 26 reels shipped with it.
- **Checks v1:** (a) asset is in the registry; (b) approved for the requesting lane (kids | adults); (c) audio beds carry an instrumentation classification (vocal-only | vocal+daf | ambience | instrumental-RETIRED); (d) flags any file in `out/backgrounds/` absent from the registry.
- **Tools:** registry table in Supabase (same DB as the reel log, per principle 3 — not markdown), ffprobe for technical metadata, render-reel.ps1 / make-kids-reel.ps1 hook for the gate.
- **Eval:** given the 12-file August 2026 library plus the 5 retired instrumental beds, correctly admits the 12 and refuses all 5; refuses an unregistered file dropped into the folder.
- **Boundary:** classification is HUMAN-entered. The agent enforces a recorded judgement; it does not decide whether an instrument is permissible.
- **Repo:** HR

#### 13. reel-producing

- **Status:** SCOPED 2026-08-31, not built. Added after the fleet was found to
  contain no agent that produces a reel — all twelve above validate or maintain,
  while the roadmap's finish line was an autonomous daily reel post. The
  orchestrator would have had nothing to dispatch.
- **Role:** Drives the text half of the reel pipeline for one language, from
  hadith selection to a staged render command. Stops at every human gate.
- **Repo:** HR
- **Tier:** 1 — highest daily return of anything unbuilt

**Does:**
1. Takes hadith number + language + style + mascot
2. Generates the four blocks (S/M/H/C)
3. Checks them against the recurring-defect table in
   `reel-creation-pipeline.md`, reporting each hit with the block and the line
4. Pulls the matn from the correct DB column (`text_uzbek_cyrillic` for UZ;
   `hadith_number` is TEXT and must be quoted) — never from the caption, since
   that compares generated text against generated text and hides a bad row
5. Writes `draft.txt` in S:/M:/H:/C: form
6. Runs `lint-content.py` and reports the output verbatim
7. Picks a nasheed from the tracker's usage table — least-used, not used in this
   language recently, not already used in this set — and states the reason
8. Assembles the `make-kids-reel.ps1` / `render-reel.ps1` command
9. **Stops.**

**Never:** clicks Generate narration · answers the Fabric or Kling gate ·
publishes to any platform · edits the tracker · picks the hadith itself.

**Human gates, unchanged:** content review before TTS · narration listen ·
the paid-generation confirmation · watching the finished reel · publishing.

**Why the boundary sits there:** every defect that mattered on the #6446 kids
set was caught by reading or listening — an attribution boundary left open, the
қаноат drift surviving a corrected DB column, «оз» voiced as «ўз». The linter
passed all four languages clean. The agent removes the mechanical work around
the review; it does not become the review.

**Eval set — ground truth from R054–R057, 2026-08-31:**
| Case | Must flag |
|---|---|
| EN | attribution boundary left open after "The Prophet ﷺ said:"; Allah absent from moral |
| RU | isnad line placed in the story block; moral rendered as self-talk, no Allah |
| UZ | H drifts to «нафснинг қаноати» against a corrected DB column; «деди» singular; caption quote Latin against Cyrillic body |
| TJ | «гуфт» singular; қаноат drift in both S and H; «дилаш» where the matn says nafs |

Threshold v1: flags ≥3 of 4 sets, no false positive on a clean block.

**Explicitly out of reach:** «оз» → «ўз» is a TTS artifact, audible only after
narration. No text-stage agent catches it. It stays human.

**Depends on:** the per-language E2E checklist in `reel-creation-pipeline.md`
(written 2026-08-31) — that document IS this agent's specification.
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

**First production dispatch:** **First production dispatch:** first agentic reel ASSEMBLY — generated, linted,
`draft.txt` synced, render command staged, awaiting human review. Publishing is
never dispatched.

**The hard rules below are the ceiling on this entire document.** Where any goal
above appears to grant an agent autonomy over reel content or channel posts, the
hard rule wins. This was a live contradiction until 2026-08-31: the goal section
promised autonomous daily posting while the hard rules forbade exactly that. Same
specification-conflict shape as P101, P103, P122 and P133 — a document demanding
what it elsewhere forbids. Fixed by removing the demand, not by strengthening the
prohibition.

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
5. An agent's own eval failures update its own SKILL.md, versioned in place.
   Nothing above does this — points 2 and 3 route learning into `fix_patterns.md`
   and in from outside, but no step corrects a spec against its own behaviour.
   `tts-validating` v1 described a dual-provider stack that had not existed
   since June and would have had anyone implementing it build against a system
   that was gone. It was corrected in August by a human rereading it, not by
   this loop.

> **Status 2026-08-31:** this loop does not run. It requires `evals/`
> directories, `doc-writing` and `upskilling` — none of which exist. `agents/`
> contains three SKILL.md files and no scripts. The end state below describes a
> machine whose parts are not yet built.

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
| Approved asset carries a defect nobody re-checks | **High** | No agent covers this today. Proven 2026-08-13: all 7 background beds were instrumental, cleared once in May and reused across 26 reels. ab-comparing inspects generated TEXT and would have passed every one. Needs asset-provenance checking (see agent 12). |

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

