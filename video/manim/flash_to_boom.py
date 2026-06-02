"""Science shot: light is instant, sound is slow.

A burst high in the sky; the FLASH reaches 'you' instantly, then a slow sound
ring crawls outward while a clock advances from 2:06 to 2:11 -> BOOM.

Beats are paced to the narration (scene7.mp3, via _sync.cue): the sound ring is
timed so the BOOM lands exactly on "...before you hear the thunder", with the
lightning/thunder analogy appearing just before it.

Render:  manim -qm video/manim/flash_to_boom.py FlashToBoom
"""
from manim import *
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _sync import cue, vo_duration

# ---- comic-flat palette (shared look across science shots) ----
NAVY = "#0d1b2a"
TEAL = "#2ec4b6"
ORANGE = "#ff9f1c"
CREAM = "#f7f3e3"
RED = "#e71d36"
MUTED = "#8d99ae"


def pop(txt, color=CREAM, size=0.7, stroke=0.0):
    return Text(txt, color=color, weight=BOLD,
                stroke_color="#000000", stroke_width=stroke).scale(size)


class FlashToBoom(Scene):
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

    def construct(self):
        self.camera.background_color = NAVY
        self._t = 0.0
        S = np.array([-2.6, 1.7, 0.0])      # the blast, high up
        T = np.array([3.4, -2.1, 0.0])      # you, on the ground
        ground_y = -2.55
        town_dist = float(np.linalg.norm(T - S))

        C = {
            "seen": cue("scene7", "But you heard the boom", lead=0.1),
            "light": cue("scene7", "Light travels at about", lead=0.2),
            "sound": cue("scene7", "But sound is slow", lead=0.1),
            "lightning": cue("scene7", "That's why you see lightning",
                             lead=0.2),
            "thunder": cue("scene7", "before you hear the thunder"),
            "ruler": cue("scene7", "And that delay is secretly a ruler", lead=0.2),
        }
        END = vo_duration("scene7")

        ground = Line([-7.2, ground_y, 0], [7.2, ground_y, 0],
                      color=MUTED, stroke_width=5)
        burst = Star(n=8, outer_radius=0.5, color=ORANGE, fill_opacity=1,
                     stroke_color=CREAM, stroke_width=2).move_to(S)
        src_lbl = pop("the blast\n~40 miles up", ORANGE, 0.4).next_to(
            burst, UP, buff=0.15)
        house = Triangle(color=TEAL, fill_opacity=1, stroke_color=CREAM,
                         stroke_width=2).scale(0.28).move_to(T + np.array([0, 0.2, 0]))
        town = Dot(T, radius=0.12, color=TEAL)
        you = pop("you", TEAL, 0.5).next_to(town, DOWN, buff=0.12)

        # clock driven by the sound ring's radius (radius=town_dist -> 2:11:00)
        radius = ValueTracker(0.0)

        def clock_seconds():
            return 360.0 + (radius.get_value() / town_dist) * 300.0  # from 2:06:00

        clock = always_redraw(lambda: pop(
            "2:%02d:%02d" % (int(clock_seconds() // 60), int(clock_seconds() % 60)),
            CREAM, 0.7).to_corner(UR, buff=0.5))

        # --- setup: the scene at 2:06 ---
        self._play(Create(ground), run_time=0.6)
        self._play(GrowFromCenter(burst), FadeIn(src_lbl), FadeIn(house),
                   FadeIn(town), FadeIn(you), run_time=1.0)
        self.add(clock)

        # --- FLASH: light reaches you instantly (the fireball is *seen* at 2:06) ---
        light = DashedLine(S, T, color=CREAM, stroke_width=3, dash_length=0.12)
        flash_lbl = pop("FLASH = light\n(instant)", CREAM, 0.4).move_to([0.2, 0.4, 0])
        self._play(Flash(burst, color=CREAM, line_length=0.5, num_lines=16,
                         flash_radius=0.8), run_time=0.6)
        self._play(Create(light), Indicate(town, color=CREAM, scale_factor=1.6),
                   run_time=0.7)

        # "...heard the boom around 2:11, five minutes later" -> pose the question
        gap_lbl = pop("but HEARD ~5 min later \u2014 why?", MUTED, 0.42).move_to(
            [0.0, -1.5, 0])
        self._hold_until(C["seen"])
        self._play(FadeIn(gap_lbl), run_time=0.6)

        # "Light travels ... effectively instantaneous" -> name the flash
        self._hold_until(C["light"])
        self._play(FadeIn(flash_lbl, shift=DOWN * 0.1),
                   Indicate(light, color=CREAM), run_time=0.8)

        # --- SOUND: slow ring crawls out; clock advances 2:06 -> 2:11 ---
        self._hold_until(C["sound"])
        self._play(FadeOut(light), FadeOut(flash_lbl), FadeOut(gap_lbl),
                   run_time=0.5)
        ring = always_redraw(lambda: Circle(
            radius=max(radius.get_value(), 1e-3), color=TEAL, stroke_width=6
        ).move_to(S).set_stroke(opacity=0.9))
        sound_lbl = pop("sound wave\n(slow)", TEAL, 0.4)
        unit = (T - S) / town_dist
        sound_lbl.add_updater(lambda m: m.move_to(
            S + unit * radius.get_value() + np.array([0.0, 0.45, 0.0])))
        self.add(ring, sound_lbl)

        # crawl in two parts so the analogy lands mid-crawl and the BOOM (sound
        # arrives) hits exactly on "...before you hear the thunder".
        t1 = max(0.6, (C["lightning"] - self._t)) if C["lightning"] else 7.0
        t2 = max(0.6, (C["thunder"] - C["lightning"])) if C["thunder"] else 3.0
        r1 = town_dist * (t1 / (t1 + t2))
        self._play(radius.animate.set_value(r1), run_time=t1, rate_func=linear)

        # the lightning & thunder analogy appears as the wave nears you
        lt = pop("Just like lightning & thunder:", CREAM, 0.44).move_to([-0.3, 0.95, 0])
        seq = pop("see the flash  \u2192  then hear the rumble", MUTED, 0.42).next_to(
            lt, DOWN, buff=0.15)
        self._play(radius.animate.set_value(town_dist), FadeIn(lt), FadeIn(seq),
                   run_time=t2, rate_func=linear)
        sound_lbl.clear_updaters()

        # --- BOOM at you (on "thunder"; clock reads 2:11) ---
        boom = pop("BOOM!", RED, 1.5, stroke=2).move_to(T + np.array([1.1, 1.0, 0]))
        later = pop("~5 minutes later", ORANGE, 0.5).next_to(clock, DOWN, buff=0.2)
        self._play(FadeIn(boom, scale=1.5), Wiggle(house), Flash(town, color=RED),
                   FadeOut(sound_lbl), FadeIn(later), run_time=0.8)

        # --- the delay is a ruler ---
        self._hold_until(C["ruler"])
        self._play(FadeOut(lt), FadeOut(seq), run_time=0.4)
        ruler = DoubleArrow(S, T, color=ORANGE, stroke_width=4, buff=0.35,
                            tip_length=0.2)
        ruler_lbl = pop("distance = delay \u00d7 speed of sound", ORANGE,
                        0.44).move_to([0.2, -0.55, 0])
        self._play(GrowFromCenter(ruler), FadeIn(ruler_lbl), run_time=0.9)
        tag = pop("That delay is a ruler:\nit tells us how far away the blast was.",
                  CREAM, 0.5).to_edge(DOWN, buff=0.35)
        self._play(FadeIn(tag), run_time=0.6)
        self._hold_until(END)
        self.wait(0.3)
