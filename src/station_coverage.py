"""Acoustic station coverage & SNR by azimuth - now including the AM citizen
network recovered by src.refetch_acoustic.

Reads:
  data/raw/stations.csv        full inventory queried (for metadata-only markers)
  outputs/station_snr.csv      per-station acoustic-window SNR/detection
                               (written by src.beaming_test; includes AM)

Produces outputs/station_coverage.png (polar: azimuth vs distance, colored by
SNR) and prints the near-field coverage table + infrasound SNR-vs-azimuth.

Run:  python -m src.beaming_test   # first, to (re)build station_snr.csv
      python -m src.station_coverage
"""
from __future__ import annotations

import csv
import math
import os
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config

STATIONS_CSV = os.path.join(config.RAW_DIR, "stations.csv")
SNR_CSV = os.path.join(config.OUT_DIR, "station_snr.csv")
OUT_PNG = os.path.join(config.OUT_DIR, "station_coverage.png")
NEAR_KM = 100.0


def load_inventory():
    sta = {}
    with open(STATIONS_CSV) as fh:
        for r in csv.DictReader(fh):
            key = (r["network"], r["station"])
            sta.setdefault(key, {"dist": float(r["dist_km"]),
                                 "az": float(r["azimuth_deg"])})
    return sta


def load_snr():
    """(net,sta) -> {dist, az, is_am, seis_snr, seis_trig, inf_snr}."""
    out = {}
    if not os.path.exists(SNR_CSV):
        return out
    with open(SNR_CSV) as fh:
        for r in csv.DictReader(fh):
            net, sta = r["code"].split(".")
            def f(k):
                v = r.get(k, "")
                return float(v) if v not in ("", None) else None
            out[(net, sta)] = {
                "dist": float(r["dist"]), "az": float(r["az"]),
                "is_am": r["is_am"] == "True",
                "seis_snr": f("seis_snr"),
                "seis_trig": r.get("seis_trig") == "True",
                "inf_snr": f("inf_snr"),
            }
    return out


def quad(az):
    az %= 360
    return ("N" if az < 45 or az >= 315 else "E" if az < 135 else
            "S" if az < 225 else "W")


def best_snr(rec):
    vals = [v for v in (rec.get("seis_snr"), rec.get("inf_snr")) if v is not None]
    return max(vals) if vals else None


def main():
    inv = load_inventory()
    snr = load_snr()
    have = set(snr)
    n_am = sum(1 for k in have if snr[k]["is_am"])
    print(f"Inventory: {len(inv)} stations queried; {len(have)} have a measured "
          f"acoustic-window SNR ({n_am} AM citizen, {len(have)-n_am} permanent).\n")

    print(f"NEAR-FIELD (< {NEAR_KM:.0f} km) coverage by azimuth:")
    near = sorted([(k, v) for k, v in {**{k: {"dist": inv[k]["dist"],
                                              "az": inv[k]["az"]} for k in inv}}.items()
                   if v["dist"] < NEAR_KM], key=lambda kv: kv[1]["az"])
    print(f"  {'sta':12s} {'dist':>6} {'az':>5} {'q':>2}  data?")
    for k, v in near:
        if k in have:
            r = snr[k]
            bits = []
            if r.get("seis_snr") is not None:
                bits.append(f"seisSNR={r['seis_snr']:.1f}"
                            f"{'*' if r['seis_trig'] else ''}")
            if r.get("inf_snr") is not None:
                bits.append(f"infSNR={r['inf_snr']:.1f}")
            tag = " ".join(bits) + ("  [AM]" if r["is_am"] else "")
        else:
            tag = "-- no waveform --"
        print(f"  {k[0]+'.'+k[1]:12s} {v['dist']:6.1f} {v['az']:5.0f} "
              f"{quad(v['az']):>2}  {tag}")

    # near-field AM seismic SNR by quadrant (same sensor class)
    print("\nNear-field AM RaspberryShake seismic SNR by quadrant "
          "(identical sensor class):")
    byq = defaultdict(list)
    for k, r in snr.items():
        if r["is_am"] and r["dist"] < NEAR_KM and r.get("seis_snr") is not None:
            byq[quad(r["az"])].append(r["seis_snr"])
    for q in ("N", "W", "S", "E"):
        if byq[q]:
            print(f"  {q}: n={len(byq[q]):2d}  median SNR={np.median(byq[q]):6.1f}")

    print("\nINFRASOUND SNR vs azimuth (permanent + AM RaspberryBoom):")
    inf = sorted([(k, r) for k, r in snr.items() if r.get("inf_snr") is not None],
                 key=lambda kr: kr[1]["az"])
    for k, r in inf:
        print(f"  {k[0]+'.'+k[1]:10s} d={r['dist']:6.0f} az={r['az']:5.0f} "
              f"{quad(r['az']):>2} infSNR={r['inf_snr']:7.1f}"
              f"{'  [AM]' if r['is_am'] else ''}")

    plot(inv, snr)
    print(f"\nWrote {OUT_PNG}")


def plot(inv, snr, path=OUT_PNG):
    fig = plt.figure(figsize=(10, 9.5))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)

    have = set(snr)
    for k, v in inv.items():
        if k not in have:
            ax.plot(math.radians(v["az"]), v["dist"], "x", color="0.65",
                    ms=6, mew=1.2, zorder=2)

    allsnr = [best_snr(r) for r in snr.values() if best_snr(r) is not None]
    norm = plt.Normalize(0, np.log10(max(allsnr) + 1))
    sm = plt.cm.ScalarMappable(cmap="plasma", norm=norm)
    for k, r in snr.items():
        s = best_snr(r)
        if s is None:
            continue
        th = math.radians(r["az"])
        is_inf = r.get("inf_snr") is not None
        mk = "^" if r["is_am"] else ("s" if is_inf else "o")
        ec = "lime" if r.get("seis_trig") else "0.4"
        ax.scatter(th, r["dist"], c=[np.log10(s + 1)], cmap="plasma", norm=norm,
                   marker=mk, s=80 if r["is_am"] else 150, edgecolor=ec,
                   linewidth=1.3, zorder=4)
    cb = fig.colorbar(sm, ax=ax, pad=0.10, shrink=0.7)
    cb.set_label("log10(SNR+1) of acoustic-window arrival")

    for k, r in snr.items():
        if quad(r["az"]) in ("N", "W") and r["dist"] < NEAR_KM and r["is_am"]:
            ax.annotate(k[1], (math.radians(r["az"]), r["dist"]), fontsize=6.5,
                        color="navy", xytext=(4, 4), textcoords="offset points")
    for k in (("N4", "I63A"), ("N4", "M63A"), ("N4", "G62A"), ("LD", "UNH"),
              ("NE", "DUNH")):
        if k in inv:
            ax.annotate(k[1], (math.radians(inv[k]["az"]), inv[k]["dist"]),
                        fontsize=7, color="darkred", xytext=(3, 3),
                        textcoords="offset points")

    th = np.linspace(0, 2 * np.pi, 200)
    ax.fill_between(th, 0, NEAR_KM, color="cyan", alpha=0.06, zorder=0)
    ax.set_rmax(290)
    ax.set_rlabel_position(110)
    ax.set_title("Acoustic station coverage & SNR by azimuth from epicenter\n"
                 "(^=AM citizen  o=broadband  s=infrasound  x=metadata only; "
                 "green edge=detection; N at top)\n"
                 "AM RaspberryShake/Boom now fills the near field incl. the N/W",
                 fontsize=9.5)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    main()
