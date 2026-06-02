# Comic Style Sheet — "The Day the Sky Exploded Over Massachusetts"

The comic panels (Scenes 1–4 and 11) carry the *human* story; the Manim shots
(5–10) carry the *science*. To make it feel like **one film**, the comic shares
the exact palette and a flat, stylized look with the science scenes — no
photo-realism, no fake "news footage."

**Reference art (approved look):**
- Character + palette + motifs: `assets/comic/style_sheet.png`
- Style-in-a-beat sample (Scene 1): `assets/comic/scene1_sample.png`

This sheet is the single source of truth for generating those panels: a fixed
**palette**, a fixed **character**, recurring **motifs**, and copy-paste
**prompt blocks** so every panel looks like it came from the same hand.

---

## Palette (shared with the Manim science shots)

| Hex | Name | Role in the comic |
|-----|------|-------------------|
| `#0d1b2a` | **navy** | backgrounds, night/indoor shadow, sky base |
| `#f7f3e3` | **cream** | key light, paper, highlights, "safe" daylight |
| `#2ec4b6` | **teal** | calm/curiosity accent, sound ripples, UI, hoodie |
| `#ff9f1c` | **orange** | energy/heat — the fireball, warm light, emphasis |
| `#e71d36` | **red** | alarm — the BOOM, danger, "something's wrong" |
| `#8d99ae` | **slate** | secondary shapes, mid shadows, overcast sky, crowd |

Rule of thumb: **navy + cream + slate** is the neutral base of every panel; add
**teal** for calm/curious beats, **orange** for the meteor/heat, **red** only
for the shock beats (the boom, the scare).

---

## Art direction

- **Flat modern explainer-comic / editorial illustration.** Think bold, clean
  vector-like shapes with a confident ink outline — not painterly, not 3D.
- **Linework:** consistent medium-weight dark outline (near-black navy), rounded
  corners, minimal interior detail. Faces are simple and expressive (a few
  decisive strokes), not realistic.
- **Shading:** 1–2 flat tones per shape (base + one shadow). Optional **subtle
  paper grain / faint halftone** for texture. Avoid heavy gradients and glows.
- **Lighting:** strong, graphic, single-source. Cool navy shadow vs. warm cream
  light; the meteor adds an orange rim light.
- **Mood arc:** cozy-but-bored → startled → unsettled/scary → awe → empowered.
- **Avoid:** photorealism, lens flares, watermarks, signatures, gibberish text,
  busy backgrounds, extra fingers, brand logos, realistic gore.

---

## The protagonist — "Alex"

A relatable Massachusetts high-schooler — **a teenage girl**. Keep the design
**simple and iconic** so it redraws consistently across panels.

- **Age/build:** ~16, average build.
- **Hair:** dark, loosely curly, shoulder-length (often pulled back in a curly
  ponytail) — a clear, easy-to-redraw silhouette.
- **Skin:** warm light-brown.
- **Face:** thick expressive eyebrows, small nose, simple dot/curve eyes; big,
  readable expressions.
- **Wardrobe:** **teal hoodie** over a cream tee, dark-slate joggers, simple
  sneakers. (The teal hoodie ties Alex to the science-scene palette.)
- **Consistency tips:** same hoodie + hair silhouette in every panel; keep
  detail low; vary pose/expression, not the design.

> Skin tone, hair, and wardrobe color are all easy to change later if you want a
> different look for the lead.

**Expression set we need:** bored/relaxed → startled (wide eyes) → worried →
wonder/awe (lit from above) → determined/curious (at the laptop).

---

## Recurring motifs / props

- **The BOOM:** jagged red comic lettering + concentric shock lines. Red only.
- **Sound ripples:** thin **teal** concentric arcs (echo the Manim sound rings).
- **The phone:** a simple slab with a **map + teal/orange pins** popping in.
- **The fireball:** an **orange** streak with a cream-hot core and a short trail.
- **Felt-map:** stylized New England silhouette dotted with pins (Scene 3).
- **Overcast light:** flat slate sky, soft cream window light (the "gray
  Saturday" — this is a cloudy day; keep skies muted, not blue).
- **The laptop (Scene 11):** screen shows our *real* stylized maps/charts.

---

## Format & motion

- **Canvas:** 16:9, render at/above 1280×720. Compose with a **lower-third
  safe zone** kept clear — captions/VO live there; **bake no narration text**
  into the art (small diegetic words like "BOOM" are fine).
- **Motion (implemented in `rough_cut.py` via an ffmpeg Ken-Burns move on a
  3× / 4K-ish canvas, so `zoompan`'s whole-pixel steps become sub-pixel after
  downscale — no jitter):** each shot gets a `motion` tag — `push_in`,
  `pull_out`, `punch` (snap-in recoil), or `drift` (barely-there). `ZOOM = 0.18`
  is the global push/pull amount (one knob). Current assignments:
  - **S1** `scene1a` **push-in** (calm) → cut on "boom" → `scene1b` **punch**;
  - **S2** `scene2a` **push-in** (street) → cut on "Then you check" → `scene2b`
    **push-in** (phone close-up, pins flooding);
  - **S3** **pull-out** to reveal the (focused) felt-cluster;
  - **S4** `scene4a` **push-in** (overcast) → cut on "meteor" → `scene4b`
    **push-in** (fireball);
  - **S11** push-in on the laptop.
- **Multi-shot panels & cut-on-cue:** a panel can list several shots that
  hard-cut on a narration cue. The cut time comes from `_sync.cue()` (char-
  proportional) **snapped to the nearest real pause** via `silencedetect`, so a
  beat like Scene 1's boom lands on the spoken word even after a re-voice.
- **Splitting a beat:** when a panel needs a *before/after* (like S1), draw two
  images that share the same room/composition (use the first as a reference
  image when generating the second) so the cut reads as one continuous space.

---

## Reusable prompt blocks

Paste **[STYLE]** + **[ALEX]** into every panel prompt, then add the panel's
**Composition** line. (Keep a negative-prompt handy too.)

**[STYLE]**
> Flat modern explainer-comic illustration, bold clean dark linework, limited
> flat color palette, simple geometric shapes, subtle paper-grain texture,
> strong graphic single-source lighting, cinematic 16:9 composition, no
> photorealism, no gradients-heavy rendering. Palette strictly: deep navy
> #0d1b2a backgrounds, cream #f7f3e3 light, teal #2ec4b6 and warm orange #ff9f1c
> accents, alarm red #e71d36 for shock, slate #8d99ae shadows.

**[ALEX]**
> Alex, a ~16-year-old teenage girl with dark curly shoulder-length hair (often
> in a curly ponytail), warm light-brown skin, thick expressive eyebrows,
> wearing a teal hoodie over a cream tee and dark joggers; simple iconic cartoon
> features, consistent design.

**[NEGATIVE]**
> photorealistic, 3D render, photograph, lens flare, watermark, signature,
> text, captions, gibberish letters, extra fingers, deformed hands, logos,
> blue sunny sky, cluttered background.

---

## Panel prompts (Scenes 1–4, 11)

Each panel: **[STYLE]** + **[ALEX]** + the Composition below. Leave the
lower-third clear for captions. Filenames land in `video/assets/comic/`.

### Scene 1 — The thud  → split: `scene1a.png` (before) + `scene1b.png` (after)
**Same room in both shots** so the cut reads as one space (gray couch, framed
picture, overcast window, coffee table w/ mug + phone). Hard-cut from **a** → **b**
on the word "boom".
- **1a (before):** interior, gray Saturday afternoon; Alex slouched **relaxed /
  bored** on the couch, idly on her phone; everything calm and orderly (picture
  straight, mug still). No boom. → slow **push-in**.
- **1b (after / the boom):** the room **jolts** — a jagged red **"BOOM"** bursts
  in the air, red shock lines, the picture tilts, the mug ripples, the phone
  dropped on the table; Alex startled, wide-eyed, gripping the cushion. →
  **punch** (snap-in recoil). Mostly navy/cream/slate with the boom in red.

*(Legacy single-image `scene1.png` is kept as the source for `scene1b.png`.)*

### Scene 2 — Bigger than your house  → split: `scene2a.png` + `scene2b.png`
Cut from **a** → **b** on "Then you check…".
- **2a (street):** exterior suburban MA street, flat overcast sky. Alex on the
  sidewalk among neighbors who all **look up / around**, confused — "did you
  hear that too?". **No phone in frame.** Faint teal sound-ribbon. → **push-in**.
- **2b (phone):** tight **over-the-shoulder close-up** of Alex's hands holding a
  phone; the screen is a regional map **flooding with teal/orange pins and
  social-post bubbles** radiating from a central point. → **push-in**.
- *(No street/welcome signs — caused a malformed-figure artifact earlier.)*
- *(Legacy `scene2.png` kept; superseded by the a/b split.)*

### Scene 3 — The clue in what didn't happen  → `scene3.png`
A stylized **map of New England**. **Important:** the felt-report teal pins are a
**focused cluster over NE-MA / SE-NH** (dense center, thinning fast) — *not*
blanketing the whole region (don't overstate the felt area). A big **magnifier**
finds **no fire, no rubble, no injuries** (red circle-slash icons); one orange
**thought-bulb** cues the insight. Calm, analytical. Navy base, cream map, slate
land, teal pins. → **pull-out** reveal.

### Scene 4 — It came from space  → split: `scene4a.png` + `scene4b.png`
Cut from **a** → **b** on the word "meteor" (same low-angle framing in both, Alex
small at the bottom looking up).
- **4a (before):** a heavy flat **overcast** sky fills the frame, ominous, a
  faint cream glow building behind the clouds — **no fireball yet**. Quiet dread.
  → **push-in**.
- **4b (reveal):** the clouds **part** to a brilliant **orange fireball** with a
  cream-hot core, warm rim-light on the clouds; Alex lit orange, in awe. →
  **push-in**.
- *(Legacy `scene4.png` is the source for `scene4b.png`.)*

### Scene 11 — Your turn  → `scene11.png`
Interior, warmer now. Alex at a desk, **determined and curious**, lit by a
**laptop** whose screen shows our stylized maps/charts (a felt-map and a ring of
sensor dots — teal/orange on navy). Cream key light on Alex's face, teal screen
glow. Optimistic, inviting. Navy room, teal screen light, cream highlights.

---

## Pipeline (how panels enter the cut)

1. Generate each panel from its prompt; save as `video/assets/comic/sceneN.png`
   (1280×720 or larger, 16:9).
2. In `rough_cut.py`, switch that scene's segment from a `card` to an image
   segment (the existing `seg_from_image` already pairs an image + the scene's
   VO and holds for the narration). The placeholder cards are the drop-in target.
3. Add the per-panel **light motion** (ffmpeg zoom/pan/shake or a thin Manim
   overlay) once the stills are approved.

Status: style locked here → next is approving the look (style-sheet image +
Scene 1 sample), then generating all five panels.
