"""Pick the air-coupled acoustic arrival on each station and verify acoustic moveout.

For a high-altitude airburst the dominant ground signal is the *acoustic* wave
that couples into the ground (and the air column for infrasound channels). It
arrives far later than any seismic phase: at ~0.30-0.34 km/s vs. >3 km/s for P.

This module band-passes each station's vertical seismic (and infrasound) trace,
runs an STA/LTA detector inside the physically-allowed acoustic window, picks the
onset, and produces:
  outputs/picks.csv            per-station arrival picks
  outputs/record_section.png   distance-vs-time wiggles + celerity reference lines
  outputs/moveout_regression.png  arrival time vs distance with linear fit

Run:  python -m src.picks
"""
from __future__ import annotations

import csv
import os
from dataclasses import asdict, dataclass

import numpy as np
from obspy import UTCDateTime
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from . import seismic_io as sio

# Passbands (Hz)
SEISMIC_BAND = (1.0, 8.0)
INFRA_BAND = (0.5, 5.0)

# STA/LTA
STA_S = 1.0
LTA_S = 12.0
TRIG_ON = 3.0
TRIG_OFF = 1.5

PICKS_CSV = os.path.join(config.OUT_DIR, "picks.csv")
RECSEC_PNG = os.path.join(config.OUT_DIR, "record_section.png")
MOVEOUT_PNG = os.path.join(config.OUT_DIR, "moveout_regression.png")

# Max plausible source altitude for the search-window lower edge (km).
MAX_ALT_KM = 75.0


@dataclass
class Pick:
    network: str
    station: str
    channel: str
    kind: str            # "seismic" | "infrasound"
    dist_km: float
    lat: float
    lon: float
    azimuth_deg: float
    pick_utc: str
    pick_rel_s: float    # seconds after origin-time prior
    app_vel_kms: float   # dist_km / pick_rel_s (horizontal apparent velocity)
    snr: float
    triggered: bool      # True = STA/LTA onset; False = envelope-peak fallback


def _search_window(t0: UTCDateTime, dist_km: float):
    """Physically-allowed acoustic arrival window for a station at dist_km."""
    near = dist_km / 0.40                                   # fast celerity, low alt
    far = np.hypot(dist_km, MAX_ALT_KM) / 0.26 + 45.0       # slow celerity + slop
    return t0 + max(near, 20.0), t0 + far


def preprocess(tr, band):
    """Band-pass, clamping the upper corner below Nyquist. Returns None if the
    channel's sample rate is too low to support the requested band (e.g. 1 sps
    microbarometers vs. an infrasound band)."""
    tr = tr.copy()
    tr.detrend("demean")
    tr.detrend("linear")
    tr.taper(0.02)
    nyq = 0.5 * tr.stats.sampling_rate
    fmin, fmax = band
    fmax = min(fmax, 0.9 * nyq)
    if fmin >= fmax:
        return None
    tr.filter("bandpass", freqmin=fmin, freqmax=fmax, corners=4, zerophase=True)
    return tr


def pick_trace(tr, t0: UTCDateTime, dist_km: float, band) -> Pick | None:
    p = preprocess(tr, band)
    if p is None:
        return None
    sr = p.stats.sampling_rate
    data = p.data.astype(float)
    if data.size < int(LTA_S * sr) + 10:
        return None

    w_start, w_end = _search_window(t0, dist_km)
    i0 = max(0, int((w_start - p.stats.starttime) * sr))
    i1 = min(data.size, int((w_end - p.stats.starttime) * sr))
    if i1 - i0 < int(STA_S * sr) + 5:
        return None

    # Noise level from a pre-signal window (start of record .. just before w_start).
    n1 = max(0, i0 - int(60 * sr))
    noise = data[n1:i0]
    noise_rms = np.sqrt(np.mean(noise ** 2)) if noise.size else np.std(data)
    if not np.isfinite(noise_rms) or noise_rms == 0:
        noise_rms = np.std(data) or 1.0

    # STA/LTA characteristic function on the full record, evaluated in-window.
    cft = recursive_sta_lta(data, int(STA_S * sr), int(LTA_S * sr))
    seg = data[i0:i1]
    env = np.abs(seg)
    peak_amp = env.max() if env.size else 0.0
    snr = float(peak_amp / noise_rms)

    triggers = trigger_onset(cft[i0:i1], TRIG_ON, TRIG_OFF)
    if len(triggers):
        onset_idx = i0 + int(triggers[0][0])
        triggered = True
    else:
        # fallback: envelope peak inside the window
        onset_idx = i0 + int(np.argmax(env))
        triggered = False

    pick_utc = p.stats.starttime + onset_idx / sr
    rel = float(pick_utc - t0)
    app_vel = dist_km / rel if rel > 0 else float("nan")

    nslc = p.stats
    return Pick(
        network=nslc.network, station=nslc.station, channel=nslc.channel,
        kind="infrasound" if sio.is_pressure(nslc.channel) else "seismic",
        dist_km=round(dist_km, 2), lat=0.0, lon=0.0, azimuth_deg=0.0,
        pick_utc=str(pick_utc), pick_rel_s=round(rel, 2),
        app_vel_kms=round(app_vel, 4), snr=round(snr, 2), triggered=triggered,
    )


def collect_picks():
    st = sio.load_raw_stream()
    meta = sio.load_station_meta()
    t0, _, _ = sio.event_window()

    seis = sio.select_vertical_seismic(st)
    infra = sio.select_infrasound(st)

    picks: list[Pick] = []
    for tr, band in [(t, SEISMIC_BAND) for t in seis] + [(t, INFRA_BAND) for t in infra]:
        code = f"{tr.stats.network}.{tr.stats.station}"
        m = meta.get(code)
        if m is None:
            continue
        pk = pick_trace(tr, t0, m.dist_km, band)
        if pk is None:
            continue
        pk.lat, pk.lon, pk.azimuth_deg = m.latitude, m.longitude, m.azimuth_deg
        picks.append(pk)
    picks.sort(key=lambda p: (p.kind, p.dist_km))
    return picks


def write_csv(picks, path=PICKS_CSV):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(asdict(picks[0]).keys()))
        w.writeheader()
        for p in picks:
            w.writerow(asdict(p))


def apparent_velocity_stats(picks, kind, min_snr=3.0):
    """Median/spread of horizontal apparent velocity (dist/time) for one kind."""
    v = [p.app_vel_kms for p in picks
         if p.kind == kind and p.snr >= min_snr and np.isfinite(p.app_vel_kms)]
    if not v:
        return None
    v = np.array(v)
    return {"median": float(np.median(v)), "min": float(v.min()),
            "max": float(v.max()), "n": int(v.size)}


def moveout_fit(picks, use_kinds=("infrasound",), min_snr=4.0, max_iter=6):
    """Robust linear moveout t = t0 + d/c on the cleanest picks, with iterative
    2-sigma outlier rejection. d is horizontal distance to the assumed (USGS)
    source so c is an *apparent* celerity; the proper source altitude/location
    (which removes the radial-distance assumption) is solved in locate.py.
    """
    sel = [p for p in picks if p.kind in use_kinds and p.snr >= min_snr
           and np.isfinite(p.app_vel_kms)]
    if len(sel) < 3:
        sel = [p for p in picks if p.kind in use_kinds and np.isfinite(p.app_vel_kms)]
    if len(sel) < 3:
        return None

    d = np.array([p.dist_km for p in sel])
    t = np.array([p.pick_rel_s for p in sel])
    keep = np.ones(d.size, dtype=bool)
    slope = intercept = float("nan")
    for _ in range(max_iter):
        A = np.vstack([d[keep], np.ones(keep.sum())]).T
        (slope, intercept), *_ = np.linalg.lstsq(A, t[keep], rcond=None)
        resid = t - (slope * d + intercept)
        std = np.std(resid[keep]) or 1.0
        new_keep = np.abs(resid) <= 2.0 * std
        if new_keep.sum() == keep.sum() or new_keep.sum() < 3:
            break
        keep = new_keep

    pred = slope * d + intercept
    ss_res = np.sum((t[keep] - pred[keep]) ** 2)
    ss_tot = np.sum((t[keep] - t[keep].mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    used = [f"{p.network}.{p.station}" for p, k in zip(sel, keep) if k]
    return {"slope_s_per_km": float(slope), "intercept_s": float(intercept),
            "celerity_kms": 1.0 / slope if slope > 0 else float("nan"),
            "r2": float(r2), "n": int(keep.sum()), "n_input": len(sel),
            "used": used}


def plot_record_section(picks, path=RECSEC_PNG):
    st = sio.load_raw_stream()
    meta = sio.load_station_meta()
    t0, _, _ = sio.event_window()
    seis = sio.select_vertical_seismic(st)

    fig, ax = plt.subplots(figsize=(10, 8))
    scale = 14.0  # km of vertical offset per normalized unit
    for tr in seis:
        code = f"{tr.stats.network}.{tr.stats.station}"
        m = meta.get(code)
        if m is None:
            continue
        p = preprocess(tr, SEISMIC_BAND)
        if p is None:
            continue
        # decimate for plotting
        factor = max(1, int(p.stats.sampling_rate // 5))
        y = p.data[::factor].astype(float)
        x = np.arange(y.size) * (factor / p.stats.sampling_rate) + (p.stats.starttime - t0)
        norm = np.max(np.abs(y)) or 1.0
        ax.plot(x, m.dist_km + (y / norm) * scale, lw=0.4, color="k", alpha=0.7)
        ax.text(-8, m.dist_km, code, ha="right", va="center", fontsize=6)

    # picks
    for p in picks:
        if p.kind != "seismic":
            continue
        ax.plot(p.pick_rel_s, p.dist_km, "o",
                color="tab:red" if p.triggered else "tab:orange",
                ms=5, zorder=5)

    # celerity reference lines (acoustic) and P-wave
    dd = np.array([0, 300])
    for c, ls, lab in [(0.34, "--", "0.34 km/s"), (0.30, "-", "0.30 km/s"),
                       (0.27, ":", "0.27 km/s")]:
        ax.plot(dd / c, dd, ls, color="tab:blue", lw=1, label=f"acoustic {lab}")
    ax.plot(dd / config.P_VELOCITY_KMS, dd, "-", color="tab:green", lw=1,
            label=f"P {config.P_VELOCITY_KMS:.0f} km/s")

    ax.set_xlim(-20, 1150)
    ax.set_ylim(0, 290)
    ax.set_xlabel(f"Time after {config.FLASH_TIME_UTC} (s)")
    ax.set_ylabel("Source distance (km)")
    ax.set_title("Record section (band 1-8 Hz, vertical seismic) - acoustic moveout")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_moveout(picks, fit, path=MOVEOUT_PNG):
    fig, ax = plt.subplots(figsize=(8, 6))
    styles = {"infrasound": ("tab:blue", "s"), "seismic": ("tab:red", "o")}
    for kind, (color, marker) in styles.items():
        for p in [p for p in picks if p.kind == kind]:
            ax.plot(p.dist_km, p.pick_rel_s, marker, color=color, ms=6,
                    alpha=0.9 if p.triggered else 0.4,
                    mec="k" if p.triggered else "none", mew=0.4)
            ax.annotate(p.station, (p.dist_km, p.pick_rel_s), fontsize=6,
                        xytext=(3, 3), textcoords="offset points")
    # legend proxies
    for kind, (color, marker) in styles.items():
        ax.plot([], [], marker, color=color, label=f"{kind} pick")

    if fit:
        dd = np.linspace(0, max(p.dist_km for p in picks) * 1.05, 200)
        tt = fit["slope_s_per_km"] * dd + fit["intercept_s"]
        ax.plot(dd, tt, "k-", lw=1.5,
                label=(f"infrasound fit t=t0+d/c\n"
                       f"c={fit['celerity_kms']:.3f} km/s, t0={fit['intercept_s']:.0f} s\n"
                       f"R^2={fit['r2']:.3f} (n={fit['n']})"))
    # straight acoustic reference lines
    for c, ls in [(0.34, "--"), (0.30, ":")]:
        dd = np.array([0, max(p.dist_km for p in picks) * 1.05])
        ax.plot(dd, dd / c, ls, color="gray", lw=0.8, alpha=0.7,
                label=f"straight {c} km/s")

    ax.set_xlabel("Horizontal distance to USGS source (km)")
    ax.set_ylabel(f"Arrival time after {config.FLASH_TIME_UTC} (s)")
    ax.set_title("Acoustic moveout: arrival time vs distance")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    picks = collect_picks()
    if not picks:
        print("No picks produced.")
        return
    write_csv(picks)
    fit = moveout_fit(picks)

    print(f"{'net.sta':<10} {'chan':<5} {'kind':<10} {'dist':>6} {'t_rel':>7} "
          f"{'app_v':>7} {'snr':>6} trig")
    for p in picks:
        print(f"{p.network}.{p.station:<6} {p.channel:<5} {p.kind:<10} "
              f"{p.dist_km:6.1f} {p.pick_rel_s:7.1f} {p.app_vel_kms:7.3f} "
              f"{p.snr:6.1f} {'Y' if p.triggered else '.'}")

    print()
    for kind in ("infrasound", "seismic"):
        s = apparent_velocity_stats(picks, kind)
        if s:
            print(f"{kind:>11} apparent velocity: median {s['median']:.3f} km/s "
                  f"[{s['min']:.3f}-{s['max']:.3f}] (n={s['n']})")

    # Acoustic verdict from infrasound (cleanest), falling back to all picks.
    inf = apparent_velocity_stats(picks, "infrasound")
    vmed = inf["median"] if inf else None
    if vmed is not None:
        verdict = ("ACOUSTIC (~0.3 km/s, ~20x slower than P)" if 0.25 < vmed < 0.42
                   else "NOT acoustic")
        print(f"  -> M1 verdict: arrivals are {verdict}")

    if fit:
        print(f"\nInfrasound apparent moveout (linear, n={fit['n']}/{fit['n_input']}, "
              f"2-sigma trimmed):")
        print(f"  apparent celerity c = {fit['celerity_kms']:.3f} km/s, "
              f"t0 offset = {fit['intercept_s']:+.0f} s, R^2 = {fit['r2']:.3f}")
        print("  (source altitude + true location solved in locate.py)")

    plot_record_section(picks)
    plot_moveout(picks, fit)
    print(f"\nWrote {PICKS_CSV}\n      {RECSEC_PNG}\n      {MOVEOUT_PNG}")


if __name__ == "__main__":
    main()
