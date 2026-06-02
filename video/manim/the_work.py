"""Science shot: not magic -- just public data + code.

A stylized code window pulls raw data from public databases (USGS quakes, GOES
satellite, a seismic network, fireball reports) into a table, then into little
maps/charts. The point: the work is reach-out-and-grab-public-data + code.

Render:  manim -qm video/manim/the_work.py TheWork
"""
from manim import *
import numpy as np

NAVY = "#0d1b2a"
PANEL = "#10243a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
RED = "#e71d36"
MUTED = "#8d99ae"
MONO = "Menlo"


def pop(txt, color=CREAM, size=0.7, stroke=0.0, font=None):
    kw = {"weight": BOLD, "stroke_color": "#000000", "stroke_width": stroke}
    if font:
        kw["font"] = font
    return Text(txt, color=color, **kw).scale(size)


def chip(label, color):
    box = RoundedRectangle(corner_radius=0.1, width=2.2, height=0.95,
                           fill_color=PANEL, fill_opacity=1, stroke_color=color,
                           stroke_width=2.5)
    txt = pop(label, color, 0.34).move_to(box)
    return VGroup(box, txt)


class TheWork(Scene):
    def construct(self):
        self.camera.background_color = NAVY

        # --- code window (left) ---
        win = RoundedRectangle(corner_radius=0.12, width=5.0, height=3.1,
                               fill_color=PANEL, fill_opacity=1,
                               stroke_color=MUTED, stroke_width=2)
        win.move_to([-4.0, -0.2, 0])
        bar = RoundedRectangle(corner_radius=0.12, width=5.0, height=0.5,
                               fill_color="#1c3a57", fill_opacity=1,
                               stroke_width=0).move_to(win.get_top() + DOWN * 0.25)
        dots = VGroup(*[Dot(radius=0.06, color=c) for c in (RED, ORANGE, TEAL)])
        dots.arrange(RIGHT, buff=0.12).next_to(bar.get_left(), RIGHT, buff=0.2)
        fname = pop("fetch_data.py", MUTED, 0.3, font=MONO).next_to(dots, RIGHT, buff=0.3)

        code_lines = [
            ("import requests", CREAM),
            ("quakes = get(USGS)", CREAM),
            ("booms  = get(sensors)", CREAM),
            ("sky    = get(GOES_sat)", CREAM),
            ("data   = clean(all)", CREAM),
            ("ask(data)  # questions!", ORANGE),
        ]
        code = VGroup(*[pop(t, c, 0.32, font=MONO) for t, c in code_lines])
        code.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        code.next_to(bar, DOWN, buff=0.25).align_to(win, LEFT).shift(RIGHT * 0.35)

        self.play(Create(win), FadeIn(bar), FadeIn(dots), FadeIn(fname))
        self.play(LaggedStart(*[AddTextLetterByLetter(c) for c in code],
                              lag_ratio=0.55), run_time=4.2)
        self.wait(1.6)

        # --- public databases (middle) ---
        sources = VGroup(
            chip("USGS\nearthquakes", TEAL),
            chip("GOES-19\nsatellite", ORANGE),
            chip("seismic\nnetwork", TEAL),
            chip("fireball\nreports", ORANGE),
        ).arrange(DOWN, buff=0.25).move_to([-0.4, -0.2, 0])
        src_lbl = pop("public databases", MUTED, 0.36).next_to(sources, UP, buff=0.2)

        a1 = Arrow(win.get_right(), sources.get_left(), color=CREAM, buff=0.15,
                   stroke_width=4, max_tip_length_to_length_ratio=0.2)
        self.play(GrowArrow(a1), FadeIn(src_lbl),
                  LaggedStart(*[FadeIn(s, shift=RIGHT * 0.2) for s in sources],
                              lag_ratio=0.2), run_time=2.4)
        free = pop("posted online \u2014 free \u2014 by governments + universities",
                   MUTED, 0.34).to_edge(UP, buff=0.4)
        self.play(FadeIn(free))
        self.wait(2.4)

        # --- table + charts (right) ---
        table = self._table().move_to([2.9, 0.9, 0])
        tbl_lbl = pop("clean data", CREAM, 0.34).next_to(table, UP, buff=0.15)
        chart = self._chart().scale(1.15).move_to([2.9, -1.5, 0])
        chart_lbl = pop("maps & charts", ORANGE, 0.32).next_to(chart, RIGHT, buff=0.4)

        a2 = Arrow(sources.get_right(), table.get_left(), color=CREAM, buff=0.15,
                   stroke_width=4, max_tip_length_to_length_ratio=0.25)
        self.play(GrowArrow(a2))

        # data "downloads": dots fly from each source into the table
        flyers = VGroup(*[Dot(s.get_right(), radius=0.07, color=TEAL)
                          for s in sources])
        self.add(flyers)
        self.play(LaggedStart(*[f.animate.move_to(table.get_center())
                                for f in flyers], lag_ratio=0.12), run_time=2.2)
        self.play(FadeOut(flyers), FadeIn(table), FadeIn(tbl_lbl))
        self.play(Indicate(tbl_lbl, color=TEAL))
        self.wait(0.8)

        a3 = Arrow(table.get_bottom(), chart.get_top(), color=CREAM, buff=0.15,
                   stroke_width=4, max_tip_length_to_length_ratio=0.3)
        self.play(GrowArrow(a3), FadeIn(chart), FadeIn(chart_lbl))
        self.wait(1.0)
        self.play(FadeOut(free))

        tag = pop("then the real fun: ask the data questions",
                  ORANGE, 0.52).to_edge(DOWN, buff=0.35)
        self.play(FadeIn(tag))
        self.wait(0.7)   # was 3.2 -- trimmed dead hold after the last line

    # ---- little icon builders ----
    def _table(self):
        box = RoundedRectangle(corner_radius=0.08, width=1.8, height=1.3,
                               fill_color=PANEL, fill_opacity=1,
                               stroke_color=CREAM, stroke_width=2)
        lines = VGroup()
        for dy in (0.2, -0.1, -0.4):
            lines.add(Line(box.get_left() + RIGHT * 0.15 + UP * dy,
                           box.get_right() + LEFT * 0.15 + UP * dy,
                           color=MUTED, stroke_width=2))
        vsep = Line(box.get_top() + DOWN * 0.15, box.get_bottom() + UP * 0.15,
                    color=MUTED, stroke_width=2).shift(LEFT * 0.1)
        header = Line(box.get_left() + RIGHT * 0.15 + UP * 0.45,
                      box.get_right() + LEFT * 0.15 + UP * 0.45,
                      color=TEAL, stroke_width=3)
        return VGroup(box, header, lines, vsep)

    def _chart(self):
        ax = VGroup(
            Line([-0.8, -0.6, 0], [0.9, -0.6, 0], color=MUTED, stroke_width=2),
            Line([-0.8, -0.6, 0], [-0.8, 0.7, 0], color=MUTED, stroke_width=2))
        pts = [[-0.8, -0.3, 0], [-0.3, 0.2, 0], [0.1, -0.1, 0], [0.5, 0.5, 0],
               [0.9, 0.1, 0]]
        curve = VMobject(color=ORANGE, stroke_width=4).set_points_as_corners(pts)
        return VGroup(ax, curve)

    def _mappin(self):
        pin = VGroup(
            Circle(radius=0.28, color=TEAL, fill_opacity=1, stroke_color=CREAM,
                   stroke_width=2),
            Triangle(color=TEAL, fill_opacity=1, stroke_width=0).scale(0.28)
            .rotate(PI).shift(DOWN * 0.32))
        dot = Dot(pin[0].get_center(), radius=0.08, color=NAVY)
        return VGroup(pin, dot)
