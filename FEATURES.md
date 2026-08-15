### Talking-mascot kids lane (fal VEED Fabric 1.0)
**Status:** PoC proven (2026-06-13); `render-reel.ps1` integration pending.

- **Engine:** fal `veed/fabric-1.0` — image + audio → lip-synced talking video.
  Resolutions 480p ($0.08/s) / 720p ($0.15/s). ~30s/clip cap (stitch longer).
- **Tool:** `generate-talking-clip.py` (fal-client handles upload + queue).
  Auth via `FAL_KEY` env var.
- **Mascots:** `assets/mascot/lamb-boy-v1`, `lamb-girl-v1` — reusable,
  face-consistent (edit, don't re-roll). One face per clip → animate each
  mascot separately, compose in render.
- Drives clips from existing ElevenLabs/OpenAI TTS narrations.

### Kids talking-mascot reels — Route A (scene-baked)
**Status:** proven end-to-end (2026-06-13).

- **Render:** `render-mascot-reel.ps1` -Lang -Slug -Clips [-Nasheed|-NoMusic]
  [-Subs] [-Open]. Talking clips = spine; nasheed under voice @0.20.
- **Scene mascots:** generate the mascot *in* the scene in Nano Banana Pro,
  attaching the locked base mascot as a face reference. Keep the mascot large,
  front-facing, clear mouth; keep empty headroom (Route-A motion coupling).
- **Proven assets:** boy = moonlit mosque (night), girl = mosque garden (day).

- **Long narration:** `split-narration.py` auto-splits story+moral into
  ordered <=28s chunks at silence boundaries; each chunk -> one Fabric clip;
  render-mascot-reel.ps1 stitches them in order. One mascot + one voice per reel.

### Content linter (`scripts/lint-content.py`)

Deterministic pre-TTS checks on generated reel text. Warn-only — never blocks,
never edits. Encodes five failure modes that were previously caught only by
human review:

| Check | Catches | Origin |
|---|---|---|
| `divine-name` | "God" / "Бог" / "Худо" substituted for the pinned name. Rabb/Lord/Господь/Парвардигор correctly allowed. | P111 |
| `unnamed-authority` | "scholars say", «Учёные», «Уламолар», «Олимон» with no named source | P111, P105 |
| `seerah-source` | A seerah title named without a cited passage — including in negative claims ("neither X nor Y records...") | P115 |
| `simile` | Comparisons absent from the matn. Pass `--matn` and the hadith's own comparison downgrades to INFO. | P111 r14 |
| `inversion` | A station of closeness rendered as lowly («поинтарин», "lowest") | P111 r15 |

Usage — input is the same `S:/M:/H:/C:` blocks used when pasting drafts for review:

```powershell
python scripts\lint-content.py draft.txt --lang tj --matn "<text from hadith_library>"
```

Validated against four generations from R022–R029: caught every documented
defect (R022 EN 4 fail, R025 TJ 4 fail, R026 EN 1 fail) and produced no false
positives on the clean R029 TJ generation.

**Limits:** heuristic, not proof. A clean run means these five checks passed —
not that the text is correct. Human review remains the gate. The `inversion`
check is the weakest (word list only). Does not check translation accuracy,
isnad verbs, or anything the reel's meaning depends on.