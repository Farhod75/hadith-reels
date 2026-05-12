# CI_WORKFLOW_TEMPLATE.md
# Universal GitHub Actions CI template — all Farhod projects
# Copy this to every new project and customize section 3 only
# Sections 1-2 are universal — never modify them
# Last updated: May 2026
# ============================================================

## ════════════════════════════════════════════════════════
## SECTION 1: THE GOLDEN RULES (never break these)
## ════════════════════════════════════════════════════════

### Rule 1: NEVER add real external API calls to CI push steps
```yaml
# FORBIDDEN in push-triggered steps:
- name: Run language-speech tests   # calls ElevenLabs ❌
- name: Run audit tests             # calls Claude 14+ times ❌
- name: Run @real-api tests         # any real external API ❌

# ALLOWED in push-triggered steps:
- name: Run E2E tests               # page.route() mocked ✅
- name: Run API tests               # unit tests + schema only ✅
- name: Type check                  # tsc --noEmit ✅
- name: Build                       # npm run build ✅
```

### Rule 2: continue-on-error for type check during active development
```yaml
- name: Type check
  run: npx tsc --noEmit
  continue-on-error: true   # remove this once project is stable
```

### Rule 3: Always specify --project=chromium in CI
```yaml
# WRONG — runs all browsers (doubles time):
run: npx playwright test tests/spec.ts

# RIGHT — chromium only in CI:
run: npx playwright test tests/spec.ts --project=chromium --workers=1
```

### Rule 4: Always add workflow_dispatch for manual real-API runs
```yaml
workflow_dispatch:
  inputs:
    run_real_api:
      description: 'Run real API tests against production'
      default: 'false'
      type: choice
      options: ['false', 'true']
```

### Rule 5: Timeout must be ≤20 minutes for push CI
- If push CI takes >20 min → too many real API calls
- Target: <5 minutes for all mocked tests

### Rule 6: NEVER commit PowerShell commands into yml files
The ci.yml must start with `name:` — nothing else.
If you see `cd "C:\..."` on line 1 → the wrong content was committed.

## ════════════════════════════════════════════════════════
## SECTION 2: UNIVERSAL CI TEMPLATE (copy-paste for any project)
## ════════════════════════════════════════════════════════

```yaml
name: {ProjectName} CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      run_real_api:
        description: 'Run real API tests against production'
        default: 'false'
        type: choice
        options: ['false', 'true']

jobs:
  test:
    name: Build + Tests
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Type check
        run: npx tsc --noEmit
        continue-on-error: true

      - name: Build
        run: npm run build
        env:
          NEXT_PUBLIC_SUPABASE_URL: ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
          NEXT_PUBLIC_SUPABASE_ANON_KEY: ${{ secrets.NEXT_PUBLIC_SUPABASE_ANON_KEY }}

      - name: Install Playwright browsers
        run: npx playwright install --with-deps chromium

      # ONLY mocked tests here — see QA_STANDARDS_AGENT_RULES.md Section 6
      - name: Run E2E tests
        run: npx playwright test tests/{project}.spec.ts --reporter=list --workers=1 --project=chromium
        env:
          BASE_URL: https://{your-production-url}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload Playwright report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

      - name: Upload screenshots on failure
        uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: test-screenshots
          path: test-results/
          retention-days: 7
```

## ════════════════════════════════════════════════════════
## SECTION 3: PROJECT-SPECIFIC CUSTOMIZATION
## Only change these values per project
## ════════════════════════════════════════════════════════

| Project | name | spec file | BASE_URL |
|---|---|---|---|
| hadith-verifier | Hadith Verifier CI/CD | tests/hadith-verifier.spec.ts | https://hadithverifier.com |
| hadith-reels | HadithReels CI | tests/hadith-reels.spec.ts | https://hadith-reels.vercel.app |
| idris-learning-app | Idris Learning CI | tests/idris.spec.ts | https://idris-learning.vercel.app |
| ct-ai-exam-prep | CT-AI Exam Prep CI | tests/exam-prep.spec.ts | https://ct-ai-exam-prep.vercel.app |

## ════════════════════════════════════════════════════════
## SECTION 4: HOW TO PREVENT THESE MISTAKES (agent rules)
## ════════════════════════════════════════════════════════

### What went wrong in HR CI #1-5
1. PowerShell setup commands were pasted into ci.yml → line 1 was `cd "C:\..."` not `name:`
2. `language-speech.spec.ts` calls real ElevenLabs → always flaky in CI
3. No spec file existed → CI failed on "No tests found"

### Prevention — 3 automated checks (add to AGENTS.md)

**Check 1: Before committing any ci.yml**
```powershell
# Verify line 1 starts with 'name:'
$line1 = (Get-Content ".github\workflows\ci.yml" -First 1)
if (-not $line1.StartsWith('name:')) {
  Write-Error "ci.yml line 1 must start with 'name:' — got: $line1"
}
```

**Check 2: Before adding any step to ci.yml**
Grep for forbidden patterns:
```powershell
Select-String -Path ".github\workflows\ci.yml" `
  -Pattern "language-speech|audit\.spec|@real-api|ElevenLabs|elevenlabs"
# If any match found → STOP, remove that step
```

**Check 3: Verify spec file exists before pushing ci.yml**
```powershell
$specFile = "tests\hadith-reels.spec.ts"
if (-not (Test-Path $specFile)) {
  Write-Error "Spec file missing: $specFile — create it before pushing ci.yml"
}
```

### Should agents handle this?
YES — the Git agent in AGENTS.md should run these 3 checks automatically
before every commit that touches ci.yml. Add this to AGENTS.md:

```
### Git agent — ci.yml validation (mandatory before commit)
Before committing any .github/workflows/*.yml file:
1. Verify line 1 starts with 'name:' — not PowerShell, not comments
2. Grep for forbidden step names: language-speech, audit.spec, @real-api
3. Verify every spec file referenced in the yml actually exists in tests/
4. Verify timeout-minutes ≤ 20
If any check fails → FIX before committing
```

## ════════════════════════════════════════════════════════
## SECTION 5: MANUAL REAL API TEST COMMANDS
## Run these locally or via workflow_dispatch — NEVER in push CI
## ════════════════════════════════════════════════════════

```powershell
# hadith-verifier — real API tests
$env:BASE_URL="https://hadithverifier.com"
npx playwright test tests/audit_spec.ts --reporter=list
npx playwright test --grep @real-api

# hadith-reels — real API tests  
$env:BASE_URL="https://hadith-reels.vercel.app"
npx playwright test tests/hadith-reels.spec.ts --grep @real-api

# Python pytest against production
$env:BASE_URL="https://hadithverifier.com"
cd tests/python; pytest test_analyze_api.py -v
```
