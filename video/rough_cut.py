"""Assemble a rough cut: real Manim science clips + comic panels + scratch VO.

For each scene we pair the narration (video/assets/vo/<key>.mp3) with a visual:
  - scenes 5-10 -> the rendered Manim clips (5=the_work, 6=sightings,
    7=flash/sound, 8=triangulation, 9=TNT meter, 10a/b/c=southern_mystery)
  - scenes 1-4, 11 -> AI comic panels (video/assets/comic/*.png) with a gentle
    Ken-Burns move (slow push-in / pull-out). A panel can be split into several
    "shots" that hard-cut on a narration cue -- e.g. Scene 1 holds on a calm
    "before" frame, then cuts to the BOOM frame right on the word "boom".
    If a panel image is missing we fall back to a placeholder title card.

Each segment runs for max(visual, narration) so nothing gets cut; the science
clips freeze their last frame if the narration runs longer. Everything is
normalized to 1280x720 / 30fps / AAC and concatenated into video/rough_cut.mp4.

Usage:  python video/rough_cut.py            # dev rough cut (with title card)
        python video/rough_cut.py --share    # clean shareable build: drops the
                                             # rough-cut card (opens cold on the
                                             # Scene 1 hook), web-optimized
                                             # (+faststart) -> meteor-ma-20260530.mp4
Prereqs: run video/voiceover.py (VO) and video/music.py (outro) first.
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "video" / "_rough"
WORK.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(WORK / ".mpl"))   # keep font cache in-repo

import matplotlib                                            # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from voiceover import SCENES                                 # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent / "manim"))
from _sync import cue                                        # noqa: E402

VO = ROOT / "video" / "assets" / "vo"
COMIC = ROOT / "video" / "assets" / "comic"
SFX = ROOT / "video" / "assets" / "sfx"
MUSIC = ROOT / "video" / "assets" / "music"
OUT = ROOT / "video" / "rough_cut.mp4"
SHARE_OUT = ROOT / "video" / "meteor-ma-20260530.mp4"  # clean build for sharing

# Sound design, mixed UNDER the narration. The intro boom is a real recording;
# the "wrong" sting is still synthesized (see video/sfx.py).
#   (scene_key, time_spec, file, gain)   time_spec: ("cue", phrase, off) | ("at", s)
# off for the boom = -0.30 so the file's peak (~0.30s in) lands on the word.
SFX_CUES = [
    ("scene1", ("cue", "boom", -0.30),
     "freesound_community-russianmeteorite_sfx-76195.mp3", 0.80),   # real meteor boom
    ("scene10c2", ("at", 2.9), "sting.wav", 0.32),                  # "theory was wrong"
]

NAVY = "#0d1b2a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
MUTED = "#8d99ae"
W, H, FPS = 1280, 720, 30


def clip(name, scene=None):
    scene = scene or "".join(p.capitalize() for p in name.split("_"))
    return ROOT / "media" / "videos" / name / "720p30" / (scene + ".mp4")


# A panel payload is a dict:
#   shots: list of (filename, motion) played in order. motion is one of
#          push_in | pull_out | punch | drift.
#   cuts:  optional list of (phrase, offset_s); cut to the next shot at
#          cue(phrase)+offset. Needs len(cuts) == len(shots)-1. Omit for a
#          single-shot panel (it just gets a Ken-Burns move across the scene).
def panel(shots, cuts=None, pan=False, reveal=None):
    return {"shots": shots, "cuts": cuts or [], "pan": pan, "reveal": reveal}


# storyboard order; (scene-key or None, kind, payload, kicker, title)
SEGMENTS = [
    (None, "card", None, "ROUGH CUT  \u2022  scratch AI narration",
     "The Day the Sky Exploded Over Massachusetts"),
    ("scene1", "panel",
     panel([("scene1a.png", "push_in"), ("scene1b.png", "punch")],
           cuts=[("boom", -0.05)]),  # snap to the pause before "boom", land on word
     "SCENE 1  \u2014  COMIC", "The thud"),
    ("scene2", "panel",
     panel([("scene2a.png", "push_in"), ("scene2b.png", "push_in")],
           cuts=[("You check social media", 0.0)]),  # street -> cut to the phone
     "SCENE 2  \u2014  COMIC", "Bigger than your house"),
    ("scene3", "panel", panel([("scene3.png", "pull_out")]),
     "SCENE 3  \u2014  COMIC", "The clue in what didn't happen"),
    ("scene4", "panel",
     panel([("scene4_pan.png", "pan"), ("scene4_react.png", "push_in")],
           cuts=[("Curiosity", 0.0)], pan=True, reveal=("meteor", 0.0)),
     "SCENE 4  \u2014  COMIC", "It came from space"),
    ("scene5", "clip", [clip("the_work")], "SCENE 5  \u2014  MANIM",
     "Not magic: public data + code"),
    ("scene6", "clip", [clip("sightings_map")], "SCENE 6  \u2014  MANIM",
     "Seen 400 miles away \u2014 but not here"),
    ("scene7", "clip", [clip("flash_to_boom")], "SCENE 7  \u2014  MANIM",
     "Light is fast, sound is slow"),
    ("scene8", "clip", [clip("triangulation")], "SCENE 8  \u2014  MANIM",
     "Finding it with sound"),
    ("scene9", "clip", [clip("tnt_meter")], "SCENE 9  \u2014  MANIM (reworked)",
     "How big? The boom is a scale"),
    ("scene10a", "clip", [clip("southern_mystery", "MysteryWhy")],
     "SCENE 10a  \u2014  MANIM", "A puzzle: why all south?"),
    ("scene10b", "clip", [clip("southern_mystery", "MysteryPopulation")],
     "SCENE 10b  \u2014  MANIM", "Not just population"),
    ("scene10c1", "clip", [clip("southern_mystery", "MysteryWindsTheory")],
     "SCENE 10c  \u2014  MANIM", "Wind-lens theory"),
    ("scene10c2", "clip", [clip("southern_mystery", "MysteryWindsWrong")],
     "SCENE 10c  \u2014  MANIM", "Theory wrong"),
    ("scene11", "panel", panel([("scene11_v2.png", "push_in")]),
     "SCENE 11  \u2014  COMIC", "Your turn"),
    ("outro", "outro", None, "OUTRO  \u2014  CREDITS",
     "Thanks + retro-futuristic music"),
]


def ffprobe_dur(p):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", str(p)])
    return float(out.strip())


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.PIPE)


def make_card(path, kicker, title, body):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    fig.patch.set_facecolor(NAVY)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off"); ax.set_facecolor(NAVY)
    ax.text(0.5, 0.84, kicker, ha="center", va="center", color=ORANGE,
            fontsize=18, fontweight="bold", transform=ax.transAxes)
    ax.text(0.5, 0.70, "\n".join(textwrap.wrap(title, 34)), ha="center",
            va="center", color=CREAM, fontsize=32, fontweight="bold",
            transform=ax.transAxes)
    if body:
        ax.text(0.5, 0.40, "\n".join(textwrap.wrap(body, 60)), ha="center",
                va="center", color="#c9d2de", fontsize=17,
                transform=ax.transAxes, linespacing=1.5)
    fig.savefig(path, facecolor=NAVY); plt.close(fig)


VF_FIT = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}")
# full-bleed: scale up to cover the frame, then center-crop (no distortion)
VF_COVER = (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1,fps={FPS}")


def seg_from_image(idx, img, vo, dur, vf=f"scale={W}:{H},setsar=1,fps={FPS}"):
    out = WORK / f"seg{idx:02d}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img)]
    if vo:
        cmd += ["-i", str(vo)]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-filter_complex",
            f"[0:v]{vf}[v];[1:a]aresample=44100,apad[a]",
            "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k", str(out)]
    run(cmd)
    return out


def normalize_clip(path, dst):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-an",
         "-vf", VF_FIT, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
         str(dst)])
    return dst


def concat_videos(idx, clips):
    if len(clips) == 1:
        return normalize_clip(clips[0], WORK / f"vis{idx:02d}.mp4")
    parts = []
    for j, c in enumerate(clips):
        parts.append(normalize_clip(c, WORK / f"vis{idx:02d}_{j}.mp4"))
    lst = WORK / f"vis{idx:02d}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = WORK / f"vis{idx:02d}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(out)])
    return out


def seg_outro(idx, vis, music, dur, gain=0.85, fade_out=1.6):
    """Outro segment: silent Manim credits visual + the generated music as its
    own audio (gentle fade in/out, fit to the visual length)."""
    out = WORK / f"seg{idx:02d}.mp4"
    af = (f"[1:a]aresample=44100,volume={gain},"
          f"afade=t=in:st=0:d=0.8,"
          f"afade=t=out:st={max(0.0, dur - fade_out):.2f}:d={fade_out},"
          f"apad,atrim=0:{dur:.3f}[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vis), "-i", str(music),
         "-filter_complex", f"[0:v]setsar=1[v];{af}",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k", str(out)])
    return out


def seg_from_clip(idx, vis, vo, dur):
    out = WORK / f"seg{idx:02d}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vis), "-i", str(vo),
         "-filter_complex",
         f"[0:v]tpad=stop_mode=clone:stop_duration=3600[v];"
         f"[1:a]aresample=44100,apad[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-ar", "44100", "-ac", "2", "-b:a", "128k", str(out)])
    return out


# --- comic-panel motion (Ken Burns) -----------------------------------------
# Render the move on a big (4K-ish) canvas: zoompan steps the crop origin in
# whole pixels, so on a 3x canvas a 1px step is ~1/3px after downscale -> the
# glide reads smooth instead of a 1px stutter ("shake"). ZOOM is the push/pull
# amount; bump it for a more deliberate, cinematic move.
UPSCALE = 4      # bigger canvas -> finer sub-pixel steps -> smoother glide
ZOOM = 0.14      # gentler push; large moves make zoompan's micro-steps visible


def _zoom_expr(motion, n):
    """zoompan z-expression over n output frames (variable `on` = 0..n-1)."""
    d = max(1, n - 1)
    if motion == "push_in":
        return f"1.0+{ZOOM}*on/{d}"
    if motion == "pull_out":
        return f"{1.0 + ZOOM}-{ZOOM}*on/{d}"
    if motion == "punch":          # snap in, then ease out to rest (a recoil)
        return f"1.0+0.16*pow(1-on/{d},2)"
    return f"1.0+0.03*on/{d}"      # "drift" — barely-there life


_sil_cache = {}


def _silence_ends(key):
    """End-times of silent gaps in a scene's VO (onsets of the next word)."""
    if key in _sil_cache:
        return _sil_cache[key]
    p = VO / f"{key}.mp3"
    ends = []
    if p.exists():
        res = subprocess.run(
            ["ffmpeg", "-hide_banner", "-nostats", "-i", str(p),
             "-af", "silencedetect=noise=-32dB:d=0.25", "-f", "null", "-"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        txt = res.stderr.decode("utf-8", "ignore")
        ends = [float(m) for m in re.findall(r"silence_end:\s*([0-9.]+)", txt)]
    _sil_cache[key] = ends
    return ends


def _snap_to_silence(key, approx, tol=1.3):
    """Nudge a char-proportional cue onto the nearest real pause (the dramatic
    beat before the next word), so cuts land on the word even with pauses."""
    cands = [e for e in _silence_ends(key) if abs(e - approx) <= tol]
    return min(cands, key=lambda e: abs(e - approx)) if cands else approx


def motion_clip(out, img, dur, motion):
    n = max(2, int(round(dur * FPS)))
    z = _zoom_expr(motion, n)
    base = (f"scale={UPSCALE * W}:{UPSCALE * H}:force_original_aspect_ratio="
            f"increase,crop={UPSCALE * W}:{UPSCALE * H},setsar=1")
    zp = (f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"d={n}:s={W}x{H}:fps={FPS}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(img),
         "-vf", f"{base},{zp},format=yuv420p", "-frames:v", str(n), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out


def pan_clip(out, img, dur, t_cut, pan_dur=1.6):
    """Vertical reveal across a TALL image: hold on the bottom (ground/clouds),
    then pan straight up to the top (the fireball), centred on t_cut so the
    reveal lands on the narration cue. Rendered on a 2x crop then downscaled so
    the glide is sub-pixel smooth."""
    n = max(2, int(round(dur * FPS)))
    cw, ch = 3 * W, 3 * H
    t0 = max(0.0, t_cut - pan_dur / 2.0)
    # y(t): hold (ih-ch) until t0, ramp to 0 over pan_dur, then hold 0
    y = f"(ih-{ch})*(1-clip((t-{t0:.3f})/{pan_dur:.3f},0,1))"
    vf = (f"scale={cw}:-2,crop={cw}:{ch}:0:'{y}',scale={W}:{H},"
          f"setsar=1,format=yuv420p,fps={FPS}")
    run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img),
         "-vf", vf, "-frames:v", str(n), "-an",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
    return out


def build_panel(idx, key, spec, vo, dur):
    """Render a comic panel (one or more motion shots) and mux the VO."""
    shots = spec["shots"]
    if spec.get("pan"):
        # the `reveal` cue drives the up-pan (fireball uncovered on that word)
        rev = spec.get("reveal")
        rt = cue(key, rev[0]) if rev else None
        t_cut = (_snap_to_silence(key, rt) + rev[1]) if rt is not None else dur * 0.3
        if len(shots) == 1:
            vis = pan_clip(WORK / f"vis{idx:02d}.mp4", COMIC / shots[0][0],
                           dur, t_cut)
            return seg_from_clip(idx, vis, vo, dur)
        # pan shot [0, pan_end] then hard-cut to a follow-on shot (e.g. the
        # curiosity reaction) for [pan_end, dur], cut on cuts[0].
        ph, off = spec["cuts"][0]
        pe = cue(key, ph)
        pan_end = (_snap_to_silence(key, pe) + off) if pe is not None else dur * 0.6
        pan_end = min(max(pan_end, t_cut + 1.2), dur - 1.2)
        p1 = pan_clip(WORK / f"pan{idx:02d}_0.mp4", COMIC / shots[0][0],
                      pan_end, t_cut)
        p2 = motion_clip(WORK / f"pan{idx:02d}_1.mp4", COMIC / shots[1][0],
                         dur - pan_end, shots[1][1])
        lst = WORK / f"vis{idx:02d}.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in (p1, p2)))
        vis = WORK / f"vis{idx:02d}.mp4"
        run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(lst), "-c", "copy", str(vis)])
        return seg_from_clip(idx, vis, vo, dur)
    if len(shots) == 1:
        vis = motion_clip(WORK / f"vis{idx:02d}.mp4", COMIC / shots[0][0],
                          dur, shots[0][1])
        return seg_from_clip(idx, vis, vo, dur)

    # multi-shot: cut to the next shot at cue(phrase)+offset (even split if the
    # cue can't be located).
    edges = [0.0]
    for j, (phrase, off) in enumerate(spec["cuts"]):
        t = cue(key, phrase)
        if t is not None:
            t = _snap_to_silence(key, t) + off
        else:
            t = dur * (j + 1) / len(shots)
        edges.append(min(max(t, edges[-1] + 0.3), dur - 0.3))
    edges.append(dur)

    parts = []
    for j, (fname, motion) in enumerate(shots):
        sub = max(0.3, edges[j + 1] - edges[j])
        parts.append(motion_clip(WORK / f"pan{idx:02d}_{j}.mp4",
                                 COMIC / fname, sub, motion))
    lst = WORK / f"vis{idx:02d}.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    vis = WORK / f"vis{idx:02d}.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(vis)])
    return seg_from_clip(idx, vis, vo, dur)


def mix_sfx(src, dst, abs_cues):
    """Layer delayed SFX under the assembled cut (normalize=0 keeps the VO at
    full level; a limiter catches summed peaks). Video is stream-copied and the
    container is web-optimized (+faststart) so it streams without a full download."""
    inputs = ["-i", str(src)]
    for wav, _, _ in abs_cues:
        inputs += ["-i", str(wav)]
    fc, labels = [], ["[0:a]"]
    for i, (wav, ta, g) in enumerate(abs_cues, start=1):
        ms = int(max(0.0, ta) * 1000)
        # normalize rate/layout first so mp3 + wav inputs mix cleanly with the bed
        fc.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                  f"adelay={ms}:all=1,volume={g}[s{i}]")
        labels.append(f"[s{i}]")
    fc.append("".join(labels) + f"amix=inputs={len(abs_cues) + 1}:normalize=0,"
              "alimiter=limit=0.95[a]")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs,
         "-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-ar", "44100", "-ac", "2",
         "-b:a", "160k", "-movflags", "+faststart", str(dst)])


def main(share=False):
    # The shareable build drops the "ROUGH CUT / scratch narration" title card so
    # the film opens cold on the Scene 1 hook.
    segments = [s for s in SEGMENTS
                if not (share and s[1] == "card" and s[0] is None)]
    out = SHARE_OUT if share else OUT
    segs = []
    starts = {}
    total = 0.0
    for idx, (key, kind, payload, kicker, title) in enumerate(segments):
        if key:
            starts[key] = total
        vo = VO / f"{key}.mp3" if key else None
        vo_dur = ffprobe_dur(vo) if vo and vo.exists() else 0.0

        if kind == "outro":
            vis = concat_videos(idx, [clip("outro")])
            dur = ffprobe_dur(vis)
            music = MUSIC / "outro.mp3"
            seg = (seg_outro(idx, vis, music, dur) if music.exists()
                   else seg_from_image(idx, WORK / f"card{idx:02d}.png", None, dur))
            segs.append(seg)
            total += dur
            print(f"  seg{idx:02d}  {kind:5s}  {title[:34]:34s}  {dur:5.1f}s  "
                  f"{'+music' if music.exists() else '(no music)'}")
            continue

        have_imgs = (kind == "panel" and payload and
                     all((COMIC / s[0]).exists() for s in payload["shots"]))
        if have_imgs:
            dur = (vo_dur + 0.8) if vo else 4.0
            seg = build_panel(idx, key, payload, vo, dur)
        elif kind in ("card", "panel"):
            body = SCENES.get(key, "") if key else (
                "Real Manim science shots in scenes 5-10.  Comic panels in "
                "scenes 1-4 & 11.  AI scratch narration for timing.")
            img = WORK / f"card{idx:02d}.png"
            make_card(img, kicker, title, body)
            dur = (vo_dur + 0.6) if vo else 3.0
            seg = seg_from_image(idx, img, vo, dur)
        else:
            vis = concat_videos(idx, payload)
            vis_dur = ffprobe_dur(vis)
            dur = max(vis_dur, vo_dur) + 0.4
            seg = seg_from_clip(idx, vis, vo, dur)

        segs.append(seg)
        total += dur
        print(f"  seg{idx:02d}  {kind:5s}  {title[:34]:34s}  {dur:5.1f}s")

    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in segs))
    raw = WORK / "cut_raw.mp4"
    run(["ffmpeg", "-y", "-loglevel", "error", "-fflags", "+genpts",
         "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(raw)])

    # resolve SFX placements to absolute timeline positions and mix them in
    abs_cues = []
    for key, spec, wav, g in SFX_CUES:
        wavp = SFX / wav
        if key not in starts or not wavp.exists():
            continue
        if spec[0] == "cue":
            ct = cue(key, spec[1])
            if ct is None:
                continue
            ta = starts[key] + _snap_to_silence(key, ct) + spec[2]
        else:
            ta = starts[key] + spec[1]
        abs_cues.append((wavp, ta, g))
    if abs_cues:
        mix_sfx(raw, out, abs_cues)
        print(f"  sfx: mixed {len(abs_cues)} cue(s)")
    else:
        shutil.copy(raw, out)
    label = "share build" if share else "rough cut"
    print(f"\n{label}: {out.relative_to(ROOT)}  (~{total:.0f}s, {total/60:.1f} min)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--share", action="store_true",
                    help="drop the rough-cut title card and write the clean "
                         "shareable build (video/meteor-ma-20260530.mp4)")
    main(share=ap.parse_args().share)
