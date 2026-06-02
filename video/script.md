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
> Your first thought: *did a tree just hit the house?*

## SCENE 2 — It's bigger than your house

**[VISUAL]** COMIC: the teen on the porch; neighbors point in different
directions; a distant siren as a sound-ribbon; phone filling with pinned posts.

> You go outside and see your neighbors on the street too. You're all asking: "did you feel it?"  Someone says they heard sirens, a mile away.
>
> You check social media. It's not just your street. People are talking about a boom in towns that are **miles and miles away**.
>
> This is getting scary. *Did something big just blow up? Are people hurt?*

## SCENE 3 — The clue hidden in what *didn't* happen

**[VISUAL]** COMIC: a map of felt-pins everywhere, a magnifier finds **no** fire,
**no** rubble. A lightbulb.

> But as minutes pass,  something doesn't add up. With *that* many people shaken,  
> across *that* huge an area — **somebody** should be reporting from near the source. Seeing real damage.
> 
> But so far...nothing.

## SCENE 4 — It came from space

**[VISUAL]** COMIC: teen looking up at clouds. Pan above the clouds to reveal a streaking fireball
**"A METEOR."**

> A new hypothesis enters your head. And the fear begins to fade.
>
> Could it have been... **a meteor**? Exploding high up in the sky unseen?
> 
> And now a new feeling takes over: **Curiosity.** *Where exactly did the meteor explode? And how big was the explosion?*
>
> And you realize: you can actually try to *answer* those questions yourself.

## SCENE 5 — Not magic: public data + code

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
<Possible to add some 3d effect here so we can illustrate people seeing "over the cloud"?>

> You start with **where**.

> The American Meteor Society collects data on big meteor sightings.  
> As far south as Baltimore, people saw a fireball **brighter than the full Moon**. Reports came in from **nine states, and two Canadian provinces.**
>
> But here, in eastern Massachusetts — right underneath it? **Clouds.** We
> *heard* the sky explode… but we couldn't *see* a thing. The people who could
> see it were the ones far enough away to look *over* the clouds.

> The sightings are helpful. But what you really need is objective data.

## SCENE 7 — Light is fast, sound is slow

**[VISUAL]** MANIM (`flash_to_boom.py`): flash at 2:06; slow expanding sound ring +
ticking clock; reaches a town at ~2:11 → BOOM.

> Intriguingly, the reported sightings were at **2:06PM**. But you *heard* the boom at **2:11** — five minutes later.

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
**≈ a couple hundred tons of TNT** as we illustrate a waveform decreasing in frequency to match; then an analogy panel — a cluster of
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
(same size/distance) → "not just population". <the illustration progressively unfolds to match the narration>
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
> It's how we know there is more to learn. There's a real, open question here — one that
> *you* could help answer.
> Ready to get started?

---

### Notes for production

- Keep panels **stylized and obviously illustrated** — no fake "news footage."
- The emotional hook for this audience: **"our theory was wrong, but that's ok"**
(Scene 10). Give it room. (We dropped the earlier "you are the data" beat; the
sensor-network story carries Scene 8 now.)
- Scenes 5 and 10 are the "how the work really happens" beats — process over
results.
- Delivery now at **1.0** (natural pace); the added pauses still carry the beats.

