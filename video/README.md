# Video production guide — "The Day the Sky Exploded Over Massachusetts"

A short (~6 min), classroom-friendly explainer for MA high-schoolers, built from
the real analysis in this repo. The goal is to **spark curiosity and show that the
data is explorable**, not to teach the analysis in detail.

## Locked creative decisions
- **Length:** target **5–7 minutes** (current cut ~6:15). The earlier "<5 min"
  goal was relaxed: this material earns the extra minute or two as long as the
  middle stays tight. Trim flab, not the opener.
- **Narration:** AI voice (no on-camera host).
- **Visual style:** simple, stylized **comic-book** animation. *No photo-realism,
  no fake news footage.* Think clean flat colors, bold outlines, halftone dots,
  expressive lettering ("BOOM!"). Veritasium-style stylization is the direction,
  not the bar.

## Files
- `script.md` — the locked narration + visual directions (source of truth).
- `storyboard.md` — shot-by-shot list: visual, asset type, duration.
- `manim/` — code-driven science animations (created on request).
- `assets/` — drop generated images/clips/VO here (gitignored; see below).

## The pipeline (what happens where)

| Step | Tool | Notes |
|------|------|-------|
| 1. Script | **here (Cursor)** | done — `script.md`, grounded in real numbers |
| 2. Storyboard | **here** | done — `storyboard.md` |
| 3. Science animations | **here → Manim** | the ~6 MANIM shots; render to mp4/png |
| 4. Comic panels | **AI image-gen** (Midjourney / Flux / DALL·E) → light motion in editor or Runway/Kling | ~11 COMIC shots; keep a consistent style (see prompts) |
| 5. Voiceover | **ElevenLabs** (or OpenAI TTS) | one clip per scene; ~150 wpm |
| 6. Music + SFX | **real recording for the intro boom** + synthesized "wrong" sting (`sfx.py`); swap for YouTube Audio Library / Epidemic Sound at final mix | real meteor boom (`assets/sfx/*russianmeteorite*.mp3`) cue-synced to the word + a light "wrong" sting, auto-mixed by `rough_cut.py`; synth boom/rattle/rumble retired |
| 7. Assemble + caption | **Descript** (text-based, easiest for VO) or **DaVinci Resolve** (free) | burn-in captions for classrooms |
| 8. Review | accuracy + pacing pass | export 1080p |

**Why start in Cursor:** the script is written next to the actual data, and the
science shots are generated *from* that data (Manim), so the factual core stays
honest. Only the look-and-feel media (comic art, VO, edit) needs outside tools.

## Comic-book style: keep it consistent
Pick ONE style string and reuse it in every image prompt so panels match. Example
base style:

> *flat 2D comic-book illustration, bold black outlines, limited flat color
> palette (navy, teal, warm orange), subtle halftone dot shading, dramatic
> lighting, clean vector look, no text*

Per-panel prompt = base style + the shot. Examples (see `storyboard.md` for all):
- **1a** "…a teenager sitting on a couch in a New England living room, gray
  afternoon light through the window, calm before something happens"
- **4** "…storm clouds parting to reveal a brilliant fireball streaking across the
  sky, dramatic, awe and fear on a small figure below"
- **7c** "…a friendly map of New England covered in glowing dots representing
  ordinary people's phones and backyard sensors, 'you are here' energy"

Tips: generate a **character turnaround / style sheet** first and feed it back as
a reference image for consistency. Add on-screen lettering ("BOOM!", titles) in
the editor, not in the image, so you control fonts/legibility.

## Voiceover (ElevenLabs)
Scripted generator: `video/voiceover.py` renders one mp3 per scene (1–9) to
`assets/vo/`. The spoken text mirrors `script.md` (kept in the script's `SCENES`
dict). Needs `ELEVENLABS_API_KEY` (read from the env or `../.env`).

```bash
source venv/bin/activate
set -a && source .env && set +a        # exports ELEVENLABS_API_KEY
python video/voiceover.py              # generates missing sceneN.mp3
python video/voiceover.py --force      # regenerate all
python video/voiceover.py --voice <voice_id>   # pick a specific voice
```
- Auto-picks a warm narrator from a preference list (falls back to whatever the
  account has; pass `--voice` to lock one). Model `eleven_multilingual_v2`,
  Stability 0.5 / Similarity 0.75 / Style 0 — tweak `VOICE_SETTINGS` in the file.
- ~150 wpm; the full script is ~720 words (~3.8 min of VO).

## Rough cut (scratch assembly)
`video/rough_cut.py` stitches the real Manim science clips (scenes 5–8) +
placeholder title cards (scenes 1–4, 9, showing the narration text + "COMIC – to
be drawn") synced to the scratch VO into `video/rough_cut.mp4`. Each segment runs
`max(visual, narration)` so nothing is trimmed (science clips freeze the last
frame if VO runs long). Use it to feel pacing before any art exists.

```bash
python video/voiceover.py      # 1) make the VO (once)
python video/rough_cut.py      # 2) build video/rough_cut.mp4  (~6.1 min)
```
Output is 1280×720/30fps H.264 + AAC. Temp segments/cards land in `video/_rough/`.

## Manim (science animations) — setup
Manim renders the precise data shots. It needs `ffmpeg` (and optionally LaTeX for
equations — we avoid equations, so LaTeX is optional). Native deps via Homebrew.

```bash
# in the repo venv
source venv/bin/activate
brew install ffmpeg cairo pango pkg-config   # macOS; required native libs
pip install manim                            # installs manim 0.20.x
```

### The science scenes (9 clips from 6 files, all built)
Each Scene class matches its scene in `script.md`. Scene 10 is split into 4
separately-synced beats so each panel stays locked to its narration slice (a
panel can't get ahead of the voice). Big scene-title cards were removed (show,
don't tell). Beats in the continuous scenes (6 map, 7 flash→boom, 8
triangulation) are paced to the VO via `_sync.py`. Durations are from the
current Bill cut (~0.9 pace).

| File | Scene class | Script scene | ~Dur |
|------|-------------|--------------|------|
| `the_work.py` | `TheWork` | 5 — public data + code pipeline | 26.8s |
| `sightings_map.py` | `SightingsMap` | 6 — ~400 mi ring, 9 states+2 provinces, MA cloud | 52.2s |
| `flash_to_boom.py` | `FlashToBoom` | 7 — light fast / sound slow + clock→BOOM | 42.5s |
| `triangulation.py` | `Triangulation` | 8 — ripples to sensors → reverse-GPS X | 55.8s |
| `tnt_meter.py` | `TntMeter` | 9 — the boom's pitch is a scale → ≈ couple hundred t TNT | 60.8s |
| `southern_mystery.py` | `MysteryWhy` | 10a — felt reports cluster south → why? | 13.1s |
| `southern_mystery.py` | `MysteryPopulation` | 10b — matched pair (NH 0 vs MA 8) | 29.4s |
| `southern_mystery.py` | `MysteryWindsTheory` | 10c-1 — wind-lens theory + pulling wind data | 12.6s |
| `southern_mystery.py` | `MysteryWindsWrong` | 10c-2 — real winds sideways → WRONG | 7.3s |

`double_boom.py` is retained on disk but **cut** from the video.

### Render
```bash
# one scene, medium quality (720p30):
manim -qm video/manim/the_work.py TheWork

# all nine at once:
for v in the_work:TheWork sightings_map:SightingsMap flash_to_boom:FlashToBoom \
         triangulation:Triangulation tnt_meter:TntMeter \
         southern_mystery:MysteryWhy southern_mystery:MysteryPopulation \
         southern_mystery:MysteryWindsTheory southern_mystery:MysteryWindsWrong; do
  manim -qm "video/manim/${v%%:*}.py" "${v##*:}"
done
```
Note: `sightings_map.py` reads `assets/vo/scene6.mp3` (via `_sync.py`) to pace its
beats, so generate that VO before rendering it.
Quality flags: `-ql` fast preview, `-qm` medium, `-qh` 1080p, `-qk` 4K. Bump to
`-qh` for the final cut once timing/motion is approved.

Output lands in `media/videos/<file>/<res>/<Scene>.mp4` (gitignore `media/`).

### Preview stills (for quick review without playing video)
```bash
# grab a frame at 97% of a clip's duration:
mp4=media/videos/flash_to_boom/720p30/FlashToBoom.mp4
dur=$(ffprobe -v error -show_entries format=duration -of default=nk=1:nw=1 "$mp4")
ffmpeg -y -ss "$(python3 -c "print($dur*0.97)")" -i "$mp4" -frames:v 1 \
  video/manim/previews/FlashToBoom_end.png
```
Stills used during review live in `video/manim/previews/` (gitignorable).

### Shared look
All scenes inline the same flat comic palette (navy bg, teal, warm orange, cream,
red) and a bold `pop()` text helper, so they match the comic panels. Text uses
Pango (no LaTeX). Tweak colors at the top of any scene file.

## .gitignore additions (suggested)
```
video/assets/         # VO mp3s, generated art
video/_rough/         # rough-cut temp segments + font cache
video/manim/previews/ # review stills/frames
media/                # Manim render output
*.mp4                 # rendered clips + rough_cut.mp4
```
Commit the **script, storyboard, README, and Manim source**; keep heavy rendered
media out of git (store finals in Drive/YouTube).

## Suggested first build order
1. Approve/tweak `script.md` wording.
2. I generate the **Manim science shots** here (they're the credibility core).
3. You lock a comic **style sheet**, then batch-generate the ~11 panels.
4. Render VO → assemble in Descript → captions → music → export.

## Accuracy guardrails (don't undercut the lesson)
- Source location is **NE Massachusetts / SE New Hampshire**, ~40 mi up; *not* the
  bays (that was a satellite artifact).
- Energy ≈ a few hundred tons TNT (our acoustic ~186 t ↔ NASA's optical ~300 t).
- It was an **airburst** (double boom = fragmentation), not a simple fly-by.
- Keep the "our wind theory was wrong" beat — it's the most valuable part.
