# RECOVERY — when an UptimeRobot email says something is down

The same file lives in `hadith-verifier` and `hadith-reels`; change both together.
Added 2026-11-10 (P388). Monitors are on the operator's UptimeRobot account, checked
every 5 minutes, alerts by email:

| Monitor | URL | What it proves |
|---|---|---|
| HV health | https://hadithverifier.com/api/health | database answers AND the Claude model exists for our key |
| HV site | https://hadithverifier.com | the deployment serves pages |
| HR health | https://www.hadithreels.com/api/health | the library database answers |
| HR site | https://www.hadithreels.com | the deployment serves pages |

## 1. Which monitor fell

| health | site | Meaning | Go to |
|---|---|---|---|
| DOWN | UP | the app serves, a dependency failed | step 3 |
| DOWN | DOWN | the deployment, Vercel or the domain | step 2 |
| UP | DOWN | the page itself fails to render | step 2 (b) |

## 2. The site is down

a. **Vercel itself:** https://www.vercel-status.com — if Vercel has an incident, wait.

b. **A bad deploy:** Vercel dashboard → project (`hadith-verifier-vp57` for HV,
   `hadith-reels` for HR) → Deployments. If the outage began right after the newest
   deployment, open the last good one → `⋯` → **Promote to Production**. That is an
   instant rollback; fix the code afterwards and push again.

c. **The domain:** open the URL. A DNS error or a "domain expired" page means the
   registrar: renew it there and keep auto-renew on. Vercel → project → Settings →
   Domains shows a red mark when DNS is broken.

## 3. Health is down: read its body

```powershell
Invoke-WebRequest -UseBasicParsing https://hadithverifier.com/api/health -SkipHttpErrorCheck | Select-Object StatusCode, Content
Invoke-WebRequest -UseBasicParsing https://www.hadithreels.com/api/health -SkipHttpErrorCheck | Select-Object StatusCode, Content
```

| Field | Value | Cause | Fix |
|---|---|---|---|
| `db` | `unreachable` | Supabase down or the project paused | https://status.supabase.com; Supabase dashboard → the project → **Restore** if paused; check usage limits |
| `db` | `unconfigured` | an environment variable is missing in Vercel | Vercel → Settings → Environment Variables → add it → Redeploy |
| `claude` | `model_unavailable` | Anthropic retired our model (P90, P129) | change `CLAUDE_MODEL` in `hadith-verifier/lib/models.ts` to a current model (https://docs.claude.com → Models overview), push. One file. |
| `claude` | `auth_failed` | the API key was revoked or rotated | https://console.anthropic.com → API keys → new key → Vercel `ANTHROPIC_API_KEY` → Redeploy. The operator enters keys himself. |
| `claude` | `unreachable` | Anthropic outage or rate limit | https://status.anthropic.com; usually clears by itself |

## 4. What the monitors cannot see

- **Anthropic credit balance used up.** Health still says `ok` (the model exists); every
  analysis fails with a credit error. Console → Billing: keep auto-reload or the
  low-balance email on.
- **ElevenLabs quota used up.** HV's Listen buttons fail; HR's public Listen plays stored
  files and is unaffected. elevenlabs.io → Subscription.
- **HV Telegram bot** — hosted on Railway: railway.app dashboard → the bot service → logs.
- **Domain renewal** — keep auto-renew on at the registrar for both domains.

## 5. After it is back

- UptimeRobot sends an "is up" email by itself.
- If our code caused it: a `fix_patterns.md` entry with the cause, as for any defect.
