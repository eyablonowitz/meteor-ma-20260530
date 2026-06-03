"""Generate background music with the ElevenLabs Music API (Eleven Music).

Reads ELEVENLABS_API_KEY (env or ../.env, via voiceover.load_api_key). Writes an
instrumental track to video/assets/music/<name>.mp3. Re-runs skip existing tracks
unless --force -- music generation is non-deterministic, so --force is a fresh
"take" (and --name lets you keep alternates side by side to pick from).

Usage:
    source .env && python video/music.py                 # generate missing
    python video/music.py --force                        # re-roll a new take
    python video/music.py --name outro_b                 # save an alternate take
    python video/music.py --secs 16                      # override length
"""
import argparse
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
MUSIC_DIR = ROOT / "video" / "assets" / "music"
API = "https://api.elevenlabs.io/v1/music"
MODEL = "music_v1"
# mp3 192 kbps requires Creator tier or above (we have it); 44.1 kHz matches the mix.
OUTPUT_FORMAT = "mp3_44100_192"

sys.path.insert(0, str(ROOT / "video"))
from voiceover import load_api_key  # noqa: E402  (reuse the .env key loader)

# Optimistic retro-futuristic credits bed -- 1980s/90s world's-fair "tomorrow"
# (EPCOT Center) energy: warm analog synths, a hopeful melody, a sense of wonder.
TRACKS = {
    "outro": {
        "secs": 19,
        "prompt": (
            "Optimistic, warm retro-futuristic instrumental in the style of "
            "1980s and 1990s EPCOT Center and world's-fair 'tomorrow' themes. "
            "Lush analog synth pads, bright arpeggiated sequencer lines, a "
            "hopeful major-key melody on a soft synth lead, gentle electronic "
            "drums and a warm rounded bassline. A feeling of wonder, curiosity, "
            "and optimism about science and the future. Mid-tempo around 100 "
            "BPM, nostalgic and uplifting, like the warm finale of a science "
            "documentary. Builds gently and resolves warmly. Fully instrumental, "
            "no vocals."
        ),
    },
}


def compose(key, prompt, secs, out_path):
    headers = {"xi-api-key": key, "Content-Type": "application/json",
               "Accept": "audio/mpeg"}
    payload = {
        "prompt": prompt,
        "music_length_ms": int(secs * 1000),
        "model_id": MODEL,
        "force_instrumental": True,
    }
    r = requests.post(f"{API}?output_format={OUTPUT_FORMAT}", headers=headers,
                      json=payload, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"Music API {r.status_code}: {r.text[:400]}")
    out_path.write_bytes(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="regenerate existing")
    ap.add_argument("--name", default=None,
                    help="track key to (re)generate; alternates reuse a spec's prompt")
    ap.add_argument("--spec", default="outro",
                    help="which TRACKS prompt to use when --name is an alternate")
    ap.add_argument("--secs", type=float, default=None, help="override length (s)")
    args = ap.parse_args()

    key = load_api_key()
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    names = [args.name] if args.name else list(TRACKS.keys())
    for name in names:
        spec = TRACKS.get(name) or TRACKS[args.spec]
        secs = args.secs or spec["secs"]
        out = MUSIC_DIR / f"{name}.mp3"
        if out.exists() and not args.force:
            print(f"  skip {name} (exists)")
            continue
        print(f"  compose {name}  ({secs:.0f}s) ...", end="", flush=True)
        compose(key, spec["prompt"], secs, out)
        print(f" -> {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
    print("done.")


if __name__ == "__main__":
    main()
