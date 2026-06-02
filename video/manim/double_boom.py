"""Science shot: one crack, or two?

A simple fly-by would make ONE smooth shock (a classic 'N-wave'). The sensors
actually recorded TWO distinct pulses -> the rock didn't just pass by, it
shattered in mid-air (an airburst).

Render:  manim -qm video/manim/double_boom.py DoubleBoom
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

XR = [-4.6, 4.6]


def pop(txt, color=CREAM, size=0.7, stroke=0.0):
    return Text(txt, color=color, weight=BOLD,
                stroke_color="#000000", stroke_width=stroke).scale(size)


def nwave(x):
    """Classic sonic-boom N-wave centered at 0."""
    A, w = 0.85, 0.6
    if -w <= x <= w:
        return -A * x / w
    return 0.0


def double(x):
    """Two decaying oscillation packets."""
    def packet(c):
        env = math.exp(-((x - c) ** 2) / (2 * 0.22 ** 2))
        return env * math.cos((x - c) * 13)
    return 0.85 * (packet(-1.3) + packet(1.2))


class DoubleBoom(Scene):
    def construct(self):
        self.camera.background_color = NAVY

        title = pop("One crack\u2026 or two?", CREAM, 0.66).to_edge(UP)
        self.play(FadeIn(title))

        top_y, bot_y = 1.25, -1.7
        base_top = Line([XR[0], top_y, 0], [XR[1], top_y, 0], color=MUTED,
                        stroke_width=2)
        base_bot = Line([XR[0], bot_y, 0], [XR[1], bot_y, 0], color=MUTED,
                        stroke_width=2)

        top_lbl = pop("If it just FLEW PAST:", MUTED, 0.42).next_to(
            base_top, UP, buff=0.15).to_edge(LEFT, buff=0.6)
        bot_lbl = pop("What the sensors recorded:", CREAM, 0.42).next_to(
            base_bot, UP, buff=0.15).to_edge(LEFT, buff=0.6)

        # top: single smooth N-wave
        nw = FunctionGraph(nwave, x_range=[XR[0], XR[1], 0.01], color=MUTED).shift(UP * top_y)
        nw.set_stroke(width=5)
        nw_tag = pop("one smooth crack\n(a sonic boom)", MUTED, 0.4).move_to([3.4, top_y - 0.05, 0])

        self.play(Create(base_top), FadeIn(top_lbl))
        self.play(Create(nw), run_time=1.8)
        self.play(FadeIn(nw_tag))
        self.wait(1.2)

        # bottom: two pulses
        db = FunctionGraph(double, x_range=[XR[0], XR[1], 0.005], color=ORANGE).shift(UP * bot_y)
        db.set_stroke(width=5)
        self.play(Create(base_bot), FadeIn(bot_lbl))
        self.play(Create(db), run_time=1.4)

        # mark the two pulses
        p1 = pop("BOOM", ORANGE, 0.5, stroke=1).move_to([-1.3, bot_y + 1.25, 0])
        p2 = pop("BOOM", ORANGE, 0.5, stroke=1).move_to([1.2, bot_y + 1.25, 0])
        gap = DoubleArrow([-1.3, bot_y - 0.95, 0], [1.2, bot_y - 0.95, 0],
                          color=CREAM, stroke_width=3, buff=0.05,
                          tip_length=0.18)
        gap_lbl = pop("two pulses = it broke apart", CREAM, 0.4).next_to(
            gap, DOWN, buff=0.1)
        self.play(FadeIn(p1, shift=DOWN * 0.2), FadeIn(p2, shift=DOWN * 0.2))
        self.play(GrowFromCenter(gap), FadeIn(gap_lbl))
        self.wait(0.4)

        tag = pop("It didn't fly by \u2014 it SHATTERED.   (an airburst)", ORANGE,
                  0.55, stroke=1).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(tag, scale=1.1))
        self.wait(2.5)
