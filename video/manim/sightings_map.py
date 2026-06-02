"""Science shot: seen ~400 miles away, but not from under the clouds.

Stylized NE-US map. The fireball's path streaks over NE Massachusetts; a
~400-mile ring grows; sighting dots pop across 9 states + 2 Canadian provinces
(Baltimore sits near the ring edge). Then a cloud slides over Massachusetts:
we heard it, we couldn't see it.

Geography is a simple equirectangular projection centered on the source, scaled
so the ~400 mi (644 km) ring fits the frame.

Beats are paced to the narration: each beat is held until the matching phrase is
spoken in scene6.mp3 (see _sync.cue), so the cloud lands on "But here, in
eastern Massachusetts..." rather than drifting.

Render:  manim -qm video/manim/sightings_map.py SightingsMap
"""
from manim import *
import numpy as np
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _sync import cue, vo_duration

NAVY = "#0d1b2a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
RED = "#e71d36"
MUTED = "#8d99ae"
CLOUD = "#cfd6e1"

LAT0, LON0 = 42.91, -71.04          # acoustic source (NE MA)
KM_PER_DEG = 111.0
SCALE = 0.00497                      # manim units per km (-> 644 km ring ~ 3.2 u)


def project(lat, lon):
    x = (lon - LON0) * KM_PER_DEG * math.cos(math.radians(LAT0)) * SCALE
    y = (lat - LAT0) * KM_PER_DEG * SCALE
    return np.array([x, y, 0.0])


def pop(txt, color=CREAM, size=0.7, stroke=0.0):
    return Text(txt, color=color, weight=BOLD,
                stroke_color="#000000", stroke_width=stroke).scale(size)


def cloud(scale=1.0):
    blobs = VGroup(
        Circle(0.55), Circle(0.7), Circle(0.6), Circle(0.45), Circle(0.5))
    pos = [(-0.7, 0, 0), (0, 0.12, 0), (0.7, 0, 0), (-0.35, 0.32, 0),
           (0.35, 0.3, 0)]
    for c, p in zip(blobs, pos):
        c.set_fill(CLOUD, 1).set_stroke(width=0).move_to(p)
    eye_l = Dot([-0.22, 0.05, 0], radius=0.06, color=NAVY)
    eye_r = Dot([0.22, 0.05, 0], radius=0.06, color=NAVY)
    frown = Arc(radius=0.28, start_angle=PI * 0.15, angle=PI * 0.7,
                color=NAVY, stroke_width=4).move_to([0, -0.18, 0])
    return VGroup(blobs, eye_l, eye_r, frown).scale(scale)


class SightingsMap(Scene):
    # --- tiny scheduler: track elapsed time and hold beats to narration cues ---
    def _play(self, *a, run_time=1.0, **k):
        self.play(*a, run_time=run_time, **k)
        self._t += run_time

    def _wait(self, dt):
        if dt and dt > 0.04:
            self.wait(dt)
            self._t += dt

    def _hold_until(self, t):
        if t is not None:
            self._wait(t - self._t)

    def _fill(self, target, minimum=1.0):
        if target is None:
            return minimum
        return max(minimum, target - self._t)

    def construct(self):
        self.camera.background_color = NAVY
        self._t = 0.0

        C = {
            "ams": cue("scene6", "The American Meteor Society", lead=0.15),
            "balt": cue("scene6", "In Baltimore", lead=0.15),
            "tally": cue("scene6", "Reports came in from nine states", lead=0.15),
            "cloud": cue("scene6", "But here, in eastern Massachusetts", lead=0.2),
            "over": cue("scene6", "The people who could see it", lead=0.2),
            "clue": cue("scene6", "You get a clue", lead=0.2),
        }
        END = vo_duration("scene6")

        # --- beat 1: orientation + source + path + ring ("where did it explode?") ---
        ocean = pop("Atlantic\nOcean", MUTED, 0.4).move_to([4.7, -1.2, 0])
        coast = DashedVMobject(Line([2.3, 3.0, 0], [3.6, -3.2, 0], color=MUTED,
                                    stroke_width=3))
        self._play(FadeIn(ocean), Create(coast), run_time=0.7)

        S = project(LAT0, LON0)
        src = Star(n=8, outer_radius=0.26, color=ORANGE, fill_opacity=1,
                   stroke_color=CREAM, stroke_width=2).move_to(S)
        src_lbl = pop("NE Massachusetts", ORANGE, 0.4).next_to(src, RIGHT, buff=0.15)
        self._play(GrowFromCenter(src), FadeIn(src_lbl), run_time=0.8)

        path = Arrow(project(44.4, -70.7), project(41.7, -71.6), color=ORANGE,
                     buff=0, stroke_width=6, max_tip_length_to_length_ratio=0.18)
        path_lbl = pop("fireball path\n(approx.)", ORANGE, 0.34).next_to(
            path.get_start(), UP, buff=0.1)
        self._play(GrowArrow(path), FadeIn(path_lbl), run_time=0.8)

        ring = Circle(radius=644.0 * SCALE, color=TEAL, stroke_width=4).move_to(S)
        ring.set_stroke(opacity=0.8)
        ring_lbl = pop("~400 miles", TEAL, 0.42).move_to(
            S + DOWN * (644 * SCALE + 0.05))
        self._play(GrowFromCenter(ring), FadeIn(ring_lbl), run_time=1.4)

        # --- beat 2: sighting dots (AMS fireball reports) ---
        self._hold_until(C["ams"])
        sights = [
            ("MD", 39.29, -76.61, True, DOWN),   # Baltimore (headline)
            ("NY", 40.71, -74.01, False, UP),
            ("NJ", 40.74, -74.17, False, DOWN),
            ("PA", 39.95, -75.16, False, LEFT),
            ("DE", 39.74, -75.55, False, DOWN),
            ("CT", 41.76, -72.67, False, RIGHT),
            ("VT", 44.48, -73.21, False, LEFT),
            ("ME", 43.66, -70.26, False, RIGHT),
            ("NH", 43.21, -71.54, False, UP),
            ("QC", 45.50, -73.57, False, UP),    # Montreal
            ("ON", 45.42, -75.70, False, UP),    # Ottawa
        ]
        dots, anims = {}, []
        for ab, lat, lon, _, ldir in sights:
            p = project(lat, lon)
            d = Dot(p, radius=0.10, color=TEAL)
            l = pop(ab, CREAM, 0.32).next_to(d, ldir, buff=0.05)
            dots[ab] = VGroup(d, l)
            anims.append(GrowFromCenter(dots[ab]))
        self._play(LaggedStart(*anims, lag_ratio=0.16),
                   run_time=min(7.0, max(3.5, self._fill(C["balt"]) - 0.5)))
        self._hold_until(C["balt"])

        # --- beat 3: Baltimore near the ring edge (no moon icon) ---
        bmore = dots["MD"][0]
        callout = pop("Baltimore, MD\n~400 mi \u2014 brighter than\n"
                      "the full Moon (in daylight!)", ORANGE, 0.38)
        panel = RoundedRectangle(corner_radius=0.12, width=callout.width + 0.4,
                                 height=callout.height + 0.3, fill_color=NAVY,
                                 fill_opacity=0.92, stroke_color=ORANGE,
                                 stroke_width=2)
        box = VGroup(panel, callout).next_to(bmore, LEFT, buff=0.25)
        self._play(bmore.animate.set_color(ORANGE).scale(1.5),
                   Flash(bmore, color=ORANGE), FadeIn(box, shift=RIGHT * 0.2),
                   run_time=1.0)

        # --- beat 4: 9 states + 2 provinces (+ dashcams) ---
        self._hold_until(C["tally"])
        tally = pop("9 states  \u2022  2 Canadian provinces  \u2022  "
                    "some caught on dashcam", TEAL, 0.4).to_edge(DOWN, buff=0.35)
        self._play(FadeIn(tally), run_time=0.6)
        self._play(LaggedStart(*[Indicate(dots[ab][0], color=ORANGE,
                                          scale_factor=1.5) for ab in dots],
                               lag_ratio=0.06),
                   run_time=min(6.0, max(2.0, self._fill(C["cloud"]) - 0.6)))
        self._hold_until(C["cloud"])

        # --- beat 5: but right here -> clouds (KEY beat, locked to the line) ---
        cl = cloud(1.05).move_to(S)
        cl_lbl = pop("right underneath: clouds \u2014\nwe heard it, couldn't see it",
                     CLOUD, 0.4).next_to(cl, RIGHT, buff=0.3).shift(DOWN * 0.2)
        self._play(FadeOut(src_lbl), FadeOut(path), FadeOut(path_lbl),
                   FadeOut(tally), FadeOut(box),
                   src.animate.set_opacity(0.25), run_time=0.6)
        self._play(FadeIn(cl, shift=DOWN * 0.3), FadeIn(cl_lbl), run_time=0.8)

        # --- beat 6: the ones far enough away saw OVER the clouds ---
        self._hold_until(C["over"])
        over = pop("far enough away? you could see OVER the clouds",
                   CREAM, 0.4).to_edge(DOWN, buff=0.5)
        self._play(FadeIn(over), run_time=0.6)

        # --- beat 7: the clue ---
        self._hold_until(C["clue"])
        clue = pop("clue: the meteor was over NE Massachusetts \u2014 "
                   "but we can do better", ORANGE, 0.4).to_edge(DOWN, buff=0.5)
        self._play(FadeOut(over), FadeIn(clue), run_time=0.6)
        self._hold_until(END)
        self.wait(0.3)
