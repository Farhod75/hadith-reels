# hr-agent-upskilling.md
# Hadith Reels — Agent Upskilling & Tool Evaluation

> **Author:** Farhod Elbekov + Claude session, 2026-05-16
> **Status:** Draft — informational scouting, NOT a commitment to adopt
> **Project:** hadith-reels (github.com/Farhod75/hadith-reels)
> **Companion docs:** `agent-architecture-roadmap.md`, `reel-creation-pipeline.md`, `fix_patterns.md`

## Purpose

This document tracks **emerging tools and techniques** that could upskill the HR agent fleet (per `agent-architecture-roadmap.md`). Each entry is:

- **Honestly assessed** — claims separated from hype
- **Verified via web search** before adoption recommendations
- **Tied to a specific prerequisite or phase** in the roadmap
- **Marked with caveats** if HR-specific testing hasn't been done

This is a scouting log, not an adoption plan. Tools listed here are CANDIDATES — they need evaluation before integration.

---

## Source channels

Tools and techniques surface from:
- LinkedIn AI engineering community (marketing-heavy, verify everything)
- Hacker News
- ArXiv papers
- GitHub trending
- Direct experimentation
- Anthropic / Claude release notes
- Conferences (NeurIPS, ICML, transcripts on YouTube)

---

## Candidates under evaluation

### Candidate 1: Supertonic (on-device TTS)

> **Source:** Mahmood Khan LinkedIn post, 2026-05-13
> **Verified via:** Supertonic GitHub repo, Hugging Face, MarkTechPost (verified 2026-05-16)
> **Status:** ⏳ EVALUATION CANDIDATE — promising for EN/RU/AR, NOT VIABLE for UZ/TJ

#### What it is

Supertonic is an open-source on-device TTS engine by Supertone Inc. (Seoul). Currently at **Supertonic v3** (released 2026-04-29), supporting **31 languages**, with the model running entirely via ONNX Runtime — no cloud calls, no API keys, no per-character pricing.

**Verified facts:**
- 99M parameters (small, runs on CPU, no GPU required)
- Sample code under MIT license; model weights under OpenRAIL-M license
- 167× faster than real-time on M4 Pro (verified in benchmarks)
- Outputs 44.1kHz 16-bit WAV
- Supports inline expression tags (`<laugh>`, `<breath>`, `<sigh>`)
- Available via `pip install supertonic`
- Runtimes: Python, Node.js, browser (WebGPU/WASM), Java, C++, C#, Go, Swift, iOS, Rust, Flutter

#### Language coverage check for HR

This is the **make-or-break test** for HR adoption:

| HR Language | Supertonic v3 Support? | Notes |
|---|---|---|
| **EN** (English) | ✅ Yes | First-class support, all voice presets work |
| **RU** (Russian) | ✅ Yes | Confirmed in v3 31-language expansion |
| **AR** (Arabic) | ✅ Yes | Confirmed in v3 31-language expansion |
| **UZ** (Uzbek) | ❌ **NOT SUPPORTED** | Not in the 31 ISO codes |
| **TJ** (Tajik) | ❌ **NOT SUPPORTED** | Not in the 31 ISO codes |

**Verified 31-language list (Supertonic v3):**
Arabic (ar), Bulgarian (bg), Croatian (hr), Czech (cs), Danish (da), Dutch (nl), English (en), Estonian (et), Finnish (fi), French (fr), German (de), Greek (el), Hindi (hi), Hungarian (hu), Indonesian (id), Italian (it), Japanese (ja), Korean (ko), Latvian (lv), Lithuanian (lt), Polish (pl), Portuguese (pt), Romanian (ro), Russian (ru), Slovak (sk), Slovenian (sl), Spanish (es), Swedish (sv), Turkish (tr), Ukrainian (uk), Vietnamese (vi).

#### Honest assessment for HR

✅ **Strong fit for EN, RU, AR reels** — eliminates ElevenLabs per-character cost, runs locally, no API rate limits, no internet dependency.

❌ **Cannot replace ElevenLabs for UZ/TJ** — those languages aren't supported. ElevenLabs Multilingual v2 must remain for these two.

⚠️ **Voice quality caveat** — per Supertone's own FAQ: *"The preset voices are clean and stable but lack the prosody range of large commercial models."* This matters for religious narration where emotional weight on "Аллах ﷻ" or "ﷺ" carries meaning. Needs A/B test against ElevenLabs Abrar Sabbah voice before adoption.

⚠️ **Pronunciation of religious Arabic terms in RU/EN context** — Supertonic was trained on general corpus. May mispronounce "Allah", "Sallallahu Alayhi Wasallam", names like "Abu Hurairah" with non-Arabic phonetics. This is a critical failure mode for the channel.

#### Decision criteria

Adopt for EN/RU/AR ONLY IF:
1. Voice quality A/B test passes (10 native speakers per language rate ≥ 4/5 vs ElevenLabs)
2. Religious term pronunciation passes manual review (no "Al-Lah" or "Mu-ham-mad" robotic syllabification)
3. Integration effort < 2 days

Do NOT adopt if:
- Pronunciation drift on "ﷺ" formula or Arabic loanwords
- Test users prefer ElevenLabs for emotional connection
- Setup adds more complexity than it removes

#### Roadmap fit

If adopted: **Phase 3 alternative** to ElevenLabs for EN/RU/AR. Documented as a fork in Narrator agent (Part 2 of agent-architecture-roadmap.md). UZ/TJ remain on ElevenLabs.

#### Test plan (post-Hajj)

```python
# Quick eval script
pip install supertonic

from supertonic import TTS
tts = TTS(auto_download=True)

test_phrases = {
    'ru': [
        'Посланник Аллаха, да благословит его Аллах и приветствует',
        'Сахих аль-Бухари передал хадис от Абу Хурайры',
        'Каждому верующему даётся свой путь к Всевышнему'
    ],
    'en': [
        'The Messenger of Allah, may peace and blessings be upon him',
        'Imam Bukhari narrated this hadith from Abu Hurairah',
        'Every believer has a unique path to the Most High'
    ],
    'ar': [
        'قال رسول الله صلى الله عليه وسلم',
        # ... full Arabic phrases
    ]
}

for lang, phrases in test_phrases.items():
    for phrase in phrases:
        style = tts.get_voice_style(voice_name="M1")
        wav, duration = tts.synthesize(phrase, voice_style=style, lang=lang)
        tts.save_audio(wav, f"supertonic-test-{lang}-{idx}.wav")
```

Then play each in headphones, score 1-5 on:
- Naturalness
- Religious term pronunciation
- Emotional appropriateness
- Comparison vs ElevenLabs same phrase

---

### Candidate 2: Speechmatics (cloud STT, alternative to Whisper)

> **Source:** Pipecat / Speechmatics LinkedIn post, 2026-05-14
> **Verified via:** Speechmatics docs (verified 2026-05-16)
> **Status:** ⏳ EVALUATION CANDIDATE — directly addresses P078

#### What it is

Speechmatics is a UK-based commercial STT provider claiming **55+ languages**, sub-500ms latency, ~90%+ accuracy. The LinkedIn post highlighted a Pipecat benchmark showing **1.07% semantic word error rate** (the lowest among 10 services tested).

**Verified facts:**
- 55+ languages supported (includes Arabic, Russian, Uzbek)
- $200 free credits to evaluate
- Two operating points: "Standard" (faster) and "Enhanced" (more accurate)
- Real-time and batch APIs
- Cloud-only (no on-device option)
- Used by enterprise customers (compliance, broadcast)

#### Language coverage for HR's P078 problem

This directly addresses the Whisper UZ/TJ Latin transliteration issue:

| HR Language | Speechmatics Support? | Notes |
|---|---|---|
| EN | ✅ Yes | Standard accuracy |
| RU | ✅ Yes | Standard accuracy |
| AR | ✅ Yes | Global Arabic model (handles MSA + dialects) |
| **UZ** (Uzbek) | ⚠️ Available but **NOT VERIFIED** as Cyrillic-native | Need to test if output is Cyrillic or Latin |
| **TJ** (Tajik) | ⚠️ Listed but quality unknown | Same Whisper-like risk — Tajik corpus is small everywhere |

#### Honest assessment for HR

✅ **The 1.07% WER claim is from Pipecat's third-party benchmark**, not Speechmatics' own marketing. Lower risk of cherry-picked numbers. Worth taking seriously.

✅ **Direct path to closing P078** — if Speechmatics outputs Cyrillic for UZ/TJ audio, we get subtitles for those languages without writing a Latin→Cyrillic conversion script (P078 Option A or C).

⚠️ **Cloud-only is a step back** — Whisper runs locally on your machine. Speechmatics requires internet + API calls. Adds latency to pipeline and a vendor dependency.

⚠️ **Cost at scale** — Free tier is $200 credit. At production volume (say 30 reels/month, ~70 sec each = 35 min/month), still well under any paid tier. But if HR scales to 5 reels/day, costs become real (~$20-50/month estimate, needs verification).

❌ **No on-device option** means if you're offline (e.g., during Hajj), you can't render reels with subtitles. Whisper local doesn't have this constraint.

#### Decision criteria

Adopt for UZ/TJ ONLY IF:
1. Speechmatics outputs proper Cyrillic for UZ/TJ audio (test with 10 sample audio clips)
2. WER on religious term transcription < 5%
3. Q→K drift doesn't appear (the specific P078 failure mode)

Adopt for EN/RU/AR as supplement IF:
1. Accuracy meaningfully exceeds Whisper local (current baseline)
2. Latency penalty is acceptable

#### Roadmap fit

If adopted: **Phase 3 alternative** to Whisper for UZ/TJ subtitle generation. Closes P078 Option A. Documented as a fork in Renderer agent.

If NOT adopted: Continue with P078 Option C (Whisper + Latin→Cyrillic converter, or skip subs entirely for UZ/TJ).

#### Test plan (post-Hajj)

```bash
# Sign up: https://www.speechmatics.com → claim $200 credits

# Test with the existing UZ/TJ MP3 narrations you have on disk:
# out/umra-to-umra-narration-full.mp3 (TJ)
# ... any UZ test files

curl -X POST "https://asr.api.speechmatics.com/v2/jobs/" \
  -H "Authorization: Bearer $SPEECHMATICS_API_KEY" \
  -F "data_file=@out/umra-to-umra-narration-full.mp3" \
  -F 'config={"type":"transcription","transcription_config":{"language":"uz","operating_point":"enhanced"}}'

# Poll for result, examine output:
# - Is it Cyrillic or Latin?
# - Do religious terms transcribe correctly?
# - WER vs known correct text?
```

Comparison matrix to fill in:

| Test phrase | Whisper output | Speechmatics output | Correct text |
|---|---|---|---|
| (TJ Cyrillic religious phrase 1) | (Latin, drift) | TBD | (correct Cyrillic) |
| (UZ Cyrillic religious phrase 1) | (Latin, drift) | TBD | (correct Cyrillic) |
| ... |

---

### Candidate 3: Hyperframes + Claude Code workflow

> **Source:** Cole Medin LinkedIn post, 2026-05-14
> **Verified:** Not fully verified per scope (excluded by user)
> **Status:** 📚 STUDY ONLY — workflow inspiration, not direct adoption

#### What it is (per the post)

A Claude Code workflow using Hyperframes (open source) that takes a single-sentence prompt and produces a quick explainer video end-to-end: script, voice, visuals, transitions, all synced. Cole reports 10-minute production for what previously took hours.

#### Honest assessment for HR

❌ **Not a direct fit** — Hyperframes likely generates abstract explainer animations, not narrated hadith reels with Kaaba B-roll, Cyrillic subtitles, and nasheed mixing. Different genre.

✅ **The orchestration pattern is interesting** — Claude Code as an orchestrator that chains text→voice→video tools is exactly what HR's agent fleet aims for (per agent-architecture-roadmap.md Phase 6-7).

#### Roadmap fit

Don't adopt the tool. **Study Cole's GitHub repo (when located) to learn how he wired Claude Code as the orchestrator.** Apply lessons to HR agent fleet Phase 6 (Curator + Generator chain).

#### Action items (post-Hajj)

1. Find Cole Medin's GitHub repo for Hyperframes workflow (linked in his LinkedIn comments)
2. Read 1 hour, extract orchestration patterns
3. Document any reusable patterns in `agent-architecture-roadmap.md` Phase 6

---

## Candidates explicitly NOT adopting (and why)

### OpenUI (LLM-to-UI protocol)

> Source: LinkedIn post (image 2 in source feed)
> Status: ❌ NOT RELEVANT for HR

HR's admin UI is a stable Next.js app. The admin doesn't generate UI dynamically per request. OpenUI's value (token reduction in LLM-generated UI) applies to apps that build interfaces on-the-fly — not HR's case.

Possibly relevant for **Idris** (children's learning app with dynamic activity UI) — see `idris-agent-upskilling.md`.

---

## Watch list (not evaluated yet)

| Tool / Tech | Source | Why interesting | Priority |
|---|---|---|---|
| Speechmatics Voice Builder | Speechmatics docs | Custom edge-native voice from your own recordings — could clone reciter voices | Low (post-monetization) |
| Whisper turbo / large-v3 | OpenAI updates | Newer Whisper variants may handle UZ/TJ Cyrillic better | Medium |
| Kokoro TTS | Hugging Face | Another open TTS, mentioned in Supertonic benchmarks | Low |
| VoxCPM2 | OpenBMB | 2B param open TTS, better quality | Low (overkill for HR) |
| Anthropic Claude Sonnet 4.7 prompt caching | Anthropic docs | Reduce cost of repeated reel generation | High |
| Pipecat orchestration framework | pipecat-ai/pipecat | Voice agent framework, possibly useful for Approver bot | Medium |

---

## Evaluation discipline

**Hard rules before adopting any tool:**

1. **Test with HR's actual content** — generic demos don't tell you if "صلى الله عليه وسلم" pronounces correctly
2. **All 5 languages must work or be honestly excluded** — never partial-adopt and ignore the gap
3. **Compare against current pipeline** — only adopt if it's meaningfully better, not just newer
4. **Document the failure modes** — what does this tool get WRONG? Add to fix_patterns as Pxxx if relevant
5. **One change at a time** — never swap TTS + STT + Renderer simultaneously
6. **Keep the fallback** — if Supertonic breaks production, can we switch back to ElevenLabs in < 1 hour?

**Anti-patterns to avoid:**

- ❌ "Just killed ElevenLabs" hype → verify it works for YOUR languages first
- ❌ "Open source so it's better" → license is one factor, quality is another
- ❌ "I saw it on LinkedIn yesterday" → wait 1-2 weeks, see how it ages
- ❌ Replacing working pipelines without an A/B baseline
- ❌ Adopting cloud tools that re-introduce vendor lock-in we previously escaped

---

## Change log

| Date | Change | By |
|---|---|---|
| 2026-05-16 | Initial scouting doc, 2 candidates evaluated (Supertonic, Speechmatics), 1 noted (Hyperframes) | Farhod / Claude session |

---

## References

- `agent-architecture-roadmap.md` — where these tools fit in the migration plan
- `reel-creation-pipeline.md` — current pipeline (what we'd replace)
- `fix_patterns.md` P078 — Whisper UZ/TJ issue (Speechmatics candidate addresses this)
- `hv-agent-upskilling.md` — Hadith Verifier scouting (separate project)
- `idris-agent-upskilling.md` — Idris learning app scouting (separate project)
