"""Objective near-field test of the southward 'beaming': now that the AM citizen
network (RaspberryShake seismographs + RaspberryBoom infrasound) fills the
near-field to the N/W/S, does the ground actually register the airwave to the
NORTH, or is the near-north genuinely in shadow?

Method (read-only; does NOT touch picks.csv / location.json):
  - For every station with data, merge gaps, band-pass, and inside the
    physically-allowed acoustic window measure peak amplitude vs. pre-signal
    noise (SNR), an STA/LTA detection flag, and the apparent celerity
    (dist / arrival-time) as a reality check that any energy is acoustic.
  - Compare AM-to-AM (identical sensor class) across azimuth in the near field
    (< 100 km) so SNR differences reflect the wavefield, not instrument type.

RaspberryShake timing is NTP (~0.1-1 s), fine for detection / SNR / rough
celerity but deliberately NOT fed back into the source inversion.

Run:  python -m src.beaming_test
"""
from __future__ import annotations

import json
import math
import os
from collections import defaultdict

import numpy as np
from obspy import Stream
from obspy.signal.trigger import recursive_sta_lta, trigger_onset

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from . import seismic_io as sio
from .picks import (preprocess, _search_window, SEISMIC_BAND, INFRA_BAND,
                    STA_S, LTA_S, TRIG_ON, TRIG_OFF)

OUT_PNG = os.path.join(config.OUT_DIR, "beaming_test.png")
OUT_JSON = os.path.join(config.OUT_DIR, "beaming_test.json")
OUT_CSV = os.path.join(config.OUT_DIR, "station_snr.csv")
NEAR_KM = 100.0


def quad(az):
    az %= 360
    return ("N" if az < 45 or az >= 315 else "E" if az < 135 else
            "S" if az < 225 else "W")


def measure(tr, t0, dist_km, band):
    """SNR, detection flag, arrival time and apparent celerity in the acoustic
    window. Returns None if the trace can't support the band/window."""
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
    n1 = max(0, i0 - int(60 * sr))
    noise = data[n1:i0]
    noise_rms = np.sqrt(np.mean(noise ** 2)) if noise.size else np.std(data)
    if not np.isfinite(noise_rms) or noise_rms == 0:
        noise_rms = np.std(data) or 1.0
    seg = data[i0:i1]
    env = np.abs(seg)
    snr = float(env.max() / noise_rms) if env.size else 0.0
    cft = recursive_sta_lta(data, int(STA_S * sr), int(LTA_S * sr))
    trig = trigger_onset(cft[i0:i1], TRIG_ON, TRIG_OFF)
    if len(trig):
        onset = i0 + int(trig[0][0]); triggered = True
    else:
        onset = i0 + int(np.argmax(env)); triggered = False
    rel = float((p.stats.starttime + onset / sr) - t0)
    return {"snr": round(snr, 2), "triggered": bool(triggered),
            "rel_s": round(rel, 1),
            "app_vel": round(dist_km / rel, 4) if rel > 0 else float("nan")}


def per_station_vertical(st):
    """One merged vertical-seismic Stream per station (gaps zero-filled)."""
    by = defaultdict(Stream)
    for tr in st:
        if sio.is_pressure(tr.stats.channel) or not tr.stats.channel.endswith("Z"):
            continue
        by[f"{tr.stats.network}.{tr.stats.station}"] += tr
    out = {}
    order = {"HHZ": 0, "BHZ": 1, "EHZ": 2}
    for code, s in by.items():
        s = s.merge(method=1, fill_value=0)
        s.traces.sort(key=lambda t: (order.get(t.stats.channel, 9),
                                     -t.stats.sampling_rate))
        out[code] = s[0]
    return out


def per_station_infra(st):
    by = defaultdict(Stream)
    for tr in st:
        if not sio.is_pressure(tr.stats.channel):
            continue
        by[f"{tr.stats.network}.{tr.stats.station}"] += tr
    out = {}
    for code, s in by.items():
        s = s.merge(method=1, fill_value=0)
        out[code] = s[0]
    return out


def main():
    st = sio.load_raw_stream()
    meta = sio.load_station_meta()
    t0, _, _ = sio.event_window()

    vert = per_station_vertical(st)
    infra = per_station_infra(st)

    rows = []
    for code, m in meta.items():
        rec = {"code": code, "net": m.network, "dist": m.dist_km,
               "az": m.azimuth_deg, "quad": quad(m.azimuth_deg),
               "is_am": m.network == "AM"}
        if code in vert:
            r = measure(vert[code], t0, m.dist_km, SEISMIC_BAND)
            if r:
                rec.update({"seis_snr": r["snr"], "seis_trig": r["triggered"],
                            "app_vel": r["app_vel"]})
        if code in infra:
            r = measure(infra[code], t0, m.dist_km, INFRA_BAND)
            if r:
                rec.update({"inf_snr": r["snr"], "inf_trig": r["triggered"]})
        if "seis_snr" in rec or "inf_snr" in rec:
            rows.append(rec)

    # ---- AM-to-AM near-field comparison (same sensor class) ----
    am_near = [r for r in rows if r["is_am"] and r["dist"] < NEAR_KM
               and "seis_snr" in r]
    print(f"AM RaspberryShake near-field (< {NEAR_KM:.0f} km) seismic stations: "
          f"{len(am_near)}")
    print(f"  {'quad':<5} {'n':>3} {'n_detect':>9} {'detect%':>8} {'median_SNR':>11} "
          f"{'median_appvel':>14}")
    summary = {}
    for q in ("N", "W", "S", "E"):
        g = [r for r in am_near if r["quad"] == q]
        if not g:
            continue
        ndet = sum(r["seis_trig"] for r in g)
        med_snr = float(np.median([r["seis_snr"] for r in g]))
        vels = [r["app_vel"] for r in g if r.get("seis_trig")
                and np.isfinite(r.get("app_vel", np.nan))]
        med_v = float(np.median(vels)) if vels else float("nan")
        summary[q] = {"n": len(g), "n_detect": ndet,
                      "detect_frac": round(ndet / len(g), 2),
                      "median_snr": round(med_snr, 2),
                      "median_app_vel": round(med_v, 3) if vels else None}
        print(f"  {q:<5} {len(g):3d} {ndet:9d} {ndet/len(g)*100:7.0f}% "
              f"{med_snr:11.2f} {med_v:14.3f}")

    # The single most diagnostic stations: near-field due-N citizen sensors
    print("\nNear-field NORTHERN stations (the former blind spot):")
    north = sorted([r for r in rows if r["quad"] == "N" and r["dist"] < NEAR_KM],
                   key=lambda r: r["dist"])
    for r in north:
        ss = (f"seis SNR={r.get('seis_snr','-')} trig={r.get('seis_trig','-')} "
              f"appvel={r.get('app_vel','-')}")
        print(f"  {r['code']:10s} d={r['dist']:5.1f} az={r['az']:5.0f}  {ss}")

    # Verdict heuristic
    if "N" in summary and "S" in summary:
        n, s = summary["N"], summary["S"]
        ratio = (s["median_snr"] / n["median_snr"]) if n["median_snr"] else float("inf")
        north_detects = n["detect_frac"] >= 0.5
        print(f"\nAM near-field SNR: median S/N-quadrant ratio = {ratio:.1f}x")
        if north_detects:
            print("  -> the airwave IS registered on near-north ground sensors: a "
                  "strong, total northern *shadow* is NOT supported; suppression "
                  "(if any) is partial.")
        else:
            print("  -> near-north ground sensors largely FAIL to detect while "
                  "southern ones do: objective support for northern suppression.")

    json.dump({"near_km": NEAR_KM, "am_quadrant_summary": summary,
               "near_north_stations": north,
               "n_stations_measured": len(rows)},
              open(OUT_JSON, "w"), indent=2, default=str)
    # full per-station table for reuse by station_coverage / raytrace
    import csv as _csv
    cols = ["code", "net", "dist", "az", "quad", "is_am",
            "seis_snr", "seis_trig", "app_vel", "inf_snr", "inf_trig"]
    with open(OUT_CSV, "w", newline="") as fh:
        w = _csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})
    plot(rows)
    print(f"\nWrote {OUT_JSON}\n      {OUT_CSV}\n      {OUT_PNG}")


def plot(rows, path=OUT_PNG):
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)

    snrs = [r["seis_snr"] for r in rows if "seis_snr" in r]
    norm = plt.Normalize(0, np.log10(max(snrs) + 1))
    for r in rows:
        if "seis_snr" not in r:
            continue
        th = math.radians(r["az"])
        mk = "^" if r["is_am"] else ("s" if "inf_snr" in r else "o")
        ec = "lime" if r.get("seis_trig") else "0.4"
        ax.scatter(th, r["dist"], c=[np.log10(r["seis_snr"] + 1)], cmap="plasma",
                   norm=norm, marker=mk, s=90 if r["is_am"] else 150,
                   edgecolor=ec, linewidth=1.4, zorder=4)
    sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
    cb = fig.colorbar(sm, ax=ax, pad=0.10, shrink=0.7)
    cb.set_label("log10(SNR+1) of acoustic-window arrival (vertical seismic)")

    # annotate near-north citizen stations
    for r in rows:
        if r["quad"] == "N" and r["dist"] < NEAR_KM:
            ax.annotate(r["code"].split(".")[1],
                        (math.radians(r["az"]), r["dist"]),
                        fontsize=7, color="navy", xytext=(4, 4),
                        textcoords="offset points")
    th = np.linspace(0, 2 * np.pi, 200)
    ax.fill_between(th, 0, NEAR_KM, color="cyan", alpha=0.06, zorder=0)
    ax.set_rmax(150)
    ax.set_title("Near-field acoustic detection by azimuth, with AM citizen network\n"
                 "(^=RaspberryShake/Boom  o=broadband  s=infrasound; "
                 "green edge=STA/LTA detection; N at top)\n"
                 "the near-NORTH is now sampled (RED1B, RB66E, ...)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
