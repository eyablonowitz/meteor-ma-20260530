"""Science shot: how big? The boom itself is a scale.

The PITCH of a blast encodes its energy: a small bang snaps high and sharp; a
giant one rumbles with a deep, slow note. Our infrasound sensors recorded a low,
~2-second note -> running that pitch through the physics points to a couple
hundred tons of TNT. To feel that: ~a few hundred lightning bolts, all at once.

(Acoustic-only: no light-vs-sound comparison, no double-boom. See storyboard.)

Render:  manim -qm video/manim/tnt_meter.py TntMeter
"""
from manim import *
import numpy as np
import math

NAVY = "#0d1b2a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
RED = "#e71d36"
MUTED = "#8d99ae"
BOLT = "#ffd60a"

FULL = 300.0          # gauge full-scale (tons of TNT)
ANSWER = 200.0        # "a couple hundred tons"


def pop(txt, color=CREAM, size=0.7, stroke=0.0):
    return Text(txt, color=color, weight=BOLD,
                stroke_color="#000000", stroke_width=stroke).scale(size)


def small_bang(x):
    """A small explosion: high-pitch, short, sharp."""
    env = math.exp(-(x / 1.1) ** 2)
    return 0.55 * env * math.cos(x * 9.0)


def big_blast(x):
    """A big explosion: low-pitch, long, slow."""
    env = math.exp(-(x / 2.3) ** 2)
    return 0.95 * env * math.cos(x * 2.1)


def boom_wave(x):
    """Our recorded boom: a low, slow ~2-second note (period ~2.4 screen units)."""
    env = math.exp(-(x / 3.0) ** 2)
    return 1.0 * env * math.cos(2 * PI * x / 2.4)


def bolt(center, s=1.0, color=BOLT):
    pts = np.array([
        [0.05, 1.0, 0], [-0.32, 0.18, 0], [0.08, 0.12, 0],
        [-0.28, -0.5, 0], [0.26, -0.55, 0], [-0.06, -1.05, 0],
    ]) * s
    m = VMobject(stroke_color=color, stroke_width=max(2.5, 5 * s))
    m.set_points_as_corners(list(pts))
    m.move_to(center)
    return m


class TntMeter(Scene):
    def construct(self):
        self.camera.background_color = NAVY

        sub0 = pop("The boom itself tells you.", MUTED, 0.5).to_edge(UP, buff=0.45)
        self.play(FadeIn(sub0))
        self.wait(3.2)
        self.play(FadeOut(sub0))

        # ---- Panel 1: pitch is a scale (small=high snap vs giant=low rumble) ----
        small = FunctionGraph(small_bang, x_range=[-2.0, 2.0, 0.01],
                              color=MUTED).set_stroke(width=4).move_to([-1.6, 1.4, 0])
        small_lbl = pop("small bang\nhigh, sharp snap", MUTED, 0.4).move_to(
            [3.0, 1.4, 0])
        big = FunctionGraph(big_blast, x_range=[-3.0, 3.0, 0.01],
                            color=TEAL).set_stroke(width=5).move_to([-1.6, -1.0, 0])
        big_lbl = pop("giant blast\ndeep, slow rumble", TEAL, 0.42).move_to(
            [3.0, -1.0, 0])

        self.play(Create(small), run_time=1.4)
        self.play(FadeIn(small_lbl, shift=RIGHT * 0.2))
        self.wait(3.0)
        self.play(Create(big), run_time=2.4)
        self.play(FadeIn(big_lbl, shift=RIGHT * 0.2))
        self.wait(1.6)

        rule = pop("lower the note  \u2192  bigger the blast", CREAM, 0.5).to_edge(
            DOWN, buff=0.5)
        arrow = Arrow([-3.0, 0.9, 0], [-3.0, -0.5, 0], color=CREAM,
                      stroke_width=4, buff=0.1)
        self.play(GrowArrow(arrow), FadeIn(rule))
        self.wait(4.5)

        self.play(*[FadeOut(m) for m in
                    (small, small_lbl, big, big_lbl, arrow, rule)])

        # ---- Panel 2: our recorded boom + the ~2-second note ----
        sub = pop("What the sensors recorded:", CREAM, 0.46).to_edge(
            UP, buff=0.45).to_edge(LEFT, buff=0.7)
        base = Line([-5.0, 0.4, 0], [5.0, 0.4, 0], color=MUTED, stroke_width=2)
        wave = FunctionGraph(boom_wave, x_range=[-4.6, 4.6, 0.005],
                             color=ORANGE).set_stroke(width=5).shift(UP * 0.4)
        self.play(FadeIn(sub), Create(base))
        self.play(Create(wave), run_time=2.6)

        # mark one full cycle (~2 s) centered on the waveform
        cyc = DoubleArrow([-1.2, -0.9, 0], [1.2, -0.9, 0], color=CREAM,
                          stroke_width=3, buff=0.05, tip_length=0.18)
        cyc_lbl = pop("one slow cycle \u2248 2 seconds", CREAM, 0.42).next_to(
            cyc, DOWN, buff=0.12)
        self.play(GrowFromCenter(cyc), FadeIn(cyc_lbl))
        self.wait(3.8)
        self.play(*[FadeOut(m) for m in (sub, base, wave, cyc, cyc_lbl)])

        # ---- Panel 3: gauge swings to ~ a couple hundred tons of TNT ----
        C = np.array([0.0, -1.4, 0])
        R = 2.7

        def at(theta, r):
            return C + r * np.array([math.cos(theta), math.sin(theta), 0])

        arc = Arc(radius=R, start_angle=PI, angle=-PI, arc_center=C,
                  color=MUTED, stroke_width=4)
        ticks = VGroup()
        for t in [0, 100, 200, 300]:
            th = PI * (1 - t / FULL)
            ticks.add(Line(at(th, R - 0.18), at(th, R), color=MUTED, stroke_width=3))
            ticks.add(pop(f"{t}", MUTED, 0.36).move_to(at(th, R + 0.32)))
        unit = pop("tons of TNT", MUTED, 0.4).move_to(C + np.array([0, -0.55, 0]))
        hub = Dot(C, radius=0.08, color=CREAM)
        self.play(Create(arc), LaggedStart(*[FadeIn(m) for m in ticks],
                                           lag_ratio=0.06), FadeIn(unit), FadeIn(hub),
                  run_time=1.6)

        tons = ValueTracker(0.0)

        def needle():
            th = PI * (1 - tons.get_value() / FULL)
            return Line(C, at(th, R - 0.35), color=ORANGE, stroke_width=7)
        ndl = always_redraw(needle)

        def readout():
            return pop(f"\u2248 {int(round(tons.get_value()))} t", ORANGE,
                       0.6).move_to(C + np.array([0, 1.05, 0]))
        rd = always_redraw(readout)
        self.add(ndl, rd)
        self.play(tons.animate.set_value(ANSWER), run_time=4.0,
                  rate_func=rate_functions.ease_out_cubic)
        self.play(Indicate(ndl, scale_factor=1.05, color=ORANGE), run_time=0.6)

        ans = pop("a couple hundred tons of TNT", CREAM, 0.56).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(ans, scale=1.1))
        self.wait(3.8)
        self.play(*[FadeOut(m) for m in (arc, ticks, unit, hub, ndl, rd, ans)])

        # ---- Panel 4: feel it -> a few hundred lightning bolts, all at once ----
        positions = [(-5.0, 1.5, 0.6), (-3.9, 2.1, 0.5), (-2.7, 1.3, 0.72),
                     (-1.5, 2.1, 0.55), (-0.3, 1.5, 0.78), (0.9, 2.15, 0.5),
                     (2.1, 1.35, 0.66), (3.3, 2.1, 0.55), (4.6, 1.5, 0.6),
                     (-4.4, 0.45, 0.5), (-1.0, 0.35, 0.52), (1.4, 0.4, 0.55),
                     (3.8, 0.4, 0.5)]
        bolts = VGroup(*[bolt(np.array([x, y, 0]), s) for (x, y, s) in positions])
        self.play(FadeIn(bolts, scale=1.3), run_time=0.5)
        self.play(Flash(np.array([0, 1.2, 0]), color=BOLT, flash_radius=5.2,
                        line_length=0.7, num_lines=28), run_time=0.8)
        lbl = pop("\u2248 a few hundred lightning bolts \u2014 all at once", BOLT,
                  0.5).move_to([0, -0.7, 0])
        self.play(FadeIn(lbl))
        self.play(LaggedStart(*[Indicate(b, color=CREAM, scale_factor=1.15)
                                for b in bolts], lag_ratio=0.04), run_time=1.2)
        self.wait(1.6)
        self.play(LaggedStart(*[Indicate(b, color=CREAM, scale_factor=1.12)
                                for b in bolts], lag_ratio=0.03), run_time=1.0)
        self.wait(0.8)

        tag = pop("Miles overhead \u2014 which is why it rattled New England.",
                  CREAM, 0.5).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(tag))
        self.wait(3.5)
