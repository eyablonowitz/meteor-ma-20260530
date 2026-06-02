"""Beat-sync helper for Manim science shots.

Maps a phrase in a scene's narration to its approximate start time in the
rendered ElevenLabs VO, so animation beats can be paced to the voice instead of
hand-guessed. Uses proportional timing (character offset x VO duration) -- a good
first-order sync for steady narration. Swap in word-level timestamps later for
exactness.

Usage in a Scene:
    from _sync import cue
    t_cloud = cue("scene6", "But here, in eastern Massachusetts")
    # ... then hold the animation until t_cloud before playing that beat.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VO = ROOT / "video" / "assets" / "vo"
sys.path.insert(0, str(ROOT / "video"))

try:
    from voiceover import SCENES
except Exception:
    SCENES = {}

_dur_cache = {}


def vo_duration(key):
    if key in _dur_cache:
        return _dur_cache[key]
    p = VO / f"{key}.mp3"
    d = 0.0
    if p.exists():
        try:
            out = subprocess.check_output([
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nk=1:nw=1", str(p)])
            d = float(out.strip())
        except Exception:
            d = 0.0
    _dur_cache[key] = d
    return d


def cue(key, phrase=None, lead=0.0):
    """Approximate seconds into the VO where `phrase` begins.

    phrase=None -> 0.0. Returns None if the phrase isn't found (callers should
    treat None as "don't wait"). `lead` shifts the cue earlier so a visual can
    land just before the word is spoken.
    """
    text = SCENES.get(key, "")
    dur = vo_duration(key)
    if not phrase:
        return 0.0
    if not text or dur <= 0:
        return None
    i = text.find(phrase)
    if i < 0:
        return None
    return max(0.0, (i / len(text)) * dur - lead)
