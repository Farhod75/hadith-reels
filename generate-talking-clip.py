"""
generate-talking-clip.py
Lip-synced talking-mascot clip via fal VEED Fabric 1.0 (image + audio -> mp4).

Requires:  pip install fal-client
Auth:      reads FAL_KEY from the environment ($env:FAL_KEY)
Limits:    Fabric caps ~30s per generation; keep test audio short.
Pricing:   480p = $0.08/sec, 720p = $0.15/sec of output.

Usage (PowerShell, from repo root):
  python generate-talking-clip.py --image "out\\mascot\\lamb-boy-v1.png" --audio "out\\test.mp3" --out "out\\talking\\test-boy.mp4" --resolution 480p
"""

import os
import sys
import argparse
import urllib.request

import fal_client


def on_queue_update(update):
    if isinstance(update, fal_client.InProgress):
        for log in update.logs or []:
            print("  fal:", log.get("message", ""))


def main():
    if not os.environ.get("FAL_KEY"):
        sys.exit("ERROR: FAL_KEY not set. Run:  $env:FAL_KEY=\"your-key\"  first.")

    parser = argparse.ArgumentParser(description="Talking mascot via fal VEED Fabric 1.0")
    parser.add_argument("--image", required=True, help="Mascot still (png/jpg/webp)")
    parser.add_argument("--audio", required=True, help="Narration audio (mp3/wav/m4a)")
    parser.add_argument("--out", default="out\\talking\\clip.mp4", help="Output mp4 path")
    parser.add_argument("--resolution", default="480p", choices=["480p", "720p"])
    args = parser.parse_args()

    for path in (args.image, args.audio):
        if not os.path.isfile(path):
            sys.exit(f"ERROR: file not found: {path}")

    print(f"Uploading image: {args.image}")
    image_url = fal_client.upload_file(args.image)

    print(f"Uploading audio: {args.audio}")
    audio_url = fal_client.upload_file(args.audio)

    print(f"Submitting to veed/fabric-1.0 ({args.resolution}) ...")
    result = fal_client.subscribe(
        "veed/fabric-1.0",
        arguments={
            "image_url": image_url,
            "audio_url": audio_url,
            "resolution": args.resolution,
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )

    video_url = result["video"]["url"]
    print(f"Done. Remote video: {video_url}")

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    urllib.request.urlretrieve(video_url, args.out)
    print(f"Saved: {args.out}")


if __name__ == "__main__":
    main()