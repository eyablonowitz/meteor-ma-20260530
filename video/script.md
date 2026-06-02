# "The Day the Sky Exploded Over Massachusetts" — Narration Script

- **Runtime target:** ~6–7 min (relaxed, classroom-friendly)
- **Audience:** smart MA high-schoolers — many of whom *felt* this
- **Voice:** AI narration, **~0.9 speed** (unhurried, warm, curious, a little
dramatic). Let beats breathe.
- **Goal:** spark curiosity, show *how the work is actually done* (public data +
code + testing your guesses) — NOT teach the analysis in detail
- **Look:** simple stylized comic-book animation (no photo-realism)

Timecodes are approximate. Narration is what the AI voice says; **[VISUAL]**
notes are for the storyboard/animation. `…` and `—` mark breathing pauses.

---

## SCENE 1 — The thud (~0:00)

**[VISUAL]** COMIC: a teen on a couch, gray light through the window. Sudden
jagged **"BOOM"**; window lines buzz; a picture frame tilts.

> It's a gray Saturday afternoon. You're home. Nothing special. And then —
>
> *(beat)*
>
> **Boom.** A deep, double *crack* you feel in your chest. The windows rattle.
> The floor jumps.
>
> Your first thought: *did a tree just hit the house? Did something explode in the basement?*

## SCENE 2 — It's bigger than your house (~0:20)

**[VISUAL]** COMIC: the teen on the porch; neighbors point in different
directions; a distant siren as a sound-ribbon; phone filling with pinned posts.

> You go outside and see your neighbors on the street too. You're all asking: *Did a transformer blow? A boiler?*
> Someone says they heard sirens, a mile away.
>
> Then you check your social media on your phone. It's not just your street. People felt it **ten, twenty, thirty miles away** — in every direction. People who listen to firefighter and police  radios say they don't know what happened either.
>
> And that's when it stops being exciting… and starts being scary. *A gas explosion? An attack? Is anyone hurt?*

## SCENE 3 — The clue hidden in what *didn't* happen (~0:45)

**[VISUAL]** COMIC: a map of felt-pins everywhere, a magnifier finds **no** fire,
**no** rubble. A lightbulb.

> But minutes pass. And something doesn't add up. With *that* many people shaken,
> across *that* huge an area — **nobody reports any real damage.** No fire. No
> rubble. No injuries.
>
> A blast that big, but that gentle on the ground, can only mean one thing.
> Whatever exploded didn't go off *near* anyone. It went off **high above everyone.**

## SCENE 4 — It came from space (~1:10)

**[VISUAL]** COMIC: clouds part to reveal a streaking fireball; title slams in:
**"A METEOR."**

> The sky exploded. A chunk of rock from space — a **meteor** — slammed into the
> atmosphere and blew apart, miles up.
>
> And once the fear fades, a better feeling takes over. **Curiosity.** *Where exactly did the meteor explode? And how big was the explosion?*
>
> And you realize: you can actually try to *answer* those questions yourself.

## SCENE 5 — Not magic: public data + code (~1:35)

**[VISUAL]** MANIM (`the_work.py`): a stylized code window types a few Python
lines; arrows pull data from labeled databases (USGS quakes, GOES satellite,
seismic network, fireball reports) into a table, then into little maps/charts.

> You start with **public data**, and a little bit of **code.**
>
> Earthquake sensors, weather satellites, people's reports get posted online, for free by governments and universities. So you write a small program that reaches out to those databases, downloads the raw numbers, and cleans them up.
>
> Now you can start **asking questions from the data.**

## SCENE 6 — Seen 400 miles away, but not here

**[VISUAL]** MANIM (`sightings_map.py`): NE-US map; a ~400 mi ring; sighting dots
pop across 9 states + 2 provinces; Baltimore on the ring edge; a cloud over MA.

> The first question you ask is: **where did the meteor explode?** 

> The American Meteor Society collects data on big meteor fireball sightings.  
> In Baltimore, people watched a fireball **brighter than the full Moon** in broad daylight. Reports came in from **nine states, and two Canadian provinces.** Some folks
> even caught it on their dashcams.
>
> But here, in eastern Massachusetts — right underneath it? **Clouds.** We
> *heard* the sky explode… but we couldn't *see* a thing. The people who could
> see it were the ones far enough away to look *over* the clouds.

> You get a clue from these reports that  the meteor was probably over northeastern Massachusetts when it was seen. But you can do better.

## SCENE 7 — Light is fast, sound is slow

**[VISUAL]** MANIM (`flash_to_boom.py`): flash at 2:06; slow expanding sound ring +
ticking clock; reaches a town at ~2:11 → BOOM.

> The visual reports of the fireball cluster around **2:06 PM Eastern time.** But many people *heard*
> the boom around **2:11** — five minutes later.

> That's not a mistake. Light travels at about 186,000 miles per second -  effectively instantaneous to our senses. But **sound is slow**.  It takes seconds or minutes to cover distances we  see in everyday life. That's why you see lightning before you hear the thunder.

> And that delay is secretly a *ruler.* It tells you how far away the blast really was.

## SCENE 8 — Finding it with sound

[VISUAL] MANIM (triangulation.py): ripples reach sensors at different times;
circles triangulate back to a glowing X over NE MA / SE NH.

> And if we know the delay for a few different spots where the blast was heard, we can use that ruler to find the source.

> It turns out that there's an entire network of earthquake detecting microphones around the country.  Many are run by amateurs in their own backyards. And many of them picked up our meteor boom!

> Crucially, these listening stations record not only the sound but also the time the sound occured. The boom reaches different sensors at slightly different moments. Line up those arrival times, and you can trace the sound backward to its source.

> Our program reads through the sound data and does the math. And we get an answer: 
> the blast happened high over northeastern Massachusetts or southeastern New Hampshire.

## SCENE 9 — How big? The boom is a scale (~4:15)

**[VISUAL]** MANIM (`tnt_meter.py`, **redesigned**): a boom waveform draws in; we
highlight one slow ~2-second oscillation ("the note"); a dial/scale swings to
**≈ a couple hundred tons of TNT**; then an analogy panel — a cluster of
**lightning bolts** all flash at once. *(No light-vs-sound gauges. No double-boom.)*

> So — how big was it? The boom *itself* tells you.
>
> The very same backyard sensors that pinned down the source also recorded the
> exact *shape* of the pressure wave. And the **pitch** of a blast works like a
> scale. A small bang cracks with a high, sharp snap. A giant one rumbles with a
> deep, slow note.
>
> Our boom rang the air with a low, **two-second** note — far too deep for a
> quarry blast, or a passing truck. Put those sound measurements through the
> physics, and they point to an explosion of about **a couple hundred tons of
> TNT.**
>
> One way to feel that: picture a few hundred **lightning bolts** — all striking in the very same instant. That's the punch the sky packed, miles above your head… which is exactly why it rattled half of New England.

## SCENE 10 — A puzzle in the data

**[VISUAL]** MANIM `southern_mystery.py`, delivered as **4 narration-synced
beats** so each panel stays locked to its line (a panel can't get ahead of the
voice):

- **10a** `MysteryWhy` — felt-dots cluster south, sparse north, a big "?".
- **10b** `MysteryPopulation` — matched pair Manchester NH = 0 vs Lowell MA = 8
(same size/distance) → "not just population".
- **10c-1** `MysteryWindsTheory` — the wind-lens "theory" + "pulling the real
wind data."
- **10c-2** `MysteryWindsWrong` — the real winds blow sideways → the theory gets
a red ✗ "WRONG." *(No "how science moves" coda — Scene 11 closes that.)*

> But the data had a puzzle hiding in it. **Almost everyone** who reported feeling
> the boom was **south** of the blast. Hardly anyone to the north. *Why?*
>
> Our first guess was simple: maybe more people just *live* to the south. Fair
> enough — so we checked. We lined up towns of the **same size,** the **same
> distance** away. Manchester, New Hampshire, to the north: **zero** reports.
> Lowell, Massachusetts, to the south: **eight.** Same size. Same distance. So it
> wasn't *only* about population — the boom really *was* louder to the south.
>
> Next guess: maybe high-altitude **winds** bent the sound southward, like a
> lens. A neat theory. So we pulled the **actual wind data** for that day…
>
> *(beat)*
>
> And the winds were blowing the **wrong way.** Our theory was **wrong.**

## SCENE 11 — Your turn (~5:05)

**[VISUAL]** COMIC + FIGURE: the teen at a laptop, our real maps/charts on screen.
End card: **"The data is public. What will you ask?"** + links.

> But being wrong isn't failing.
> It's how we know there is more to learn. There's a real, **open question** here. One that
> *you* could help answer.
> Ready to get started?

---

### Notes for production

- Keep panels **stylized and obviously illustrated** — no fake "news footage."
- The emotional hook for this audience: **"our theory was wrong — that's science"**
(Scene 10). Give it room. (We dropped the earlier "you are the data" beat; the
sensor-network story carries Scene 8 now.)
- Scenes 5 and 10 are the "how the work really happens" beats — process over
results.
- Slower delivery (~0.9) + the added pauses are deliberate; don't rush the cut.

