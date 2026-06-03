"""Outro / credits shot (~18s, no VO -- carried by the retro-futuristic music).

A warm, optimistic "world's-fair tomorrow" end card: a soft horizon glow, a
sparse starfield with one gentle shooting star, then thanks to the people who
filed sighting / "Did You Feel It?" reports and to the open-data providers whose
instruments made the analysis possible.

Render:  manim -qm video/manim/outro.py Outro
Music:   video/assets/music/outro.mp3 (ElevenLabs Music; mixed in by rough_cut.py)
"""
from manim import *
import numpy as np

NAVY = "#0d1b2a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
MUTED = "#8d99ae"

REPO = "github.com/eyablonowitz/meteor-ma-20260530"


def txt(s, color=CREAM, size=0.7, weight=BOLD):
    return Text(s, color=color, weight=weight).scale(size)


class Outro(Scene):
    def construct(self):
        self.camera.background_color = NAVY
        rng = np.random.RandomState(7)

        # --- horizon glow: stacked soft ellipses rising from the bottom edge ---
        glow = VGroup()
        for i in range(7):
            e = Ellipse(width=18 - 1.4 * i, height=5.2 - 0.55 * i,
                        color=ORANGE, fill_opacity=0.06, stroke_width=0)
            e.move_to([0, -4.0, 0])
            glow.add(e)
        horizon = Line([-7.5, -3.0, 0], [7.5, -3.0, 0], color=ORANGE,
                       stroke_width=2).set_stroke(opacity=0.35)

        # --- sparse starfield in the upper field ---
        stars = VGroup()
        for _ in range(46):
            x = rng.uniform(-6.9, 6.9)
            y = rng.uniform(-1.6, 3.8)
            r = rng.uniform(0.012, 0.04)
            s = Dot([x, y, 0], radius=r, color=CREAM)
            s.set_opacity(rng.uniform(0.25, 0.9))
            stars.add(s)

        self.play(FadeIn(glow, shift=UP * 0.3),
                  Create(horizon),
                  LaggedStart(*[FadeIn(s, scale=0.4) for s in stars],
                              lag_ratio=0.02),
                  run_time=1.8)
        # slow life: the glow breathes upward a touch through the whole card
        glow.add_updater(lambda m, dt: m.shift(UP * dt * 0.012))

        # --- headline ---
        head = txt("Thank you.", CREAM, 1.05).move_to([0, 2.55, 0])
        self.play(FadeIn(head, shift=UP * 0.25), run_time=1.1)

        # --- one gentle shooting star, L->R, behind the text ---
        star_dot = Dot([-6.5, 3.4, 0], radius=0.05, color=CREAM)
        trail = Line([-6.5, 3.4, 0], [-6.9, 3.5, 0], color=CREAM, stroke_width=3)
        trail.set_stroke(opacity=0.0)
        shoot = VGroup(trail, star_dot).set_z_index(-1)
        self.add(shoot)
        self.play(star_dot.animate.move_to([2.0, 1.7, 0]),
                  UpdateFromFunc(trail, lambda m: m.put_start_and_end_on(
                      star_dot.get_center() + np.array([-1.0, 0.32, 0]),
                      star_dot.get_center())),
                  trail.animate.set_stroke(opacity=0.7),
                  run_time=1.2, rate_func=rate_functions.ease_in_out_sine)
        self.play(FadeOut(shoot), run_time=0.5)

        # --- the human line (the heart of it) ---
        human = VGroup(
            txt("To everyone who looked up \u2014 and filed a sighting", CREAM, 0.46),
            txt("or a \u201cDid You Feel It?\u201d report.", CREAM, 0.46),
        ).arrange(DOWN, buff=0.16).move_to([0, 1.15, 0])
        self.play(FadeIn(human, shift=UP * 0.15), run_time=1.0)
        self.wait(1.4)

        # --- data / instrument credits ---
        cred_head = txt("Built from open data shared by", ORANGE, 0.4)
        lines = VGroup(
            txt("USGS  \u00b7  American Meteor Society  \u00b7  EarthScope / IRIS",
                MUTED, 0.4, weight=NORMAL),
            txt("Weston Observatory  \u00b7  Lamont\u2013Doherty  \u00b7  "
                "the Raspberry Shake citizen network", MUTED, 0.4, weight=NORMAL),
            txt("NOAA GOES-19  \u00b7  NASA / CNEOS  \u00b7  ECMWF Copernicus",
                MUTED, 0.4, weight=NORMAL),
        ).arrange(DOWN, buff=0.22)
        credits = VGroup(cred_head, lines).arrange(DOWN, buff=0.34)
        if credits.width > 12.4:
            credits.scale_to_fit_width(12.4)
        credits.move_to([0, -1.15, 0])
        self.play(FadeIn(cred_head, shift=UP * 0.1), run_time=0.6)
        self.play(LaggedStart(*[FadeIn(l, shift=UP * 0.1) for l in lines],
                              lag_ratio=0.35), run_time=1.7)
        self.wait(2.2)

        # --- open-source sign-off ---
        repo = txt(f"Open data & code:   {REPO}", TEAL, 0.34, weight=NORMAL)
        repo.move_to([0, -3.25, 0])
        self.play(FadeIn(repo), run_time=0.7)
        self.wait(2.0)

        glow.clear_updaters()
        self.play(FadeOut(VGroup(head, human, credits, repo)),
                  FadeOut(stars), FadeOut(horizon), FadeOut(glow),
                  run_time=1.7)
