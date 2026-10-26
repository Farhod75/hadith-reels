# Still prompts

One `<name>-still.json` per FLUX text-to-image call, written by
`scripts/generate-image.ps1`.

The sibling of `assets/scene-prompts/`, which records the image-to-video call
that animates the still this folder describes. Together they are the full
provenance of a scene clip: what was asked for, of which model, when, and which
variants came back.

Tracked, and deliberately NOT in `out/`. The stills themselves live in
`out/refs/`, which is gitignored - a sidecar written beside them would vanish
on a clean checkout, which is the loss P250 exists to prevent.

`chosen` is null until a human picks a variant to animate. Fill it in then; the
generator cannot know.
