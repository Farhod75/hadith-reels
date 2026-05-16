## ════════════════════════════════════════════════════════
## ADDENDUM TO AGENTS.md (both HV and HR)
## Append to the bottom of each AGENTS.md
## ════════════════════════════════════════════════════════

## ── GOLDEN RULE: CI GREEN GATE ──────────────────────────
## Added: May 2026 — agreed with Farhod
## ─────────────────────────────────────────────────────────

### The rule
**NEVER move to the next task until CI is green.**

This applies to:
- Every feature build
- Every bug fix
- Every doc update
- Every spec change
- Moving from HV tasks to HR tasks (or vice versa)
- Starting any new Phase

### Why
- Red CI = broken code in main branch = next push builds on broken foundation
- Moving forward with red CI caused 10+ wasted CI runs (P037–P048)
- Each wasted run = 3-5 minutes + context switching + debugging time

### How to enforce
Before declaring any task complete, the orchestrator MUST:
1. Confirm CI run number from GitHub Actions
2. Confirm green ✅ status
3. Only then mark task done and move to next

### Exception
Documentation-only commits (CLAUDE.md, fix_patterns.md, README.md):
- These cannot break CI
- Can be pushed while watching another CI run
- But still must not contain code changes

### What to do if CI is red
1. STOP — do not start next task
2. CI monitor agent reads the failure
3. Check fix_patterns.md first
4. Fix the failing test
5. Push fix
6. Wait for green
7. THEN move forward

## ── NEVER-DO LIST ADDITIONS (P046–P048) ─────────────────

- P046: Never add language-speech or ElevenLabs steps to CI push workflow
- P047: Never use getByText() or filter({ hasText }) on buttons with emojis
- P048: Never test UI label text — test functional outcome instead
- P048: For emoji tab buttons use page.evaluate() to click by textContent
- P048: For lang buttons scope to header: page.locator('header').locator('button', { hasText: 'EN' })

## ── TEST DESIGN CHECKLIST (before writing any new test) ──

Ask these questions before writing each test:
1. Am I testing a label/text or a functional outcome? → Test outcome
2. Does the element I'm targeting contain an emoji? → Use evaluate()
3. Am I calling a real external API? → Mock it or tag @real-api
4. Is this locator scoped to a specific container? → If not, scope it
5. Would this test pass if the feature was broken? → If yes, rewrite it

## ── FILE DELIVERY PROTOCOL ──────────────────────────────
## Added: May 2026 — agreed with Farhod after multi-hour debug session
## ─────────────────────────────────────────────────────────

### The rule
**Every file Claude produces must be a complete, ready-to-paste artifact — never a partial diff, never a snippet requiring the user to "fill in the rest."**

### Why
- Partial snippets with `...` placeholders caused a build break and ~2 hours of recovery work during the P072 session
- Farhod uses Windows + PowerShell + VS Code; pasting partial diffs across files is error-prone
- The `Downloads → PowerShell copy` workflow is faster and less error-prone than manual editing
- This rule is also a stated user preference; codifying it here means new Claude sessions adopt it without being reminded

### Mandatory delivery format

Every file Claude produces follows this pattern:

1. **Generate as a complete artifact** — full file content, no `...`, no `// rest unchanged`, no `{/* existing classes */}` placeholders
2. **Filename prefix by project:**
   - `hr-<name>` for files destined for the Hadith Reels repo
   - `hv-<name>` for files destined for the Hadith Verifier repo
   - No prefix for universal/shared files
3. **Assume download location:** `$env:USERPROFILE\Downloads\` on Windows
4. **Provide a single PowerShell block** that:
   - Changes directory to the correct project root
   - Creates any missing folders with `New-Item -ItemType Directory -Force`
   - Moves the file from `Downloads` to the final destination with `Move-Item -Force`
   - Renames it from the `hr-` / `hv-` prefix to the canonical name in-place
   - Ends with a `Get-ChildItem ... | Select-Object FullName` verification line
5. **Never use placeholder paths** like `C:\path\to\hadith-verifier` — always use the real paths:
   - HR: `C:\QA\Hadith verification AI app\hadith-reels`
   - HV: `C:\QA\Hadith verification AI app\hadith-verifier`

### Canonical PowerShell block template

```powershell
cd "C:\QA\Hadith verification AI app\<project>"

# Create folders (use -Force; idempotent)
New-Item -ItemType Directory -Force -Path "<folder>" | Out-Null

# Move file from Downloads, renaming off the hr-/hv- prefix
Move-Item "$env:USERPROFILE\Downloads\<hr|hv>-<filename>" `
          "<destination-folder>\<filename>" -Force

# Verify
Get-ChildItem -Recurse "<destination-folder>" | Select-Object FullName
```

### Banned patterns (Claude must never produce these)

- `...` as a placeholder inside JSX, TS, JS, Python, or any code block intended for pasting
- `// rest of file unchanged` / `# ... (existing code)` annotations in delivered artifacts
- Partial className strings: `className="w-full bg-slate-700 ..."` ← the literal `...` becomes part of the source on paste
- Placeholder paths: `C:\path\to\...`, `/your/repo/here`, `<your-token>` inside PowerShell that's meant to be executed as-is
- "Find this section and replace it with..." instructions when a full-file artifact would be unambiguous

### When a snippet IS appropriate

Inline code blocks for **discussion or explanation** can use ellipses and abbreviations freely. The rule applies only to artifacts intended for the user to download, paste, or copy into project files.

Example — fine:
> "The route accepts `{ text, lang, style }` and returns `audio/mpeg`. The relevant block is roughly `const { text, lang, ... } = await req.json()` — the rest just sets up the fetch call."

Example — NOT fine (this is a delivered artifact masquerading as a snippet):
> "Replace your input element with this: `<input ... suppressHydrationWarning />`"

The second form caused the P072 build break. Don't do it.

## ── SESSION STARTUP PROTOCOL ────────────────────────────
## Added: May 2026 — agreed with Farhod after governance audit
## ─────────────────────────────────────────────────────────

### The rule
**In every new chat, Claude reads all governance files in project knowledge BEFORE giving the first technical direction.**

### Mandatory pre-direction reads

In order, the first turn of any new chat must include reading:

1. `CLAUDE.md` — HV project contract
2. `hr-CLAUDE.md` — HR project contract
3. `AGENTS_ADDENDUM.md` — this file (universal agent rules)
4. `HR-AGENTS.md` — HR agent orchestration rulebook
5. `QA_STANDARDS_ADDENDUM.md` — QA standards additions
6. `CI_WORKFLOW_TEMPLATE.md` — CI rules and forbidden patterns
7. `fix_patterns.md` — HV patterns P037 onwards
8. `fix_patterns_P060_P061_final.md` — most recent HV patterns and smart pre-push v3 mapping
9. `hr-fix-patterns.md` — HR patterns P046 onwards
10. `README.md` — HV public-facing contract

If the chat is for HR only, files 1, 7, 8, 10 still get read because HV and HR share Supabase and several patterns are cross-applicable.

### Confirmation required

Claude must explicitly confirm to the user: "Governance files read: <list>". No technical direction is given before this confirmation.

If a governance file referenced above is missing from project knowledge, Claude must flag it and ask the user whether to proceed without it, rather than silently working from incomplete context.

## ── PRIORITY-BASED TASK SEQUENCING ──────────────────────
## Added: May 2026 — agreed with Farhod
## ─────────────────────────────────────────────────────────

### The rule
**Before any multi-step plan, Claude produces a prioritized task list scored on urgency × impact × importance.**

### Format

For each pending task, score on three axes (1–5 each):

- **Urgency:** Does it block work today? Has a deadline?
- **Impact:** How many downstream tasks does it unblock or de-risk?
- **Importance:** Strategic alignment with the user's stated goals?

Tasks execute in descending total score order. Ties broken by user priority.

### Mandatory per-direction declaration

Before giving any technical direction, Claude must state one of:

- "This direction advances priority task #N (<name>)."
- "This direction does NOT advance any priority task; it is cleanup/polish. Recommend deferring."
- "This direction is a prerequisite for priority task #N because <reason>."

This prevents Claude from chasing low-priority cosmetic issues while higher-priority business work is blocked. The P072 hydration-warning detour (cosmetic dev-only browser-extension noise) cost ~2 hours that should have gone toward UZ kids reel posting.

## ── ATOMIC COMMIT DISCIPLINE ────────────────────────────
## Added: May 2026 — agreed with Farhod after working-tree audit
## ─────────────────────────────────────────────────────────

### The rule
**Before any commit, run `git status` and audit every modified or untracked file. No `git add .` unless every change in the tree belongs in the same atomic commit.**

### Why
- Working trees accumulate stale or in-progress work over sessions
- A blind `git add .` mixes unrelated changes, violates "one task per commit," and tangles bisects
- HR-AGENTS.md rule: "Never mix HV and HR changes in same commit" — same principle, smaller scale

### Audit checklist

Before any commit:

1. Run `git status` — list every modified and untracked file
2. For each file, answer: "Does this belong in the current commit?"
3. Stash anything that doesn't: `git stash push <file>` or `git stash push -m "<reason>"`
4. Confirm `.gitignore` covers transient junk: `test-audio.mp3`, `test-results/`, `.env.local`, build outputs
5. Run `git diff --staged` after `git add` — verify the diff matches the commit message
6. Only then commit

### Pre-commit hooks supplement this

Smart pre-push v3 catches some of these issues automatically (file → test mapping, tsc check). The audit is upstream — it catches things hooks can't, like "this file is intentionally uncommitted because it's WIP."

## ── ANTHROPIC SKILLS FORMAT FOR NEW AGENTS ──────────────
## Added: May 2026 — agreed with Farhod after agent gap analysis
## ─────────────────────────────────────────────────────────

### The rule
**All new agents follow the Anthropic Skills canonical structure.**

### Folder structure (mandatory)

```
agents/<gerund-name>/
├── SKILL.md              — required: YAML frontmatter + body
├── references/           — optional: lazy-loaded supporting docs
├── scripts/              — optional: execution code (TS or Python)
├── assets/               — optional: static resources
└── evals/                — recommended: self-validation eval set
    └── evals.json
```

### SKILL.md YAML frontmatter (mandatory)

```yaml
---
name: <gerund-form-lowercase-hyphens>
description: <when to trigger, what it does, ≤1024 chars, "pushy" wording to combat undertriggering>
---
```

Constraints:
- `name`: max 64 chars, lowercase letters + numbers + hyphens only, no "anthropic" or "claude"
- `description`: max 1024 chars, must include both *what* the skill does and *when* Claude should use it

### Progressive disclosure principle

SKILL.md body stays short and decisive (target: ~200 lines). Long pattern catalogs, schemas, and supporting examples live in `references/` and load only when the workflow requires them. This preserves Claude's context window.

### Self-validation

Every agent must have an `evals/evals.json` defining baseline test cases. The agent runs its own evals when SKILL.md or any reference is changed. Eval pass criteria are stated in the SKILL.md.

### Per-repo, not shared

Per HR-AGENTS.md infrastructure decision: agents live in each repo's `agents/` folder. No shared dependency between HV and HR for agent code. Duplication is intentional — keeps CI self-contained per project.

## ── CROSS-LLM A/B VALIDATION ────────────────────────────
## Added: May 2026 — agreed with Farhod for ab-comparing agent
## ─────────────────────────────────────────────────────────

### The rule
**A/B model comparison uses Claude + ChatGPT + Kimi, not Claude-vs-Claude variants.**

### Why
- Intra-Claude comparison (Sonnet vs Haiku) catches some variance but shares Claude's blind spots
- Cross-LLM comparison surfaces Claude-specific behavior — e.g. Islamic jurisprudence edge cases where Claude is more cautious than ChatGPT or Kimi
- Three models give a 2-of-3 majority signal: when 2 agree and 1 disagrees, route the disagreement to human review

### Required adapters

The `ab-comparing` agent (when built) must support:
- Anthropic Claude (current Sonnet via existing `ANTHROPIC_API_KEY`)
- OpenAI ChatGPT (via existing `OPENAI_API_KEY` — already set in HR for Nova/Onyx TTS)
- Moonshot Kimi (separate `KIMI_API_KEY` to be added)

### What gets validated

Reel content: story, moral, seerah_context, caption, hashtags
Hadith verdicts: severity, red_flags, suggested_comment, references
Translations: when content is rendered in non-source language

### What does NOT get validated by A/B

Voice/audio quality — that's the `tts-validating` agent's job
Visual rendering — that's a future `frontend-validating` agent
Anything where Claude is the only model with vision (e.g. Vision API outputs)

## ── SELF-UPSKILLING WATCHLIST ───────────────────────────
## Added: May 2026 — agreed with Farhod for autonomous agent growth
## ─────────────────────────────────────────────────────────

### The rule
**Claude maintains a `self_upskilling.md` watchlist of resources to study for relevant patterns. Surfaces matches when current tasks align with watchlist topics.**

### Current watchlist (May 2026)

| Resource | Type | Relevance |
|---|---|---|
| *30 Agents Every AI Engineer Must Build* — Imran Ahmad | Book + GitHub | Agent taxonomy: planning, memory-augmented, knowledge retrieval, explainable, domain-specific. Maps to our 11-agent fleet. |
| Anthropic Skills official guide | Documentation | Canonical SKILL.md format, progressive disclosure, evals. Already adopted. |
| Specialist-stacking pattern (GenAI Works article) | Reference | Confirms HR's architecture (Claude + ElevenLabs + Nova + Whisper + Kling + Remotion). |
| CT-GenAI certification syllabus | Certification | Farhod's in-progress cert; surfaces testing patterns for generative AI. |
| AWS Bedrock for Claude deployment | Course | For Phase 5+ when Vercel becomes a cost ceiling. |
| DeepLearning.AI — Prompt Engineering, Agentic AI | Course | For agent orchestration patterns. |

### Surfacing rule

When a task aligns with a watchlist topic, Claude states at the start of the response: "Watchlist match: <resource> — relevant because <reason>." User decides whether to integrate the pattern.

This is opt-in surfacing, not unsolicited recommendation. No nagging.
