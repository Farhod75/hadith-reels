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
