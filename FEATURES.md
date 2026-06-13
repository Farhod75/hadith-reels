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