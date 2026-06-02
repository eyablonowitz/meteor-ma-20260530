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
            "balt": cue("scene6", "Baltimore", lead=0.15),
            "tally": cue("scene6", "Reports came in from nine states", lead=0.15),
            "cloud": cue("scene6", "But here, in eastern Massachusetts", lead=0.2),
            "over": cue("scene6", "The people who could see it", lead=0.2),
            "clue": cue("scene6", "The sightings are helpful", lead=0.2),
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
                      "the full Moon", ORANGE, 0.38)
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
        tally = pop("9 states  \u2022  2 Canadian provinces", TEAL,
                    0.4).to_edge(DOWN, buff=0.35)
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

        # --- beat 6: side-view cutaway -- distant viewers saw OVER the cloud ---
        self._hold_until(C["over"])
        map_grp = VGroup(ring, ring_lbl, ocean, coast, src, cl, cl_lbl,
                         *dots.values())
        self._play(FadeOut(map_grp), run_time=0.5)

        title = pop("side view: why distance let people see it", MUTED,
                    0.4).to_edge(UP, buff=0.4)
        ground = Line([-6.2, -2.6, 0], [6.2, -2.6, 0], color=MUTED, stroke_width=3)
        band = VGroup(*[Circle(r).set_fill(CLOUD, 1).set_stroke(width=0)
                        .move_to([cx, cy, 0]) for (cx, cy, r) in
                        [(-1.5, -0.7, 0.5), (-0.8, -0.5, 0.6), (0, -0.45, 0.66),
                         (0.8, -0.5, 0.6), (1.5, -0.7, 0.5)]])
        band_lbl = pop("cloud deck over MA", MUTED, 0.32).next_to(
            band, UP, buff=0.06)
        blast = Star(n=8, outer_radius=0.3, color=ORANGE, fill_opacity=1,
                     stroke_color=CREAM, stroke_width=2).move_to([0, 2.4, 0])
        blast_lbl = pop("the fireball, miles up", ORANGE, 0.36).next_to(
            blast, UP, buff=0.08)

        # local viewer (right below) -- sightline blocked by the cloud
        v1 = Dot([0, -2.45, 0], radius=0.1, color=CREAM)
        v1_lbl = pop("right below", CREAM, 0.32).next_to(v1, DOWN, buff=0.07)
        block = DashedLine([0, -2.3, 0], [0, -1.15, 0], color=RED, stroke_width=4)
        x1 = VGroup(
            Line([-0.18, -0.98, 0], [0.18, -0.62, 0], color=RED, stroke_width=6),
            Line([-0.18, -0.62, 0], [0.18, -0.98, 0], color=RED, stroke_width=6))

        # distant viewer -- sightline clears the cloud, straight to the blast
        v2 = Dot([4.8, -2.45, 0], radius=0.1, color=CREAM)
        v2_lbl = pop("miles away", CREAM, 0.32).next_to(v2, DOWN, buff=0.07)
        sight = Line([4.8, -2.3, 0], [0.2, 2.15, 0], color=TEAL, stroke_width=4)

        over = pop("far enough away, your line of sight clears the cloud",
                   CREAM, 0.42).to_edge(DOWN, buff=0.35)
        self._play(FadeIn(title), Create(ground), FadeIn(band), FadeIn(band_lbl),
                   GrowFromCenter(blast), FadeIn(blast_lbl), run_time=0.8)
        self._play(FadeIn(v1), FadeIn(v1_lbl), Create(block), Create(x1),
                   run_time=0.7)
        self._play(FadeIn(v2), FadeIn(v2_lbl), Create(sight), FadeIn(over),
                   run_time=0.8)
        cutaway = VGroup(title, ground, band, band_lbl, blast, blast_lbl,
                         v1, v1_lbl, block, x1, v2, v2_lbl, sight)

        # --- beat 7: eyewitness lines are imprecise -> we need objective data ---
        # scattered observers all point toward MA, but their sight-lines cross in
        # a fuzzy zone, not a single point -> subjective data can't pin the source.
        self._hold_until(C["clue"])
        self._play(FadeOut(cutaway), FadeOut(over), run_time=0.5)

        ma_lbl = pop("everyone looks toward Massachusetts\u2026", MUTED,
                     0.4).to_edge(UP, buff=0.45)
        obs = [(-5.2, -1.2), (-4.3, -2.7), (-2.5, -3.0), (-0.7, -2.7),
               (1.3, -3.0), (3.1, -2.4), (4.9, -1.0), (-5.4, 0.7)]
        jit = [(-0.9, 0.5), (0.8, -0.5), (-0.5, 0.8), (0.7, 0.5),
               (-0.8, -0.4), (0.95, 0.15), (-0.6, 0.65), (0.6, -0.6)]
        tgt = np.array([0.3, 1.5, 0])
        people, rays = VGroup(), VGroup()
        for (px, py), (jx, jy) in zip(obs, jit):
            p = np.array([px, py, 0])
            people.add(Dot(p, radius=0.09, color=TEAL))
            rays.add(DashedLine(p, tgt + np.array([jx, jy, 0]), color=TEAL,
                                stroke_width=2, dash_length=0.12).set_opacity(0.6))

        fuzzy = Ellipse(width=2.3, height=1.6, color=ORANGE,
                        stroke_width=3).set_stroke(opacity=0.9).move_to(tgt)
        fuzzy_lbl = pop("they cross in a fuzzy zone \u2014\nnot a single point",
                        ORANGE, 0.36).next_to(fuzzy, RIGHT, buff=0.35)
        cap = pop("eyewitness lines don't quite meet \u2014 we need objective data",
                  CREAM, 0.42).to_edge(DOWN, buff=0.4)

        self._play(FadeIn(ma_lbl),
                   LaggedStart(*[GrowFromCenter(pp) for pp in people],
                               lag_ratio=0.08), run_time=0.8)
        self._play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.06),
                   run_time=1.1)
        self._play(Create(fuzzy), FadeIn(fuzzy_lbl), FadeIn(cap), run_time=0.7)
        self._hold_until(END)
        self.wait(0.3)
