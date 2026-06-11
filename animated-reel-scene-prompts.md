# Animated Reel — Scene Prompt Generation (Pillar 2, POC step 1)

> **Status:** DESIGN / for review — not yet wired to fal.ai Kling
> **Project:** hadith-reels (Pillar 2 — narration-driven animated/cinematic reels)
> **Purpose:** Turn a hadith into 2-3 *anonymous, religiously-appropriate* cinematic scene
>   prompts that fal.ai Kling can generate, which then replace the looping-Kaaba background
>   in render-reel.ps1.
> **Hard principle:** Depict the THEME, never the FIGURES. The narration tells the story
>   (including who spoke); the visuals show the lesson's mood and setting — never the
>   Prophet ﷺ, prophets, angels, or named companions.

---

## 1. Why this step matters most

Everything downstream (Kling generation, assembly, posting) is mechanical. This step is
where **religious appropriateness is won or lost**, and where a careless prompt could
produce something impermissible. So it is human-reviewed by design, and Claude self-audits
every scene before a human ever sees it. No scene reaches Kling without passing both gates.

---

## 2. Religious guardrails (the non-negotiable core)

### NEVER depict (hard block — regenerate the scene if any appears)
- **The Prophet Muhammad ﷺ** — no face, body, silhouette, or figure intended to be him.
- **Any prophet** (Ibrahim, Musa, Isa, Yusuf, etc.) — same rule.
- **Angels** (Jibril and others).
- **Allah** — any depiction whatsoever, literal or symbolic.
- **Named Sahaba / Ahl al-Bayt as identifiable individuals** — Abu Bakr, Umar, Uthman, Ali,
  Aisha, Fatima, Khadija, etc. Even when the hadith is *about* them, they are never shown.
- **Any specific named historical Islamic personage** the narration mentions.
- Idols or the sacred symbols of other religions shown reverently.
- Anything immodest: revealing dress, intimacy, alcohol, etc.

### ALLOWED (the safe visual palette — build scenes from these)
- **Anonymous, generic humans** who do NOT represent any named figure: an elderly man in
  prayer, a child reading Qur'an, pilgrims as an undifferentiated crowd, a lone traveler —
  shown from behind, at a distance, or as silhouettes where possible.
- **Sacred places:** the Kaaba, Masjid an-Nabawi exterior, mosque interiors, the landscapes
  of Mecca / Medina, minarets at dawn.
- **Nature & environment:** desert dunes, sunrise/sunset, mountains, oases, rain, olive and
  date palms, a clear night sky, flowing water.
- **Objects (strong symbolic carriers):** an open Qur'an, prayer beads (misbaha), dates,
  Zamzam water, a lantern, a prayer mat, Arabic calligraphy, an open door, a winding path.
- **Atmospheric / symbolic:** light streaming through a window, a path through the desert,
  doors opening to light, footprints in sand — visual metaphors for the lesson.

### THE FACE DIAL (your call — set once, applies to all scenes)
Your stated approach ("an old man or child praying") allows **generic anonymous faces**.
A stricter scholarly view avoids depicting any detailed animate face. So this is a setting:
- **MODE A (your default):** generic anonymous humans with faces allowed, as long as they
  represent no named figure. (e.g. an old man's face in prayer is fine.)
- **MODE B (stricter):** no detailed faces at all — figures only from behind, as
  silhouettes, distant, or implied (hands, shadows). Safest if scholarly review is uncertain.

Recommendation: start in **MODE B** for the POC (lowest risk, and silhouette/back-view
scenes are often *more* cinematic anyway), then relax to A if you and a reviewer are
comfortable. Either is supported; the system prompt switches on it.

### ERA & SETTING (inferred per hadith — environment + clothing must match the period)

A hadith may describe different historical eras, and the visuals should match whichever one
the hadith is about — NOT a fixed period, and NOT modern Mecca. Claude infers the era from
the hadith text and picks the matching environment and (anonymous, period-appropriate) dress.

> **THE ERA RULE DOES NOT RELAX THE FIGURE RULE.** Even when a hadith narrates the story of
> Ibrahim, Musa, Yusuf or any earlier prophet (عليهم السلام), the prophet himself is **still
> never depicted** — same absolute MODE B/never rule. The era only changes the *environment
> and clothing*; we show the period's setting and anonymous figures (from behind), never the
> prophet's face or body. This is the most important line in this document.

| Hadith era | Visual setting | Anonymous dress (from behind / no face) |
|---|---|---|
| **Prophet ﷺ / Companions** (7th c. CE, ~1400 yrs ago) | Ancient Mecca / Medina — mud-brick & stone, palm groves, open Kaaba plaza, NO modern marble or towers | Men: ihram = two unstitched white cloths (one at waist, one over left shoulder, right shoulder bare). Women: modest flowing period robe + headscarf |
| **Ibrahim عليه السلام** (~2000 BCE) | Ancient Mesopotamia / Levant — mud-brick, open desert, starry night skies, early Kaaba foundations being raised | Simple ancient Near-Eastern robes, undyed cloth |
| **Musa عليه السلام** | Ancient Egypt / Sinai — pharaonic stone architecture, Red Sea, desert mountains | Ancient robes; a staff shown as an OBJECT (never the prophet holding it in view) |
| **Yusuf عليه السلام** | Ancient Egypt — palaces, the Nile, granaries, market | Period Egyptian dress |
| **General / timeless lesson** | Nature, light, symbolic objects — no specific era needed | n/a |

Correct era phrasing for prompts: say **"7th-century Arabia, early Islamic period, ancient
Mecca, simple stone and mud-brick buildings, no modern structures"** — NOT "300-500 years
ago" (that yields wrong Ottoman-era visuals). Earlier prophets are *thousands* of years
before the Prophet ﷺ, so their eras get their own ancient settings as above.

---

## 3. The system prompt (for Claude — Fable 5 / Opus 4.8)

> Used as the `system` message in the scene-generation API call. The hadith story text is the
> user message. Output is JSON only.

```
You are a visual director for short Islamic educational reels. Given a hadith's narration
text, you produce 2-3 cinematic SCENE PROMPTS for an AI video generator. The scenes
illustrate the hadith's THEME and emotional tone — never its characters.

ABSOLUTE RULES (a scene that breaks any of these is forbidden):
- NEVER depict the Prophet Muhammad (peace be upon him), any prophet, any angel, or Allah.
  This includes earlier prophets (Ibrahim, Musa, Yusuf, etc.) even when the hadith is ABOUT
  them — show their era's environment and anonymous figures only, never the prophet himself.
- NEVER depict named companions or any specific named Islamic figure, even if the hadith
  names them. The narration may name them; the VISUAL must not show them.
- Depict only: anonymous generic people (representing no named figure), sacred places,
  nature, symbolic objects, and atmospheric imagery.
- Face mode = {MODE}. If MODE B: no detailed faces — use silhouettes, back views, distance,
  hands, or shadows only.
- Modest dress; reverent, calm tone; nothing that could offend Islamic sensibilities.

ERA & DRESS: infer the historical era from the hadith and make environment + clothing match.
- Prophet/Companions era -> 7th-century Arabia, ancient Mecca/Medina, mud-brick & stone, no
  modern buildings; men in ihram (two unstitched white cloths, waist + over left shoulder).
- Ibrahim era -> ancient Mesopotamia/Levant; Musa -> ancient Egypt/Sinai; Yusuf -> ancient
  Egypt. Use ancient period dress; never modern Mecca for an old-era hadith.
- Say "7th-century Arabia / early Islamic period", NOT "300-500 years ago".

For each scene give: a vivid natural-language video prompt (cinematic, vertical 9:16,
specify era/setting/dress, lighting/mood/camera motion), a duration in seconds (4-8), what it
depicts in plain terms, and a self-audit confirming it shows no forbidden figure.

The scenes together should visually carry the hadith's lesson from opening mood to closing
reflection, timed to roughly match a {DURATION}-second narration.

Output ONLY valid JSON, no preamble:
{
  "hadith_ref": "...",
  "theme": "one-line statement of the lesson the visuals must convey",
  "era": "the historical era inferred (e.g. '7th-century Arabia' or 'Ibrahim era, ancient Mesopotamia')",
  "face_mode": "A" | "B",
  "scenes": [
    {
      "id": 1,
      "duration_sec": 6,
      "prompt": "cinematic vertical 9:16 ...",
      "depicts": "plain description",
      "guardrail_self_audit": "PASS — explanation of why no forbidden figure appears"
    }
  ]
}
```

---

## 4. Output schema (what the step returns)

A JSON object: `hadith_ref`, `theme`, `face_mode`, and a `scenes[]` array. Each scene
carries its Kling prompt, duration, a plain-language `depicts`, and a
`guardrail_self_audit` string. A human reviews the JSON (especially each `depicts` +
`guardrail_self_audit`) and edits/rejects before any scene goes to Kling. This mirrors the
P079 / subtitle-review discipline: human approval before anything irreversible.

---

## 5. Worked example — Bukhari #1520 (women's Hajj as jihad)

**Hadith theme (from your RU narration):** Aisha (RA) asked the Prophet ﷺ about joining
military expeditions; he taught that for women, the best jihad is an accepted Hajj (Hajj
mabrur) — a path of spiritual elevation open to every believing woman.

**Note how the visuals carry the THEME (women's spiritual ascent through Hajj) while never
showing Aisha (RA) or the Prophet ﷺ — the two figures the narration is actually about.**

Example output (MODE B — no detailed faces):

```json
{
  "hadith_ref": "bukhari-1520",
  "theme": "A woman's path to the highest spiritual rank is an accepted Hajj",
  "era": "7th-century Arabia, early Islamic period",
  "face_mode": "B",
  "scenes": [
    {
      "id": 1,
      "duration_sec": 6,
      "prompt": "Cinematic vertical 9:16. A lone anonymous woman seen fully from behind in a modest flowing white period robe and headscarf, standing at the edge of a vast desert at dawn in 7th-century Arabia, soft golden light breaking over distant dunes, gentle wind moving the fabric, slow push-in camera, reverent and hopeful mood. No face visible, no modern structures.",
      "depicts": "A woman pilgrim (from behind) facing the dawn desert — the start of a spiritual journey",
      "guardrail_self_audit": "PASS — anonymous figure from behind, period-accurate dress, represents no named person; no Prophet, prophet, angel, or companion depicted."
    },
    {
      "id": 2,
      "duration_sec": 6,
      "prompt": "Cinematic vertical 9:16. Close shot of anonymous hands raised in dua, prayer beads draped over the fingers, warm light, the blurred Kaaba and circling crowd softly out of focus in the background, slow gentle motion, serene atmosphere.",
      "depicts": "Hands in supplication near the Kaaba — the act of worship at the heart of Hajj",
      "guardrail_self_audit": "PASS — only hands and a distant anonymous crowd; the Kaaba is a place, not a figure; no forbidden depiction."
    },
    {
      "id": 3,
      "duration_sec": 6,
      "prompt": "Cinematic vertical 9:16. A winding sunlit path through the desert that leads toward a horizon glowing with soft light, footprints in the sand, calm and uplifting, slow upward tilt revealing the bright sky, symbolic of ascent.",
      "depicts": "A path toward light — the spiritual elevation the hadith promises",
      "guardrail_self_audit": "PASS — pure landscape and symbolism; no people, no figures of any kind."
    }
  ]
}
```

This is what you'd review: three scenes that *feel* the hadith — journey, worship, ascent —
without ever depicting the people in the story. If a scene's `depicts` or `self_audit`
looked wrong, you'd edit or reject it before Kling.

---

## 6. How this plugs into the existing pipeline

1. **This step (Claude):** hadith text -> scene-prompt JSON (above).
2. **Human review:** approve/edit the JSON (the religious gate).
3. **Kling (POC step 2, not yet built):** each approved `prompt` -> a short clip.
4. **Assembly:** the clips replace the random-Kaaba pick in `render-reel.ps1`'s Step 6 —
   everything after (narration concat, subtitle review, nasheed mix, final merge) is the
   SAME proven pipeline. So Pillar 2 reuses Pillar 1's back half.

---

## 7. Open decisions before POC step 2 (Kling)
- **Face mode:** A or B for the POC? (recommend B)
- **Scenes per reel:** 2-3? (more scenes = more Kling cost + more review)
- **Clip length vs narration:** loop/extend short clips to fill narration, or generate
  longer? (affects cost and Kling params)
- **Scholarly review loop:** who signs off on generated imagery before first publish?
- **Agent fleet:** deferred — prove this manual flow first, THEN consider a scene-agent.
```
