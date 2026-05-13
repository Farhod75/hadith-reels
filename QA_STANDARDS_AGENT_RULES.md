# QA_STANDARDS_AGENT_RULES.md
# Universal AI Agent Quality Standards
# Version: 1.0 — May 2026
# Author: Farhod Elbekov (ISTQB CT-AI · CTFL v4.0 · CT-GenAI in progress)
#
# PURPOSE: Paste this file into ANY project. All agents in that project
# inherit these rules automatically when Claude Code reads this file.
#
# SOURCES:
#   - ISTQB CT-AI syllabus (March 2026)
#   - ISTQB CTFL v4.0 syllabus (Feb 2026)
#   - ISTQB CT-GenAI syllabus (in progress)
#   - Anthropic Claude prompt engineering best practices
#     https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
#   - Playwright best practices: https://playwright.dev/docs/best-practices
#   - pytest best practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html
#   - OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
#   - fix_patterns.md (this repo) — 43 patterns from real CI failures
#   - github.com/Farhod75/engineering-standards (public standards repo)
#   - github.com/Farhod75/ai-testing-enterprise (enterprise AI testing framework)
#   - github.com/Farhod75/hadith-verifier (primary portfolio project)
# ============================================================

## ════════════════════════════════════════════════════════
## SECTION 1: CORE PRINCIPLES (apply to ALL agents)
## ════════════════════════════════════════════════════════

### 1.1 Read before write
- ALWAYS read the current file before editing it
- NEVER replace a file without checking all content-type paths it handles
- NEVER change unrelated files during a bug fix
- ALWAYS compare old vs new before replacing working code

### 1.2 One concern per output
- One fix per commit
- One pattern per fix_patterns.md entry
- One test per assertion
- One file per agent task output
- NEVER mix two projects (HV + HR) in the same commit or output

### 1.3 Documentation is not optional
- Every fix → fix_patterns.md entry in the SAME message/commit
- Every feature → CLAUDE.md update in the SAME commit
- Every new API field → audit_spec.ts update in the SAME commit
- If a doc update is skipped, the task is not complete

### 1.4 Human decides, AI flags
- No auto-delete, no auto-ban, no auto-moderation
- AI agents flag content and score severity
- All final moderation actions require human review
- This applies to both HV and HR

## ════════════════════════════════════════════════════════
## SECTION 2: CODE AGENT RULES
## Source: CTFL v4.0 · Playwright best practices
## ════════════════════════════════════════════════════════

### 2.1 Before writing any code
1. Read the target file first (view tool or Get-Content)
2. Check ALL content-type paths (multipart/form-data AND application/json)
3. Search for existing patterns in fix_patterns.md
4. Identify minimum scope — touch as few lines as possible

### 2.2 Route/API rules (from P041)
- ALWAYS handle BOTH multipart/form-data AND application/json in routes that accept files
- NEVER rewrite a route without checking what content types it receives
- ALWAYS test image upload AND text-only paths after any route change
- Pattern: `if (contentType.includes('multipart/form-data')) { formData } else { json }`

### 2.3 State management rules (from P042)
- When adding a new state variable, check all places that SHOULD sync to it
- Use useEffect to sync dependent state when source state changes
- Example: appLang change → replyLang must auto-sync

### 2.4 Language enforcement rules (from P018, P039)
- langInstruction must cover ALL output fields, not just suggested_comment
- Use appLang (UI language) for search queries, NOT replyLang (analyze tab language)
- UZ Cyrillic requires explicit "EVERY CHARACTER MUST BE CYRILLIC" instruction
- Tajik → falls back to Russian for TTS (no native TJ TTS voice available)

### 2.5 Supabase rules (from P001)
- ALWAYS use SUPABASE_SERVICE_ROLE_KEY server-side — NEVER anon key
- RLS must be DISABLED on flagged_posts (silently blocks reads without error)
- NEVER use .single() on queries that may return 0 or multiple rows
- Always verify with: SELECT COUNT(*) FROM table_name; after changes

## ════════════════════════════════════════════════════════
## SECTION 3: TEST AGENT RULES
## Source: ISTQB CT-AI · CT-GenAI · CTFL v4.0 · fix_patterns P037–P043
## ════════════════════════════════════════════════════════

### 3.1 THE MOST IMPORTANT RULE (from P043)
**NEVER call real external AI APIs (Claude, OpenAI, ElevenLabs) in CI push tests.**
- Use page.route() to mock API responses in Playwright
- Use monkeypatch or responses library to mock in pytest
- Real API tests MUST be tagged @real-api and excluded from CI workflow
- Reason: AI API latency (15-30s) + CI runner slowness = guaranteed timeout

```ts
// ALWAYS do this for any test that shows AI output:
async function mockAnalyze(page, lang = 'en') {
  await page.route('**/api/analyze', route =>
    route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify(MOCK_RESPONSE(lang)) })
  )
}
```

### 3.2 Locator rules (from P037, P038)
- NEVER use `.last()` or `.first()` on generic selectors — non-deterministic in CI
- ALWAYS scope locators to the specific container, not the entire page
- Use label text as anchor → walk to card → query down for target element
- NEVER use `.bg-gray-50.rounded-lg.last()` — multiple elements share this class

```ts
// WRONG (P038):
const text = await page.locator('.bg-gray-50.rounded-lg').last().textContent()

// RIGHT (P038v3):
const text = await page.evaluate(() => {
  const label = Array.from(document.querySelectorAll('div'))
    .find(el => el.className?.includes?.('uppercase') &&
                el.textContent?.includes('Ready-to-post comment'))
  const card = label?.closest('.bg-white.rounded-xl')
  return card?.querySelector('.bg-gray-50.rounded-lg')?.textContent?.trim() || ''
})
```

### 3.3 Timeout rules (from P040)
- Default Playwright timeout: 30000ms for mocked tests
- Real API tests: 120000ms maximum
- If a test needs >30s without mocking → it is testing the wrong thing
- After adding new fields to AI prompt → increase timeout OR add mock

### 3.4 Test separation (ISTQB CT-AI principle)
- UI rendering tests → Playwright with mocked API (fast, deterministic)
- AI output quality tests → pytest against production (real API, scheduled)
- CI push tests → ONLY mocked tests (never real external calls)
- Manual validation → @real-api tagged tests (run explicitly, not on push)

### 3.5 AI-specific test patterns (CT-AI syllabus)
- Non-determinism: test RANGES not exact values (confidence: high|medium|low)
- Hallucination: verify URLs contain valid domain, not exact path
- Language: check CHARACTER RANGES not exact strings (Cyrillic regex, Arabic unicode)
- Severity: test mapping logic separately from AI output (deterministic function)
- Prompt injection: send OWASP LLM Top 10 payloads, verify verdict stays correct

### 3.6 Audit spec rules (CT-GenAI)
- audit_spec.ts runs post-deploy ALWAYS — never skip it
- When a new field is added to AI response → add audit test for it same day
- Audit tests call REAL API against production (not mocked)
- Run: `$env:BASE_URL="https://hadithverifier.com"; npx playwright test tests/audit_spec.ts`

### 3.7 Debug output in tests
- Add `__LABEL_NOT_FOUND__` style sentinel returns in evaluate() blocks
- Use `expect(text, \`Selector failed: ${text}\`).not.toMatch(/^__.*__$/)` pattern
- This makes CI failures self-diagnosing — exact step that broke is in the error

## ════════════════════════════════════════════════════════
## SECTION 4: DOC AGENT RULES
## Source: Anthropic Claude Code best practices · engineering-standards repo
## ════════════════════════════════════════════════════════

### 4.1 Fix pattern entry format (ALWAYS follow this)
```
## ════════════════════════════════════════════════════════
## PATTERN {N}: {short title}
## ════════════════════════════════════════════════════════
**ID:** P{N}
**Type:** {Bug fix | Test fix | Architecture fix | UX fix}
**File:** {file path}
**Commit:** {conventional commit message}
**Symptom:** {exact error message or behavior}
**Root cause:** {why it happened}
**Fix:** {code snippet showing wrong vs right}
**Rule going forward:** {what to check next time}
**Status:** FIXED
```

### 4.2 CLAUDE.md must always contain
- Current test counts (Playwright + pytest)
- Current CI status (last N runs, green/red)
- All known bugs with status
- All pending features with status
- Exact run commands for Windows PowerShell
- All env vars (keys redacted, names present)
- Last updated date

### 4.3 README.md rules
- NEVER leave the Next.js boilerplate README in any project
- README must have: live URL, tech stack, quick start, feature status table
- Feature status table uses: ✅ Built | ⏳ Pending | 🔴 Not Started

### 4.4 CHANGELOG.md format (semantic versioning)
```
## [Unreleased]
### Added
- seerah_context field in analyze route (Ar-Raheeq Al-Makhtum)
### Fixed
- P041: FormData handler dropped in route rewrite
- P042: replyLang not synced to appLang on language switch
### Changed
- Playwright tests now mock API in CI (P043)
```

## ════════════════════════════════════════════════════════
## SECTION 5: GIT AGENT RULES
## Source: Conventional Commits spec · CTFL v4.0 traceability
## ════════════════════════════════════════════════════════

### 5.1 Commit message format (ALWAYS)
```
{type}: {description} ({pattern-id})

Types: feat | fix | docs | test | refactor | chore | style
Examples:
  feat: add seerah_context storytelling field (Ar-Raheeq Al-Makhtum)
  fix: restore FormData image upload in analyze route (P041)
  test: mock API in CI language tests (P043)
  docs: update CLAUDE.md test counts + CI history
```

### 5.2 Commit scope rules
- One logical change per commit
- NEVER mix HV and HR changes in one commit
- NEVER mix feature + test + docs in one commit
- Test file + fix_patterns entry CAN be in same commit (they are one concern)

### 5.3 Windows PowerShell deploy sequence
```powershell
# Standard fix deploy:
git add {specific files only — never git add .}
git commit -m "fix: {description} ({pattern-id})"
git push origin main
# Then watch CI — do not push again until CI result is known

# Vercel env vars (Production + Preview separately):
vercel env add KEY_NAME production
vercel env add KEY_NAME preview
# NEVER add Development via CLI — use .env.local
```

### 5.4 Never do
- `git add .` — always name specific files
- Push again before previous CI run completes
- Mix HV + HR in same push

## ════════════════════════════════════════════════════════
## SECTION 6: CI MONITOR AGENT RULES
## Source: fix_patterns.md P037–P043 · GitHub Actions best practices
## ════════════════════════════════════════════════════════

### 6.1 Diagnosis protocol
When CI fails:
1. Read the EXACT error line from CI log screenshot
2. Find the spec file + line number
3. Check fix_patterns.md for matching pattern FIRST
4. If pattern exists → apply known fix immediately
5. If no pattern → diagnose root cause before writing any code
6. NEVER trial-and-error patch the same test 3+ times — it means wrong diagnosis

### 6.2 Escalation rule
- Same test failing 3+ times in a row → stop patching, redesign the test
- Example: AR language test failed CI #122–#131 = 10 runs
  Should have mocked after run #124 — instead patched 7 more times
- Rule: if second patch attempt fails → the test architecture is wrong

### 6.3 CI run budget
- Each CI push should pass in ≤ 15 minutes
- If tests take >15 min → too many real API calls in CI suite
- Target: all CI push tests run in < 5 minutes (mocked)
- Real API tests: run separately, not on every push

### 6.4 Duplicate CI steps
- Two "Run E2E tests" steps = matrix strategy (chromium + firefox)
- Both must pass for CI to be green
- If only one fails → it is a browser-specific issue, not a code bug

## ════════════════════════════════════════════════════════
## SECTION 7: EXTERNAL KNOWLEDGE SOURCES
## Updated automatically as new sources are validated
## ════════════════════════════════════════════════════════

### 7.1 Primary standards (authoritative)
| Source | URL | Used for |
|---|---|---|
| ISTQB CT-AI syllabus | https://www.istqb.org/certifications/certified-tester-ai-testing | AI test design patterns |
| ISTQB CTFL v4.0 | https://www.istqb.org/certifications/certified-tester-foundation-level | Test levels, POM, data-driven |
| ISTQB CT-GenAI | https://www.istqb.org/certifications/certified-tester-generative-ai | GenAI output validation |
| Anthropic prompt engineering | https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview | Prompt design |
| Anthropic Claude Code | https://docs.anthropic.com/en/docs/claude-code | Agentic workflows |

### 7.2 Testing frameworks (implementation)
| Source | URL | Used for |
|---|---|---|
| Playwright best practices | https://playwright.dev/docs/best-practices | Locators, mocking, CI |
| Playwright page.route() | https://playwright.dev/docs/api/class-route | API mocking in tests |
| pytest documentation | https://docs.pytest.org/en/stable | Python test structure |
| axe-core / axe-playwright | https://github.com/dequelabs/axe-core | WCAG 2.1 AA audit |

### 7.3 Security standards
| Source | URL | Used for |
|---|---|---|
| OWASP LLM Top 10 | https://owasp.org/www-project-top-10-for-large-language-model-applications/ | Prompt injection, hallucination |
| OWASP API Security | https://owasp.org/www-project-api-security/ | API validation patterns |

### 7.4 Farhod's portfolio repos (primary upskill source)
| Repo | URL | What to learn from it |
|---|---|---|
| engineering-standards | https://github.com/Farhod75/engineering-standards | Public QA standards library |
| hadith-verifier | https://github.com/Farhod75/hadith-verifier | Primary portfolio — all patterns applied here |
| ai-testing-enterprise | https://github.com/Farhod75/ai-testing-enterprise | 135-test enterprise AI framework · 5 ISTQB levels |
| ct-ai-exam-prep | https://github.com/Farhod75/ct-ai-exam-prep | CT-AI + CT-GenAI question bank |
| hadith-reels | https://github.com/Farhod75/hadith-reels | HR project — applies all HV learnings |

### 7.5 AI/GenAI upskill sources (external)
| Source | URL | Topic |
|---|---|---|
| DeepLearning.AI prompt engineering | https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/ | Prompt patterns |
| DeepLearning.AI agentic AI | https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/ | Multi-agent systems |
| AWS Bedrock Claude | https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-claude.html | AWS Claude deployment |
| Anthropic cookbook | https://github.com/anthropics/anthropic-cookbook | Claude API patterns |
| LangChain docs | https://python.langchain.com/docs/get_started/introduction | Agent orchestration |
| AutoGen (Microsoft) | https://github.com/microsoft/autogen | Multi-agent frameworks |

### 7.6 Daily reading sources (agent upskill feed)
| Source | URL | Frequency |
|---|---|---|
| Anthropic news | https://www.anthropic.com/news | Weekly |
| ISTQB news | https://www.istqb.org/news | Monthly |
| Playwright releases | https://github.com/microsoft/playwright/releases | Per release |
| GitHub Actions changelog | https://github.blog/changelog/label/actions/ | Weekly |
| Hacker News AI | https://news.ycombinator.com/news | Daily |

## ════════════════════════════════════════════════════════
## SECTION 8: DAILY SKILL UPGRADE PROTOCOL
## How agents get smarter automatically
## ════════════════════════════════════════════════════════

### 8.1 The upgrade loop (runs on every CI push)
```
CI run completes (pass or fail)
  ↓
CI monitor agent reads result
  ↓
If fail: diagnose → fix → log to fix_patterns.md → commit
If pass: log "CI #{N} ✅" to CLAUDE.md → commit
  ↓
Next Claude Code session reads updated fix_patterns.md
  ↓
Agent task inherits all previous learnings automatically
```

### 8.2 Weekly upgrade tasks (manual, 10 min each Friday)
1. Check Playwright releases — any breaking changes to locator API?
2. Check Anthropic API changelog — new model? new features?
3. Review fix_patterns.md — any pattern that could be a general rule?
4. Update this file if a new rule emerges from the week's work
5. Push updated AGENTS.md to all active projects

### 8.3 Monthly upgrade tasks
1. Review ISTQB CT-GenAI updates — new test patterns?
2. Check OWASP LLM Top 10 — new vulnerability categories?
3. Review enterprise-standards repo — any new patterns to add?
4. Update QA_STANDARDS_AGENT_RULES.md version number

### 8.4 How to propagate updates to other projects
```powershell
# After updating this file in hadith-verifier:
Copy-Item "QA_STANDARDS_AGENT_RULES.md" `
  "..\hadith-reels\QA_STANDARDS_AGENT_RULES.md" -Force

Copy-Item "QA_STANDARDS_AGENT_RULES.md" `
  "..\idris-learning-app\QA_STANDARDS_AGENT_RULES.md" -Force

# Commit in each project separately
```

## ════════════════════════════════════════════════════════
## SECTION 9: PROJECT-SPECIFIC OVERRIDES
## Add project-specific rules below this line
## Do not modify sections 1-8 — those are universal
## ════════════════════════════════════════════════════════

### 9.1 Hadith Verifier (HV) overrides
- Islamic content: compassionate tone always, never accusatory
- Source tiers: Tier 1 (sunnah.com, dorar.net, hadeethenc.com) only for authentication
- Ar-Raheeq Al-Makhtum: storytelling/context only, NOT authentication source
- Language priority: UZ Cyrillic > UZ Latin > RU > AR > EN for Uzbek users
- Admin queue: human reviews all flagged posts — no auto-action ever

### 9.2 Hadith Reels (HR) overrides
- All hadiths must be sahih or hasan — never daif in reels
- Adults style: dark elegant, scholarly tone
- Kids style: bright, simple language, age 6-14
- Daily reel limit: 1 Adults + 1 Kids per day (cron job)
- Shared Supabase: never modify hadith_library schema without updating HV too

### 9.3 Idris Learning App overrides
- ASD-appropriate content: clear, structured, no ambiguity
- All AI responses must be validated for age-appropriateness
- Never use timer-based pressure in UI
- Accessibility: WCAG 2.1 AA minimum, AAA preferred

---
*Last updated: May 2026 · Farhod Elbekov · ISTQB CT-AI #26-CT-AI-00063-USA*
*Next review: June 2026*
## ════════════════════════════════════════════════════════
## ADDENDUM TO QA_STANDARDS_AGENT_RULES.md
## Section 6 additions — CI workflow rules (P044, P045)
## Append to bottom of QA_STANDARDS_AGENT_RULES.md Section 6
## ════════════════════════════════════════════════════════

### 6.5 CI yml must NEVER contain (P045)
These step types cause non-deterministic CI failures:
```yaml
# NEVER add these to push-triggered CI steps:
- name: Run Audit tests          # real Claude × 14+ calls
- name: Run language-speech tests # real ElevenLabs calls
- name: Run @real-api tests       # any tagged real-api tests
```

### 6.6 Correct CI yml structure (permanent template)
```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:             # manual trigger for audit
    inputs:
      run_audit:
        description: 'Run audit against production'
        default: 'false'
        type: choice
        options: ['false', 'true']

jobs:
  test:                         # runs on every push
    steps:
      - Run API tests            # mocked severity unit tests
      - Run E2E tests            # all page.route() mocked
      # NO audit step
      # NO language-speech step

  audit:                        # manual dispatch ONLY
    if: github.event_name == 'workflow_dispatch' && inputs.run_audit == 'true'
    steps:
      - Run audit_spec.ts        # real Claude, post-deploy
```

### 6.7 CI timeout budget
- Push CI timeout: 20 minutes maximum (was 55 — wasteful)
- If tests need >20 min → too many real API calls in CI suite
- Target: all CI push tests in <5 minutes

### 6.8 Deterministic vs non-deterministic test separation
ALWAYS ask: "Does this test need Claude to return a specific value?"
- YES → it is a non-deterministic test → mock it OR tag @real-api
- NO  → it tests deterministic logic → unit test it directly

Examples:
  getSeverity() → pure function → unit test (no Claude)
  UI renders verdict badge → rendering test → mock API response
  Claude returns valid enum → schema test → real Claude OK (just enum check)
  Claude returns Arabic text → language test → mock with Arabic MOCK_RESPONSE
  Claude returns compassionate tone → quality test → audit_spec (post-deploy)

### 6.9 How to run audit manually (two options — add to all project READMEs)
Option A — PowerShell (local):
```powershell
$env:BASE_URL="https://[your-production-url].com"
npx playwright test tests/audit_spec.ts --reporter=list
```

Option B — GitHub Actions manual dispatch:
1. GitHub → your repo → Actions tab
2. Select workflow "Hadith Verifier CI/CD"
3. Click "Run workflow" dropdown
4. Set run_audit = true
5. Click "Run workflow"

### 6.10 Spec file naming convention (P045 lesson)
ALWAYS use underscores in spec filenames — NEVER dots except the .spec extension:
  ✅ audit_spec.ts
  ✅ api_spec.ts
  ✅ hadith_verifier_spec.ts
  ❌ audit.spec.ts  ← dot before spec causes yml path mismatch
When CI yml references a file, verify exact filename with:
  Get-ChildItem tests/ -Filter "*.spec.ts"
## ════════════════════════════════════════════════════════
## QA_STANDARDS_AGENT_RULES.md ADDENDUM — May 2026
## Append to bottom of QA_STANDARDS_AGENT_RULES.md
## Covers: Pre-push protocol, P040-P059 rules, agent auto-update
## ════════════════════════════════════════════════════════

### 6.5 MANDATORY: Pre-push test protocol (added after CI #122-143)
NEVER run `git push` without running tests locally first.
20+ CI failures were caused by skipping this step.

```powershell
# hadith-verifier — run before EVERY push:
npx tsc --noEmit
npx playwright test tests/hadith-verifier.spec.ts --project=chromium
npx playwright test tests/api.spec.ts --project=chromium

# hadith-reels — run before EVERY push:
npx tsc --noEmit
npm run build
npx playwright test tests/hadith-reels.spec.ts --project=chromium
```

Automated via .git/hooks/pre-push script in both projects.
Doc-only commits bypass with: git push --no-verify

### 6.6 CI yml forbidden steps (P045/P046)
NEVER add these to push-triggered CI:
- audit_spec.ts (14+ real Claude calls)
- language-speech.spec.ts (real ElevenLabs)
- Any @real-api tagged tests
Use workflow_dispatch for audit runs instead.

### 6.7 Deterministic vs non-deterministic test rule (P044)
NEVER test a deterministic function through a non-deterministic AI API.
Pure functions (getSeverity, mapLang, getRateLimit) → unit test directly.
AI output quality → @real-api tagged tests only.

### 6.8 Emoji tab button locator rule (P047/P048)
NEVER use getByText() or filter({hasText}) on buttons containing emojis.
Test FUNCTIONAL OUTCOME (content that loads) not UI LABEL TEXT.
Use page.evaluate() to click emoji buttons by partial textContent.

### 6.9 TTS text sanitization rule (P059)
ALWAYS sanitize text before sending to TTS (ElevenLabs or browser):
Remove: URLs (https://...), bullet chars (◆♦•·), hadith refs (#1234, bukhari:8)
Remove: markdown (**bold**), tier labels ([tier1])
Function: sanitizeForTTS() in TTSPlayer.tsx

### 6.10 BCP-47 language codes for browser SpeechSynthesis (P058)
Browser SpeechSynthesis requires full BCP-47 codes:
  en → en-US  |  uz → uz-UZ  |  ar → ar-SA  |  ru → ru-RU  |  tj → ru-RU
'uz' alone is NOT recognized — browser falls back to English voice.
'tj' has no native voice — ru-RU is closest available.

### 6.11 Native binary packages in Next.js routes (P054/P055)
NEVER import native binary packages in Next.js API routes without externalizing:
- @remotion/renderer, @remotion/bundler — use serverExternalPackages
- Sharp, Canvas, FFmpeg, node-gyp packages — same rule
Next.js 15+: use top-level serverExternalPackages (not experimental.*)
Next.js 16+: uses Turbopack by default — remove webpack config entirely

## ════════════════════════════════════════════════════════
## SECTION 8 UPDATE: Daily skill upgrade protocol (enhanced)
## ════════════════════════════════════════════════════════

### 8.5 Agent self-update rule (NEW)
After every session where fixes are applied:
1. Doc agent MUST update fix_patterns.md in the SAME commit as the fix
2. Doc agent MUST update CLAUDE.md when: CI run completes, feature added,
   bug fixed, test count changes, pending feature list changes
3. Doc agent MUST update AGENTS.md when: new never-do rule identified,
   new test pattern established, pre-push protocol changes
4. Doc agent MUST update QA_STANDARDS_AGENT_RULES.md when: new section
   needed from production learnings (like P040-P059 this session)
5. QA_STANDARDS_AGENT_RULES.md propagated to ALL projects after update:
   Copy-Item "QA_STANDARDS_AGENT_RULES.md" "..\hadith-reels\..." -Force
   Copy-Item "QA_STANDARDS_AGENT_RULES.md" "..\idris-learning-app\..." -Force

### 8.6 What was missed this session (self-audit May 2026)
The following were NOT documented in real-time and required catch-up:
- fix_patterns.md: P040-P059 (20 patterns) missing until end of session
- CLAUDE.md: outdated (4 tabs, no seerah_context, wrong CI count)
- AGENTS.md: pre-push protocol not added until end of session
- QA_STANDARDS: sections 6.5-6.11 not added until end of session
Root cause: doc tasks were treated as separate from code tasks.
Fix: every fix message includes fix_patterns entry in same response.

### 8.7 Video trace agent (planned — Phase 4)
Current state: Playwright saves trace.zip on failure. No agent reads it.
Planned: CI monitor agent downloads trace.zip from GitHub Actions artifacts
and runs: npx playwright show-trace trace.zip
This gives video + DOM + network log of exact failure moment.
Eliminates all guessing about what the page looked like during failure.

## ════════════════════════════════════════════════════════
## SECTION 9 UPDATE: TTS and audio quality rules (NEW)
## ════════════════════════════════════════════════════════

### 9.1 TTS voice quality by language
| Language | Primary | Fallback | Quality |
|---|---|---|---|
| AR | ElevenLabs Hijazi/Abu Salem | ar-SA browser | High |
| RU | ElevenLabs Abrar Sabbah | ru-RU browser | High |
| EN | ElevenLabs EN voice | en-US browser | High |
| UZ | ElevenLabs multilingual | uz-UZ browser | Medium |
| TJ | ElevenLabs (ru voice) | ru-RU browser | Low — no native TJ |

### 9.2 Tajik narration — real voice recommendation
ElevenLabs has no native Tajik voice. Options for authentic TJ narration:
1. islamhouse.com — free Tajik Islamic audio (CC licensed)
2. Custom ElevenLabs voice clone from real Tajik scholar recording
3. Phase 4: integrate a Tajik TTS API (e.g. SalomAI by Uzbek/Tajik teams)
Current acceptable behavior: ru-RU voice for TJ (sounds Russian — acceptable)

### 9.3 Text sanitization before TTS (mandatory)
sanitizeForTTS() must be called before ANY TTS provider:
- ElevenLabs API call
- Browser SpeechSynthesis
- Any future TTS provider
Strips: URLs, bullets, hadith refs, markdown, tier labels, excess whitespace
