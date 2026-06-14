r"""
split-narration.py
================================================================================
Split narration audio into ordered <=N-second chunks at SILENCE boundaries, so
each chunk fits fal VEED Fabric's ~30s per-clip cap before lip-sync generation.

Cuts are placed at natural pauses (silence) near each length boundary, never
mid-word. Optionally concatenates several inputs (e.g. story + moral) into one
timeline first, then splits.

Requires: ffmpeg + ffprobe on PATH (same as render-reel.ps1).

Usage (PowerShell, from repo root):
  # split a single narration file:
  python split-narration.py --base kids-en-bukhari-1520 --audio out\kids-en-bukhari-1520-story.mp3

  # concat story + moral (in order), then split:
  python split-narration.py --base kids-en-bukhari-1520 ^
      --audio out\kids-en-bukhari-1520-story.mp3 out\kids-en-bukhari-1520-moral.mp3

  # custom max length:
  python split-narration.py --base kids-ru-bukhari-1520 --maxlen 25 --audio out\story.mp3

Outputs (ordered, in out\talking\):
  <base>-clip01.mp3, <base>-clip02.mp3, ...
The script then prints a ready-to-run block to turn each chunk into a talking
clip (Fabric) and render the final reel.
================================================================================
"""

import argparse
import os
import re
import subprocess
import sys

# --- tunables ----------------------------------------------------------------
DEFAULT_MAXLEN = 28.0   # seconds per chunk (margin under Fabric's ~30s cap)
MIN_CHUNK      = 4.0    # avoid cutting a chunk shorter than this when possible
SILENCE_DB     = -30    # silencedetect noise floor (dB)
SILENCE_DUR    = 0.35   # min silence length to count as a pause (s)
GAP            = 0.6    # silence inserted between concatenated inputs (s)
OUTDIR         = os.path.join("out", "talking")


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def need_tool(name):
    from shutil import which
    if which(name) is None:
        sys.exit(f"ERROR: {name} not found on PATH. Add ffmpeg's bin folder, e.g.\n"
                 f'  $env:PATH += ";C:\\ffmpeg\\ffmpeg-master-latest-win64-gpl\\bin"')


def ffprobe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", path])
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit(f"ERROR: could not read duration of {path}\n{r.stderr}")


def concat_inputs(paths, out_path):
    """Concat inputs into one uniform timeline with GAP silence between each."""
    args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for p in paths:
        args += ["-i", p]
    n = len(paths)
    chains, labels = [], []
    for i in range(n):
        chain = f"[{i}:a]aformat=sample_rates=44100:channel_layouts=stereo"
        if i < n - 1:
            chain += f",apad=pad_dur={GAP}"
        chain += f"[a{i}]"
        chains.append(chain)
        labels.append(f"[a{i}]")
    filt = ";".join(chains) + ";" + "".join(labels) + f"concat=n={n}:v=0:a=1[out]"
    args += ["-filter_complex", filt, "-map", "[out]", out_path]
    r = run(args)
    if not os.path.isfile(out_path):
        sys.exit("ERROR: failed to concat inputs:\n" + r.stderr)


def detect_silence_mids(path):
    """Return sorted midpoints of detected silences (good cut candidates)."""
    r = run(["ffmpeg", "-hide_banner", "-i", path,
             "-af", f"silencedetect=noise={SILENCE_DB}dB:d={SILENCE_DUR}",
             "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", r.stderr)]
    ends   = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", r.stderr)]
    return sorted((s + e) / 2.0 for s, e in zip(starts, ends))


def plan_cuts(duration, mids, maxlen):
    """Greedy: from each position, cut at the latest silence within reach,
    else hard-cut at maxlen."""
    cuts = [0.0]
    pos = 0.0
    while duration - pos > maxlen:
        target = pos + maxlen
        cands = [m for m in mids if pos + MIN_CHUNK < m <= target]
        cut = cands[-1] if cands else target
        cuts.append(round(cut, 3))
        pos = cut
    cuts.append(round(duration, 3))
    return cuts


def main():
    ap = argparse.ArgumentParser(description="Silence-aware narration splitter for Fabric")
    ap.add_argument("--base", required=True, help="Output base name, e.g. kids-en-bukhari-1520")
    ap.add_argument("--audio", required=True, nargs="+", help="One or more audio files (in order)")
    ap.add_argument("--maxlen", type=float, default=DEFAULT_MAXLEN, help=f"Max chunk seconds (default {DEFAULT_MAXLEN})")
    ap.add_argument("--outdir", default=OUTDIR, help=f"Output dir (default {OUTDIR})")
    args = ap.parse_args()

    need_tool("ffmpeg")
    need_tool("ffprobe")

    for p in args.audio:
        if not os.path.isfile(p):
            sys.exit(f"ERROR: file not found: {p}")

    os.makedirs(args.outdir, exist_ok=True)

    # build the source timeline (concat if >1 input)
    tmp_concat = None
    if len(args.audio) > 1:
        tmp_concat = os.path.join(args.outdir, f"_src-{args.base}.mp3")
        print(f"Concatenating {len(args.audio)} inputs (gap {GAP}s) ...")
        concat_inputs(args.audio, tmp_concat)
        src = tmp_concat
    else:
        src = args.audio[0]

    duration = ffprobe_duration(src)
    print(f"Total narration: {duration:.1f}s  (max chunk {args.maxlen:.0f}s)")

    if duration <= args.maxlen:
        cuts = [0.0, round(duration, 3)]
        print("Under the cap — single chunk, no split needed.")
    else:
        mids = detect_silence_mids(src)
        print(f"Found {len(mids)} silence points to cut at.")
        cuts = plan_cuts(duration, mids, args.maxlen)

    # cut each segment, re-encoding for sample-accurate boundaries
    made = []
    for i in range(len(cuts) - 1):
        start, end = cuts[i], cuts[i + 1]
        out = os.path.join(args.outdir, f"{args.base}-clip{i+1:02d}.mp3")
        r = run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                 "-i", src, "-ss", str(start), "-to", str(end),
                 "-c:a", "libmp3lame", "-q:a", "2", out])
        if not os.path.isfile(out):
            sys.exit(f"ERROR: failed to write {out}\n{r.stderr}")
        made.append((out, end - start))

    if tmp_concat and os.path.isfile(tmp_concat):
        os.remove(tmp_concat)

    print("\nCreated chunks:")
    for path, dur in made:
        print(f"  {os.path.basename(path)}   ({dur:.1f}s)")

    # print a ready next-step block (user fills in the mascot image)
    mp4_clips = ",".join(f"{args.base}-clip{i+1:02d}.mp4" for i in range(len(made)))
    print("\n--- NEXT: generate a talking clip per chunk, then render ---")
    print('  $img   = "assets\\mascot\\lamb-boy-mosque-night-v2.png"   # <- pick the mascot scene')
    print(f'  $chunks = Get-ChildItem "{args.outdir}\\{args.base}-clip*.mp3" | Sort-Object Name')
    print('  foreach ($c in $chunks) {')
    print('    $out = $c.FullName -replace "\\.mp3$",".mp4"')
    print('    python generate-talking-clip.py --image $img --audio $c.FullName --out $out --resolution 480p')
    print('  }')
    lang = args.base.split("-")[1] if len(args.base.split("-")) > 1 else "en"
    slug = "-".join(args.base.split("-")[2:]) if len(args.base.split("-")) > 2 else "slug"
    print(f'  .\\render-mascot-reel.ps1 -Lang {lang} -Slug {slug} -Clips {mp4_clips} -Open')


if __name__ == "__main__":
    main()