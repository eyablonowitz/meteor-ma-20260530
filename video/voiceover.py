"""Generate per-scene AI narration (scratch VO) with ElevenLabs.

Reads ELEVENLABS_API_KEY from the environment (or ../.env with `export KEY=...`).
Writes one mp3 per scene to video/assets/vo/sceneN.mp3. Re-runs skip scenes that
already exist unless --force.

Usage:
    source .env && python video/voiceover.py            # generate missing
    python video/voiceover.py --force                   # regenerate all
    python video/voiceover.py --voice <voice_id>        # pick a specific voice

Narration text is the spoken-only lines from video/script.md (kept in sync here).
"""
import argparse
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
VO_DIR = ROOT / "video" / "assets" / "vo"
API = "https://api.elevenlabs.io/v1"
MODEL = "eleven_multilingual_v2"          # high quality; ~720 words is cheap
# Warm-narrator preferences; first available wins. Override with --voice / env.
# Bill = wise, mature documentary narrator (locked in for this video).
PREFERRED = ["Bill", "Brian", "George", "Sarah", "Chris", "Daniel", "Adam"]

VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": True,
    "speed": 0.9,                # < 1.0 = slower, more relaxed delivery
}

# Curated narrator shortlist for --audition (warm/curious explainer voices).
AUDITION_SHORTLIST = [
    ("George", "JBFqnCBsd6RMkjVDRZzb"),   # British, warm captivating storyteller
    ("Brian", "nPczCjzI2devNBz1zQrb"),    # American, deep resonant, great narration
    ("Bill", "pqHfZKP75CvOlQylNhV4"),     # American, wise mature documentary
    ("Sarah", "EXAVITQu4vr4xnSDxMaL"),    # American female, warm reassuring
    ("Chris", "iP95p4xoKVk53GoZ742B"),    # American, down-to-earth, relatable
]
# One line with warmth + drama + a number, to hear range across voices.
AUDITION_SAMPLE = (
    "It's a gray Saturday afternoon. You're home. And then \u2014 boom. "
    "The windows rattle, the floor jumps. Four hundred miles away, people "
    "watched a fireball brighter than the full Moon. Here's the cool part: "
    "you can actually figure out what happened \u2014 yourself."
)

# Spoken narration only (no [VISUAL] notes). Mirror of video/script.md.
# Scene order (post-reorder): 1-4 felt experience -> 5 data+code -> 6 sightings
# (where) -> 7 light/sound (the ruler) -> 8 triangulation (precise where) ->
# 9 how big (acoustic pitch->energy) -> 10 the southward puzzle (3 synced beats)
# -> 11 your turn / open question.
SCENES = {
    "scene1": (
        "It's a gray Saturday afternoon. You're home. Nothing special. And then "
        "\u2014 boom. A deep, double crack you feel in your chest. The windows "
        "rattle. The floor jumps. Your first thought: did a tree just hit the "
        "house? Did something explode in the basement?"
    ),
    "scene2": (
        "You go outside and see your neighbors on the street too. You're all "
        "asking: did a transformer blow? A boiler? Someone says they heard sirens, "
        "a mile away. Then you check your social media on your phone. It's not "
        "just your street. People felt it ten, twenty, thirty miles away \u2014 in "
        "every direction. People who listen to firefighter and police radios say "
        "they don't know what happened either. And that's when it stops being "
        "exciting\u2026 and starts being scary. A gas explosion? An attack? Is "
        "anyone hurt?"
    ),
    "scene3": (
        "But minutes pass. And something doesn't add up. With that many people "
        "shaken, across that huge an area \u2014 nobody reports any real damage. "
        "No fire. No rubble. No injuries. A blast that big, but that gentle on the "
        "ground, can only mean one thing. Whatever exploded didn't go off near "
        "anyone. It went off high above everyone."
    ),
    "scene4": (
        "The sky exploded. A chunk of rock from space \u2014 a meteor \u2014 "
        "slammed into the atmosphere and blew apart, miles up. And once the fear "
        "fades, a better feeling takes over. Curiosity. Where exactly did the "
        "meteor explode? And how big was the explosion? And you realize: you can "
        "actually try to answer those questions yourself."
    ),
    "scene5": (
        "You start with public data, and a little bit of code. Earthquake "
        "sensors, weather satellites, people's reports get posted online, "
        "for free by governments and universities. So you write a small program "
        "that reaches out to those databases, downloads the raw numbers, and "
        "cleans them up. Now you can start asking questions from the data."
    ),
    # Scene 6 = WHERE (sightings); now BEFORE the light/sound ruler.
    "scene6": (
        "The first question you ask is: where did the meteor explode? The "
        "American Meteor Society collects data on big meteor fireball sightings. "
        "In Baltimore, people watched a fireball brighter than the full Moon in "
        "broad daylight. Reports came in from nine states, and two Canadian "
        "provinces. Some folks even caught it on their dashcams. But here, in "
        "eastern Massachusetts \u2014 right underneath it? Clouds. We heard the "
        "sky explode\u2026 but we couldn't see a thing. The people who could see "
        "it were the ones far enough away to look over the clouds. You get a clue "
        "from these reports that the meteor was probably over northeastern "
        "Massachusetts when it was seen. But you can do better."
    ),
    # Scene 7 = the ruler (light fast / sound slow); now AFTER sightings.
    "scene7": (
        "The visual reports of the fireball cluster around 2:06 PM Eastern time. "
        "But many people heard the boom around 2:11 \u2014 five minutes later. "
        "That's not a mistake. Light travels at about 186,000 miles per second, "
        "effectively instantaneous to our senses. But sound is slow. It takes "
        "seconds or minutes to cover distances we see in everyday life. That's "
        "why you see lightning before you hear the thunder. And that delay is "
        "secretly a ruler. It tells you how far away the blast really was."
    ),
    "scene8": (
        "And if we know the delay for a few different spots where the blast was "
        "heard, we can use that ruler to find the source. It turns out that "
        "there's an entire network of earthquake-detecting microphones around the "
        "country. Many are run by amateurs in their own backyards. And many of "
        "them picked up our meteor boom! Crucially, these listening stations "
        "record not only the sound, but also the time the sound occurred. The "
        "boom reaches different sensors at slightly different moments. Line up "
        "those arrival times, and you can trace the sound backward to its source. "
        "Our program reads through the sound data and does the math. And we get an "
        "answer: the blast happened high over northeastern Massachusetts, or "
        "southeastern New Hampshire."
    ),
    # Scene 9 = HOW BIG, reworked: acoustic only (pitch -> energy), lightning analogy.
    "scene9": (
        "So \u2014 how big was it? The boom itself tells "
        "you. The very same backyard sensors that pinned down the source also "
        "recorded the exact shape of the pressure wave. And the pitch of a blast "
        "works like a scale. A small bang cracks with a high, sharp snap. A giant "
        "one rumbles with a deep, slow note. Our boom rang the air with a low, "
        "two-second note \u2014 far too deep for a quarry blast, or a passing "
        "truck. Put those sound measurements through the physics, and they point "
        "to an explosion of about a couple hundred tons of TNT. One way to feel "
        "that: picture a few hundred lightning bolts \u2014 all striking in the "
        "very same instant. That's the punch the sky packed, miles above your "
        "head\u2026 which is exactly why it rattled half of New England."
    ),
    # Scene 10 = the southward puzzle, split into 3 narration-synced beats so each
    # animation panel (asymmetry / population / winds) stays locked to its line.
    "scene10a": (
        "But the data had a puzzle hiding in it. Almost everyone who reported "
        "feeling the boom was south of the blast. Hardly anyone to the north. Why?"
    ),
    "scene10b": (
        "Our first guess was simple: maybe more people just live to the south. "
        "Fair enough \u2014 so we checked. We lined up towns of the same size, the "
        "same distance away. Manchester, New Hampshire, to the north: zero "
        "reports. Lowell, Massachusetts, to the south: eight. Same size. Same "
        "distance. So it wasn't only about population \u2014 the boom really was "
        "louder to the south."
    ),
    # 10c split into two synced beats so the "WRONG" reveal can't precede the line.
    "scene10c1": (
        "Next guess: maybe high-altitude winds bent the sound southward, like a "
        "lens. A neat theory. So we pulled the actual wind data for that day\u2026"
    ),
    "scene10c2": (
        "And the winds were blowing the wrong way. Our theory was wrong."
    ),
    "scene11": (
        "But being wrong isn't failing. It's how we know there is more to learn. "
        "There's a real, open question here. One that you could help answer. "
        "Ready to get started?"
    ),
}


def load_api_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key.strip()
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?ELEVENLABS_API_KEY\s*=\s*(.+)\s*$", line)
            if m:
                return m.group(1).strip().strip('"').strip("'")
    sys.exit("ELEVENLABS_API_KEY not found (set env or add to .env). Aborting.")


def fetch_voices(key):
    r = requests.get(f"{API}/voices", headers={"xi-api-key": key}, timeout=30)
    r.raise_for_status()
    return r.json().get("voices", [])


def pick_voice(key, override):
    if override:
        return override, "(override)"
    voices = fetch_voices(key)
    # Account names are descriptive (e.g. "Bill - Wise, Mature, Balanced"); match
    # on the short name before the dash so PREFERRED can use plain first names.
    def short(v):
        return v["name"].split(" - ")[0].strip()
    by_short = {short(v): v for v in voices}
    for name in PREFERRED:
        if name in by_short:
            v = by_short[name]
            return v["voice_id"], v["name"]
    if voices:
        return voices[0]["voice_id"], voices[0]["name"]
    sys.exit("No ElevenLabs voices available on this account.")


def list_voices(key):
    voices = fetch_voices(key)
    print(f"{len(voices)} voices on this account:\n")
    for v in voices:
        labels = v.get("labels") or {}
        bits = [labels.get(k) for k in
                ("gender", "age", "accent", "descriptive", "use_case")]
        tags = ", ".join(b for b in bits if b)
        desc = (v.get("description") or "").strip().replace("\n", " ")
        print(f"  {v['name']:<26} {v['voice_id']}  [{v.get('category','')}]")
        if tags:
            print(f"      {tags}")
        if desc:
            print(f"      \u201c{desc[:110]}\u201d")


def audition(key):
    out_dir = VO_DIR / "auditions"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"auditioning {len(AUDITION_SHORTLIST)} voices "
          f"({len(AUDITION_SAMPLE)} chars each) -> {out_dir.relative_to(ROOT)}/")
    for name, vid in AUDITION_SHORTLIST:
        out = out_dir / f"{name}.mp3"
        print(f"  tts  {name} ...", end="", flush=True)
        tts(key, vid, AUDITION_SAMPLE, out)
        print(f" -> {out.name} ({out.stat().st_size//1024} KB)")
    print("done. Open the files in video/assets/vo/auditions/ to compare.")


def tts(key, voice_id, text, out_path):
    url = f"{API}/text-to-speech/{voice_id}"
    headers = {"xi-api-key": key, "Content-Type": "application/json",
               "Accept": "audio/mpeg"}
    payload = {"text": text, "model_id": MODEL, "voice_settings": VOICE_SETTINGS}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"TTS {r.status_code}: {r.text[:300]}")
    out_path.write_bytes(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="regenerate existing")
    ap.add_argument("--list", action="store_true", help="list account voices and exit")
    ap.add_argument("--audition", action="store_true",
                    help="generate narrator audition clips and exit")
    ap.add_argument("--voice", default=os.environ.get("ELEVENLABS_VOICE_ID"),
                    help="ElevenLabs voice_id override")
    args = ap.parse_args()

    key = load_api_key()
    if args.list:
        list_voices(key)
        return
    if args.audition:
        audition(key)
        return
    VO_DIR.mkdir(parents=True, exist_ok=True)
    voice_id, voice_name = pick_voice(key, args.voice)
    total_chars = sum(len(t) for t in SCENES.values())
    print(f"voice: {voice_name} ({voice_id[:6]}\u2026)  model: {MODEL}  "
          f"chars: {total_chars}")

    for name, text in SCENES.items():
        out = VO_DIR / f"{name}.mp3"
        if out.exists() and not args.force:
            print(f"  skip {name} (exists)")
            continue
        print(f"  tts  {name}  ({len(text)} chars) ...", end="", flush=True)
        tts(key, voice_id, text, out)
        print(f" -> {out.relative_to(ROOT)} ({out.stat().st_size//1024} KB)")

    print("done.")


if __name__ == "__main__":
    main()
