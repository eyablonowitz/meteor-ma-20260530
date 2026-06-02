"""Science shot: the puzzle in the data (split into narration-synced beats).

Standalone scenes so each panel stays locked to its own narration slice (a panel
can't get ahead of the voice):

  MysteryWhy         -> scene10a : felt reports cluster SOUTH, sparse north -> why?
  MysteryPopulation  -> scene10b : matched pair Manchester NH=0 vs Lowell MA=8
  MysteryWindsTheory -> scene10c1: wind-lens theory + pulling the real wind data
  MysteryWindsWrong  -> scene10c2: real winds blow sideways -> theory WRONG

The winds beat is split in two so the red "WRONG" can't appear while the narrator
is still introducing the theory.

Render:
  manim -qm video/manim/southern_mystery.py MysteryWhy
  manim -qm video/manim/southern_mystery.py MysteryPopulation
  manim -qm video/manim/southern_mystery.py MysteryWindsTheory
  manim -qm video/manim/southern_mystery.py MysteryWindsWrong
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


def star(pos, r=0.28):
    return Star(n=8, outer_radius=r, color=RED, fill_opacity=1,
                stroke_color=CREAM, stroke_width=2).move_to(pos)


def house(color, s=0.32):
    body = Square(side_length=s, fill_color=color, fill_opacity=1,
                  stroke_color=CREAM, stroke_width=2)
    roof = Triangle(fill_color=color, fill_opacity=1, stroke_color=CREAM,
                    stroke_width=2).scale(s * 0.8).next_to(body, UP, buff=-0.02)
    return VGroup(body, roof)


# --- shared geometry for the two winds sub-clips (identical -> seamless cut) ---
def theory_panel():
    t_head = pop("OUR THEORY", CREAM, 0.42).move_to([-3.4, 2.3, 0])
    t_src = star([-3.4, 1.3, 0], r=0.2)
    rays = VGroup(
        CurvedArrow([-3.4, 1.1, 0], [-4.7, -1.6, 0], color=TEAL, angle=-0.9),
        CurvedArrow([-3.4, 1.1, 0], [-3.4, -1.9, 0], color=TEAL, angle=-0.6),
        CurvedArrow([-3.4, 1.1, 0], [-2.1, -1.6, 0], color=TEAL, angle=-0.3),
    )
    t_lbl = pop("winds bend the boom\nsouth, like a lens", TEAL, 0.34).move_to(
        [-3.4, -2.4, 0])
    return t_head, t_src, rays, t_lbl


def reality_winds():
    wind = VGroup(
        Arrow([2.0, 1.2, 0], [4.8, 1.2, 0], color=ORANGE, buff=0, stroke_width=5),
        Arrow([4.8, 0.3, 0], [2.0, 0.3, 0], color=ORANGE, buff=0, stroke_width=5),
        Arrow([2.0, -0.6, 0], [4.8, -0.6, 0], color=ORANGE, buff=0, stroke_width=5),
    )
    r_lbl = pop("blowing sideways \u2014\nnot south", ORANGE, 0.34).move_to(
        [3.4, -2.4, 0])
    return wind, r_lbl


def divider_line():
    return DashedLine([0, 2.6, 0], [0, -2.9, 0], color=MUTED, stroke_width=2)


class MysteryWhy(Scene):
    """scene10a -- the asymmetry + the question."""

    def construct(self):
        self.camera.background_color = NAVY

        src = star([0, 2.4, 0])
        src_lbl = pop("the blast", RED, 0.36).next_to(src, RIGHT, buff=0.15)

        south = [(-4.0, -2.5), (-3.1, -1.1), (-2.3, -2.5), (-1.5, -0.5),
                 (-0.8, -1.9), (0.1, -0.3), (0.4, -2.3), (1.1, -1.1),
                 (1.9, -2.6), (2.5, -1.3), (3.3, -0.4), (3.7, -2.0),
                 (-3.6, 0.3), (2.1, 0.5), (-1.1, 1.1), (1.3, 1.3)]
        north = [(-0.6, 3.0), (0.7, 3.05)]
        south_dots = VGroup(*[Dot([x, y, 0], radius=0.11, color=TEAL)
                              for x, y in south])
        north_dots = VGroup(*[Dot([x, y, 0], radius=0.11, color=TEAL)
                              for x, y in north])

        self.play(GrowFromCenter(src), FadeIn(src_lbl))
        self.play(LaggedStart(*[GrowFromCenter(d) for d in south_dots],
                              lag_ratio=0.12), run_time=3.2)
        self.play(LaggedStart(*[GrowFromCenter(d) for d in north_dots],
                              lag_ratio=0.2), run_time=0.8)
        self.wait(0.5)

        q = pop("?", ORANGE, 2.2, stroke=2).move_to([4.3, 1.3, 0])
        cap = pop("almost every \u201cI felt it\u201d report came from SOUTH",
                  CREAM, 0.46).to_edge(DOWN, buff=0.4)
        self.play(FadeIn(q, scale=1.4), FadeIn(cap))
        self.wait(3.0)


class MysteryPopulation(Scene):
    """scene10b -- the matched-pair check, unfolded in step with the narration."""

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

    def construct(self):
        self.camera.background_color = NAVY
        self._t = 0.0
        C = {
            "lined": cue("scene10b", "We lined up towns", lead=0.15),
            "manch": cue("scene10b", "Manchester", lead=0.1),
            "lowell": cue("scene10b", "Lowell", lead=0.1),
            "concl": cue("scene10b", "wasn't only about population", lead=0.15),
        }
        END = vo_duration("scene10b")

        sub = pop("first guess: just more people down south?", MUTED,
                  0.42).to_edge(UP, buff=0.4)
        self._play(FadeIn(sub), run_time=0.6)

        # fill the opening (was an empty frame): the "more people south" guess --
        # a crowd of homes to the south, only a couple to the north.
        npos = [(-1.2, 2.0), (1.2, 2.05)]
        spos = [(-3.7, -1.4), (-2.5, -2.3), (-1.3, -1.4), (-0.2, -2.3),
                (1.0, -1.4), (2.2, -2.3), (3.5, -1.4), (0.7, -0.6)]
        crowd_n = VGroup(*[house(MUTED, 0.2).move_to([x, y, 0]) for x, y in npos])
        crowd_s = VGroup(*[house(TEAL, 0.2).move_to([x, y, 0]) for x, y in spos])
        self._play(LaggedStart(*[GrowFromCenter(h) for h in crowd_n],
                               lag_ratio=0.15), run_time=0.7)
        self._play(LaggedStart(*[GrowFromCenter(h) for h in crowd_s],
                               lag_ratio=0.1), run_time=1.3)

        axis = DashedLine([0, 2.7, 0], [0, -3.0, 0], color=MUTED, stroke_width=2)
        bsrc = star([0, 0.2, 0], r=0.24)
        bsrc_lbl = pop("blast", RED, 0.32).next_to(bsrc, RIGHT, buff=0.12)

        n_house = house(MUTED).move_to([0, 2.1, 0])
        n_txt = pop("Manchester, NH  (north)", CREAM, 0.36).next_to(n_house, RIGHT, buff=0.3)
        n_num = pop("0", MUTED, 1.3, stroke=1).next_to(n_house, LEFT, buff=0.4)
        n_rep = pop("reports", MUTED, 0.3).next_to(n_num, DOWN, buff=0.08)

        s_house = house(TEAL).move_to([0, -2.0, 0])
        s_txt = pop("Lowell, MA  (south)", CREAM, 0.36).next_to(s_house, RIGHT, buff=0.3)
        s_num = pop("8", ORANGE, 1.3, stroke=1).next_to(s_house, LEFT, buff=0.4)
        s_rep = pop("reports", ORANGE, 0.3).next_to(s_num, DOWN, buff=0.08)

        d_n = DoubleArrow([0.0, 0.45, 0], [0.0, 1.85, 0], color=MUTED, buff=0,
                          stroke_width=3, tip_length=0.16)
        d_n_lbl = pop("~35 km", MUTED, 0.3).next_to(d_n, RIGHT, buff=0.1)
        d_s = DoubleArrow([0.0, -0.05, 0], [0.0, -1.75, 0], color=MUTED, buff=0,
                          stroke_width=3, tip_length=0.16)
        d_s_lbl = pop("~35 km", MUTED, 0.3).next_to(d_s, RIGHT, buff=0.1)

        # "we lined up towns of the same size, the same distance away"
        self._hold_until(C["lined"])
        self._play(FadeOut(crowd_n), FadeOut(crowd_s), run_time=0.4)
        self._play(Create(axis), GrowFromCenter(bsrc), FadeIn(bsrc_lbl),
                   run_time=0.6)
        self._play(FadeIn(n_house), FadeIn(n_txt), GrowArrow(d_n),
                   FadeIn(d_n_lbl), FadeIn(s_house), FadeIn(s_txt),
                   GrowArrow(d_s), FadeIn(d_s_lbl), run_time=0.9)

        # "Manchester, New Hampshire, to the north: zero reports"
        self._hold_until(C["manch"])
        self._play(FadeIn(n_num, scale=1.3), FadeIn(n_rep), run_time=0.6)

        # "Lowell, Massachusetts, to the south: eight" -- let it land hard
        self._hold_until(C["lowell"])
        self._play(FadeIn(s_num, scale=1.4), FadeIn(s_rep), run_time=0.5)
        self._play(Flash(s_num, color=ORANGE, flash_radius=1.1, num_lines=16),
                   Indicate(s_num, color=ORANGE, scale_factor=1.25), run_time=0.6)

        # "so it wasn't only about population"
        self._hold_until(C["concl"])
        cap = pop("same size \u2022 same distance \u2192 not just population",
                  TEAL, 0.46).to_edge(DOWN, buff=0.4)
        self._play(FadeIn(cap), run_time=0.6)
        self._hold_until(END)
        self.wait(0.3)


class MysteryWindsTheory(Scene):
    """scene10c1 -- the wind-lens theory + pulling the real wind data."""

    def construct(self):
        self.camera.background_color = NAVY
        t_head, t_src, rays, t_lbl = theory_panel()
        divider = divider_line()
        r_head = pop("THE REAL WINDS", CREAM, 0.42).move_to([3.4, 2.3, 0])
        fetching = pop("pulling the actual\nwind data\u2026", MUTED, 0.4).move_to(
            [3.4, -0.1, 0])

        self.play(FadeIn(t_head), GrowFromCenter(t_src),
                  LaggedStart(*[Create(r) for r in rays], lag_ratio=0.3),
                  FadeIn(t_lbl), run_time=2.6)
        self.wait(1.4)
        self.play(Create(divider), FadeIn(r_head))
        self.play(FadeIn(fetching))
        self.wait(3.6)


class MysteryWindsWrong(Scene):
    """scene10c2 -- the real winds blow sideways: the theory is WRONG."""

    def construct(self):
        self.camera.background_color = NAVY

        # reconstruct the theory panel exactly (seamless cut from 10c1)
        t_head, t_src, rays, t_lbl = theory_panel()
        divider = divider_line()
        r_head = pop("THE REAL WINDS", CREAM, 0.42).move_to([3.4, 2.3, 0])
        fetching = pop("pulling the actual\nwind data\u2026", MUTED, 0.4).move_to(
            [3.4, -0.1, 0])
        self.add(t_head, t_src, rays, t_lbl, divider, r_head, fetching)

        # the real winds arrive (replace the "fetching" placeholder)
        wind, r_lbl = reality_winds()
        self.play(FadeOut(fetching),
                  LaggedStart(*[GrowArrow(w) for w in wind], lag_ratio=0.3),
                  FadeIn(r_lbl), run_time=2.4)
        self.wait(0.7)

        # ... so the theory is wrong.
        x_mark = VGroup(
            Line([-4.9, 2.0, 0], [-1.9, -2.0, 0], color=RED, stroke_width=12),
            Line([-1.9, 2.0, 0], [-4.9, -2.0, 0], color=RED, stroke_width=12))
        wrong = Text("WRONG", color=RED, weight=BOLD, stroke_color=CREAM,
                     stroke_width=1.2).scale(1.15).move_to(
                         [-3.4, -0.2, 0]).rotate(-PI / 12)
        self.play(Create(x_mark), FadeIn(wrong, scale=1.4))
        self.wait(2.8)
