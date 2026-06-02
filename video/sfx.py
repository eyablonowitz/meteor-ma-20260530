"""Synthesize the rough-cut's sound effects from scratch (no samples, no
licensing). Everything here is deterministic (seeded RNG) so the wavs are fully
reproducible -- run it once and `rough_cut.py` mixes them under the narration.

  sting.wav   a short downward "that-was-wrong" thunk                 [Scene 10c]

The intro boom (Scene 1) now uses a real recording
(video/assets/sfx/freesound_community-russianmeteorite_sfx-76195.mp3) instead of
a synthesized blast; the synth boom/rattle/rumble below were retired as they read
as distracting rather than helpful. They're kept here, unused, in case we revisit.

Usage:  python video/sfx.py        # writes video/assets/sfx/sting.wav (44.1k stereo)
"""
import wave
from pathlib import Path

import numpy as np

SR = 44100
OUT = Path(__file__).resolve().parent / "assets" / "sfx"
OUT.mkdir(parents=True, exist_ok=True)


def t(dur):
    return np.linspace(0, dur, int(SR * dur), endpoint=False)


def lpf(x, fc):
    """One-pole low-pass approximated by a short exponential FIR (fast, no loop)."""
    a = np.exp(-2 * np.pi * fc / SR)
    L = int(min(len(x), max(8, -np.log(1e-3) / (2 * np.pi * fc / SR))))
    k = (1 - a) * a ** np.arange(L)
    k /= k.sum()
    return np.convolve(x, k, mode="same")


def norm(sig, peak=0.95):
    m = np.max(np.abs(sig))
    return sig / m * peak if m > 0 else sig


def write(name, sig):
    sig = np.clip(norm(sig), -1.0, 1.0)
    if sig.ndim == 1:
        sig = np.stack([sig, sig], axis=1)
    data = (sig * 32767).astype("<i2").tobytes()
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data)
    print(f"  {name:12s} {sig.shape[0] / SR:5.2f}s")


def boom():
    # A deep, natural "whump" -- mostly low-passed noise (no tonal sine lead, no
    # bright crack), with a soft sub thump and a low punch, then darkened so there
    # is no synthetic high end.
    x = t(1.8)
    rng = np.random.RandomState(11)
    env = (1 - np.exp(-x / 0.008)) * np.exp(-x / 0.6)  # fast attack, slow decay
    body = lpf(rng.randn(len(x)), 85) * env            # the rumble body
    f = 46 * np.exp(-x * 3.0) + 22                      # soft, low sub thump (secondary)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.5) * 0.6
    punch = lpf(rng.randn(len(x)), 220) * np.exp(-x / 0.06) * 0.5  # low impact, no crack
    sig = np.tanh((body + sub + punch) * 1.4)          # gentle density, not harsh
    return lpf(sig, 280)                                # keep it dark / felt, not heard


def rattle():
    x = t(0.9)
    rng = np.random.RandomState(3)
    noise = rng.randn(len(x))
    band = lpf(noise, 2600) - lpf(noise, 550)          # rough band-pass (glass/frame)
    clatter = (0.5 + 0.5 * np.sin(2 * np.pi * 22 * x)) * (rng.rand(len(x)) > 0.35)
    return band * clatter * np.exp(-x / 0.32)


def rumble():
    x = t(20.0)
    f = 33 + 2 * np.sin(2 * np.pi * 0.15 * x)
    base = np.sin(2 * np.pi * np.cumsum(f) / SR)
    mod = 0.7 + 0.3 * norm(lpf(np.random.RandomState(4).randn(len(x)), 3), 1.0)
    fade = np.ones_like(x)
    fi, fo = int(SR * 2.0), int(SR * 3.0)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    return base * mod * fade


def sting():
    x = t(0.8)
    f = 330 * np.exp(-x * 5) + 100                      # downward sweep
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x / 0.3)
    thud = np.sin(2 * np.pi * 60 * x) * np.exp(-x / 0.18)
    return 0.6 * tone + 0.5 * thud


def main():
    print("synthesizing sfx ->", OUT.relative_to(Path(__file__).resolve().parents[1]))
    # Only the sting is still mixed in; boom/rattle/rumble are retired (see module
    # docstring) but the synth functions above are kept for possible reuse.
    write("sting.wav", sting())
    print("done.")


if __name__ == "__main__":
    main()
