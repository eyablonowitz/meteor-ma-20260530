# Storyboard / Shot List

Maps each narration beat (see `script.md`) to a visual, the asset *type* (which
tool makes it), and a rough duration. Asset types:

- **COMIC** — stylized comic-book panel/animation (AI image-gen → light motion).
- **MANIM** — code-driven science animation (precise; from our real data). Built.
- **FIGURE** — an existing chart from `outputs/` (optionally restyled).
- **TEXT** — title/end card.

Durations are measured from the current cut (Bill VO at ~0.9 pace).
◆ = new/process beat. ‹moved› notes the reorder.

**Show, don't tell:** the big scene-title cards were removed from the Manim shots
— the visuals + voice carry it now (small guiding captions only).

| # | On screen (visual) | Asset | Manim file | Narration cue | ~Dur |
|---|--------------------|-------|------------|---------------|------|
| 1 | **2 shots:** calm-on-couch *(push-in)* → **hard cut on "boom"** → startled + **BOOM** *(punch)* | COMIC | `scene1a`+`scene1b` | "It's a gray Saturday… boom." | 24s |
| 2 | **2 shots:** street + neighbors looking up *(push-in)* → **cut on "Then you check"** → phone close-up, pins flooding outward *(push-in)* | COMIC | `scene2a`+`scene2b` | "It's not just your street." | 41s |
| 3 | Felt-pins **clustered** over NE-MA / SE-NH (not all of New England); magnifier finds **no** fire/rubble/injuries *(pull-out reveal)* | COMIC | `scene3` | "nobody reports real damage." | 27s |
| 4 | **2 shots:** ominous overcast sky, Alex looks up *(push-in)* → **cut on "meteor"** → clouds part, fireball | COMIC | `scene4a`+`scene4b` | "The sky exploded… a meteor." | 25s |
| 5 ◆ | Code window pulls public data → table → charts (+ "free/public", clean-data beat) | MANIM | `the_work.py` *(27s)* | "public data + code." | 27s ✓ |
| 6 | NE-US map; ~400 mi ring; sightings; Baltimore callout; clouds-overhead; clue *(beats paced to the VO via `_sync`; Moon/dashcam icons removed)* | MANIM | `sightings_map.py` *(52s)* | "WHERE? seen 400 mi away — not here." | 52s ✓ ‹moved, was 7› |
| 7 | Flash 2:06; slow ring + clock → BOOM; lightning/thunder; ruler *(light speed corrected to ~186,000 mi/s; clip re-synced)* | MANIM | `flash_to_boom.py` *(39s)* | "light fast, sound slow — a *ruler*." | 40s ✓ ‹moved, was 6› |
| 8 | Network (earthquake mics, backyards) → arrival-time stamps → circles → **X** + answer *(beats paced to VO via `_sync`; script simplified)* | MANIM | `triangulation.py` *(56s)* | "trace the sound back to the source." | 56s ✓ |
| 9 ◆**REWORKED** | Pitch=scale → boom waveform + ~2 s note → dial **≈ a couple hundred t TNT** → lightning cluster | MANIM | `tnt_meter.py` *(redesigned, 56s)* | "HOW BIG? the boom's pitch is a scale." | 61s ✓ |
| 10 | Asymmetry → matched pair → wind theory **refuted** | MANIM | `southern_mystery.py` (**4 synced beats:** Why / Population / WindsTheory / WindsWrong) | "a puzzle: why all *south*? our theory was wrong." | 62s ‹moved, was 9› |
| 11 | Teen at laptop; end card + links | COMIC+TEXT | — | "being wrong isn't failing… **your turn.**" | 14s ‹now carries the open-question close› |

**Total ≈ 7.2 min** (scratch cut: `video/rough_cut.mp4`).

✓ **Freeze issue resolved:** the science clips were extended (more beats + holds)
to track the richer narration; freezes are now ≤ ~4 s each.

✓ **Comic panels in:** scenes 1–4 & 11 now use the AI comic panels
(`video/assets/comic/`, style per `comic_style.md`), scaled full-bleed into the
cut — no more placeholder cards. Lead character "Alex" is a teenage girl.

✓ **Comic motion (Ken Burns):** each panel gets a move (push-in / pull-out /
punch / drift). Rendered on a **3× (4K-ish) canvas** so `zoompan`'s whole-pixel
crop steps become sub-pixel after downscale — fixes the earlier "micro-shake."
`ZOOM = 0.18` (push/pull amount) is the single knob; raise/lower for more/less
move. Panels can **split into multiple shots that hard-cut on a narration cue**
— the cut time is `_sync.cue()` snapped to the nearest real pause
(`silencedetect`), so it survives a re-voice. **Splits so far:** S1 (calm →
**BOOM** on "boom"), S2 (street → phone on "Then you check"), S4 (overcast →
fireball on "meteor"). Scene 2 regenerated to drop a malformed sign; Scene 3
felt-area tightened to a NE-MA/SE-NH cluster (no longer overstates the area).

## Beat-to-narration sync (`video/manim/_sync.py`)
Two complementary techniques keep visuals locked to the voice:
- **Continuous scenes** (e.g. Scene 6 map) — each beat is *held until the matching
  phrase is spoken*. `_sync.cue("scene6", "But here, in eastern Massachusetts")`
  returns that phrase's approximate timestamp (char-offset × VO duration), so the
  cloud appears exactly on the line instead of drifting. Reusable for 7/8.
- **Panel scenes** (e.g. Scene 10) — *split into one sub-clip per narration slice*
  so a panel can't get ahead of the voice. Scene 10c is now **two** beats:
  `MysteryWindsTheory` (scene10c1: theory + "pulling the wind data") then
  `MysteryWindsWrong` (scene10c2: real winds sideways → **WRONG**). The "how
  science moves" coda was dropped (it lives in Scene 11 now).

## Scene 9 rework — LOCKED design
Focus: the **acoustic** size analysis only (the light-vs-sound comparison is
dropped), made **tangible** with one analogy.

- **Hero idea:** the *pitch/period* of the boom is a "scale" — a small bang snaps
  high; a giant blast rumbles with a deep, slow note. We read a ~2 s note off the
  **same backyard sensors** from Scene 8 → **a couple hundred tons of TNT**
  (acoustic geom-mean **186 t**; cleanest pitch/period method ≈ **65 t**).
- **Analogy (locked):** ≈ **a few hundred lightning bolts** striking at once —
  closes on "rattled New England without breaking a window" (ties back to Scene 3).
- **Animation:** redesign `tnt_meter.py` — **out:** twin light/sound gauges that
  "agree". **in:** boom waveform → highlight the slow ~2 s "note" → dial swings to
  ≈ a couple hundred tons of TNT → lightning-bolt cluster flashes at once.

### Locked decisions (Scene 9)
1. Hero mechanic = **"pitch of the boom → size"** (no 3-method bracket on screen).
2. Stated size = **"a couple hundred tons of TNT."**
3. Analogy = **lightning bolts** only.
4. Light/optical (NASA 300 t) = **dropped entirely** (acoustic story only).
5. Double-boom / airburst beat = **cut** (Scene 9 is purely about size).
6. "You are the data" (DYFI *I felt it*) = **left out** (sensor-network story stands).

**`double_boom.py` → CUT from the cut** (file kept on disk, no longer in the rough cut).

## Which existing figures can feed the comic/figure shots
- Shot 3 felt-pins → `outputs/felt_heatmap.png` / `map.html` (restyle as cartoon).
- Shot 6 sightings → AMS event page as *reference only*; we redraw it (don't ship
  AMS's image without permission).
- Shot 8 triangulation X → `outputs/location_map.png` (the real solution).
- Shot 9 how-big → `outputs/energy.json` (period-yield 65 t; geom-mean 186 t),
  `energy_summary.png`; boom waveform / double-boom → `record_section.png`.
- Shot 10 mystery → `outputs/population_vs_response.png`, `beaming_test.png`,
  `raytrace_era5_duct_vs_azimuth.png` (the real per-capita + wind evidence).

## Asset status (for planning)
- MANIM built: the_work, flash_to_boom, sightings_map, triangulation,
  southern_mystery (**4 sub-scenes**), tnt_meter (redesigned). double_boom (cut).
- Big scene-title cards removed from all Manim shots (show, don't tell).
- COMIC panels done & wired: scenes 1–4, 11 (5 panels) in `video/assets/comic/`.
- Title/end cards: 2.
