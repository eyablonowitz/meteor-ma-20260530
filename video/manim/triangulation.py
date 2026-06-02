"""Science shot: 'reverse GPS' — locating the blast from sound arrival times.

Phase 1: a ring expands from the (unknown) source; each sensor 'hears' it at a
different time. Phase 2: knowing only those times, draw a circle around each
sensor (radius = time x speed of sound); the circles intersect at the source.

Beats are paced to the narration (scene8.mp3, via _sync.cue): the network beat,
the ring crawl, the circle-fitting, and the final answer each land on their line.

Render:  manim -qm video/manim/triangulation.py Triangulation
"""
from manim import *
import numpy as np
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


def pop(txt, color=CREAM, size=0.7, stroke=0.0):
    return Text(txt, color=color, weight=BOLD,
                stroke_color="#000000", stroke_width=stroke).scale(size)


class Triangulation(Scene):
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
        S = np.array([-1.0, 1.4, 0.0])     # true source (NE MA / SE NH)
        sensors = {
            "A": np.array([-4.7, 0.6, 0.0]),
            "B": np.array([-2.8, -2.1, 0.0]),
            "C": np.array([2.6, -1.6, 0.0]),
            "D": np.array([4.6, 1.2, 0.0]),
            "E": np.array([0.7, -2.6, 0.0]),
        }
        order = sorted(sensors, key=lambda k: np.linalg.norm(sensors[k] - S))
        dists = {k: float(np.linalg.norm(sensors[k] - S)) for k in sensors}
        maxd = max(dists.values())
        sec = {k: 18.0 * dists[k] for k in sensors}   # illustrative seconds

        C = {
            "net": cue("scene8", "It turns out that", lead=0.2),
            "back": cue("scene8", "Many are run by amateurs", lead=0.2),
            "boom": cue("scene8", "And many of them picked up", lead=0.2),
            "time": cue("scene8", "Crucially", lead=0.2),
            "reach": cue("scene8", "The boom reaches different sensors", lead=0.2),
            "lineup": cue("scene8", "Line up those arrival times", lead=0.2),
            "prog": cue("scene8", "Our program reads through", lead=0.2),
            "ans": cue("scene8", "And we get an answer", lead=0.1),
        }
        END = vo_duration("scene8")

        sensor_dots, sensor_lbls = {}, {}
        for k, p in sensors.items():
            d = Dot(p, radius=0.13, color=TEAL)
            l = pop(k, TEAL, 0.45).next_to(d, UP, buff=0.1)
            sensor_dots[k], sensor_lbls[k] = d, l
        src = Star(n=8, outer_radius=0.32, color=ORANGE, fill_opacity=1,
                   stroke_color=CREAM, stroke_width=2).move_to(S)

        # --- beat 1: intro ("use that ruler at several spots to find the source") ---
        self._play(LaggedStart(*[FadeIn(sensor_dots[k]) for k in sensors],
                               lag_ratio=0.1), GrowFromCenter(src), run_time=1.4)
        self._play(*[FadeIn(sensor_lbls[k]) for k in sensors], run_time=0.6)
        intro_lbl = pop("lots of places heard it \u2014 each delay is a ruler",
                        MUTED, 0.42).to_edge(UP, buff=0.35)
        self._play(FadeIn(intro_lbl), run_time=0.5)
        self._hold_until(C["net"])

        # --- beat 2: a nationwide network of earthquake-detecting mics ---
        net_lbl = pop("a nationwide network of earthquake-detecting microphones",
                      TEAL, 0.42).to_edge(DOWN, buff=0.4)
        self._play(FadeOut(intro_lbl), FadeIn(net_lbl), run_time=0.5)
        web = VGroup(*[
            DashedLine(sensors[order[i]], sensors[order[i + 1]], color=MUTED,
                       stroke_width=2).set_stroke(opacity=0.4)
            for i in range(len(order) - 1)])
        self._play(Create(web),
                   LaggedStart(*[Indicate(sensor_dots[k], color=TEAL,
                                          scale_factor=1.5) for k in sensors],
                               lag_ratio=0.1),
                   run_time=max(1.5, self._fill(C["back"]) - 0.4))
        self._hold_until(C["back"])

        # --- beat 3: many run by amateurs in their backyards ---
        back_lbl = pop("many in people's backyards", ORANGE, 0.44).to_edge(
            DOWN, buff=0.4)
        self._play(FadeOut(net_lbl), FadeIn(back_lbl), run_time=0.5)
        self._hold_until(C["boom"])

        # --- beat 4: ...and they caught our boom! ---
        boom_lbl = pop("\u2026 and they caught our boom!", CREAM, 0.44).to_edge(
            DOWN, buff=0.4)
        self._play(FadeOut(back_lbl), FadeIn(boom_lbl),
                   LaggedStart(*[Flash(sensor_dots[k], color=ORANGE,
                                       flash_radius=0.5) for k in sensors],
                               lag_ratio=0.1), run_time=1.2)
        self._hold_until(C["time"])

        # --- beat 5: crucially, they log the exact arrival TIME ---
        time_lbl = pop("they record the exact arrival TIME of the sound", ORANGE,
                       0.42).to_edge(DOWN, buff=0.4)
        self._play(FadeOut(boom_lbl), FadeIn(time_lbl), run_time=0.6)
        self._hold_until(C["reach"])

        # --- beat 6 (Phase 1): the ring reaches each sensor at a different time ---
        self._play(FadeOut(time_lbl), FadeOut(web), run_time=0.3)
        reach_lbl = pop("the boom reaches each sensor at a different moment",
                        MUTED, 0.42).to_edge(UP, buff=0.35)
        self._play(FadeIn(reach_lbl), run_time=0.4)

        radius = ValueTracker(0.0)
        ring = always_redraw(lambda: Circle(
            radius=max(radius.get_value(), 1e-3), color=TEAL, stroke_width=5
        ).move_to(S).set_stroke(opacity=0.85))
        self.add(ring)

        stamp_t = 0.45
        crawl_budget = max(2.0, self._fill(C["prog"]) - 0.6 - len(order) * stamp_t)
        stamps = VGroup()
        prev = 0.0
        lineup = None
        for k in order:
            rt = max(0.25, (dists[k] - prev) / maxd * crawl_budget)
            self._play(radius.animate.set_value(dists[k]), run_time=rt,
                       rate_func=linear)
            prev = dists[k]
            stamp = pop("+%ds" % round(sec[k]), CREAM, 0.4).next_to(
                sensor_dots[k], RIGHT, buff=0.12)
            self._play(Indicate(sensor_dots[k], color=CREAM, scale_factor=1.7),
                       FadeIn(stamp), run_time=stamp_t)
            stamps.add(stamp)
            if lineup is None and C["lineup"] and self._t >= C["lineup"]:
                lineup = pop("line up those arrival times\u2026", ORANGE,
                             0.44).to_edge(DOWN, buff=0.4)
                self._play(FadeIn(lineup), run_time=0.4)
        if lineup is None:
            lineup = pop("line up those arrival times\u2026", ORANGE,
                         0.44).to_edge(DOWN, buff=0.4)
            self._play(FadeIn(lineup), run_time=0.4)
        self._hold_until(C["prog"])

        # --- Phase 2: only the times are known -> work backward (the math) ---
        self._play(FadeOut(ring), FadeOut(src), FadeOut(reach_lbl),
                   FadeOut(lineup), FadeOut(stamps), run_time=0.5)
        sub2 = pop("we only know the times \u2014 so work backward", ORANGE,
                   0.45).to_edge(UP, buff=0.35)
        rad_lbl = pop("each time \u2192 a circle:  radius = arrival time \u00d7 "
                      "speed of sound", MUTED, 0.38).to_edge(DOWN, buff=0.4)
        self._play(FadeIn(sub2), FadeIn(rad_lbl), run_time=0.6)
        circles = VGroup(*[
            Circle(radius=dists[k], color=ORANGE, stroke_width=4)
            .move_to(sensors[k]).set_stroke(opacity=0.7)
            for k in sensors])
        self._play(LaggedStart(*[Create(c) for c in circles], lag_ratio=0.25),
                   run_time=max(2.4, self._fill(C["ans"]) - 0.8))
        self._hold_until(C["ans"])

        # --- the answer ---
        self._play(FadeOut(rad_lbl), run_time=0.3)
        x = VGroup(
            Line(UL, DR, color=RED, stroke_width=10),
            Line(UR, DL, color=RED, stroke_width=10),
        ).scale(0.32).move_to(S)
        found_txt = pop("Source:\nNE Massachusetts /\nSE New Hampshire", RED, 0.5)
        panel = RoundedRectangle(
            corner_radius=0.15, width=found_txt.width + 0.5,
            height=found_txt.height + 0.4, fill_color=CREAM, fill_opacity=1,
            stroke_color=RED, stroke_width=3)
        found = VGroup(panel, found_txt).move_to([2.9, -0.2, 0])
        self._play(GrowFromCenter(x), Flash(S, color=RED, flash_radius=0.6),
                   FadeOut(sub2), run_time=0.7)
        self._play(FadeIn(found, shift=UP * 0.2), run_time=0.6)
        self._hold_until(END)
        self.wait(0.3)
