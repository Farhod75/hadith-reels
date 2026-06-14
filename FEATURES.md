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