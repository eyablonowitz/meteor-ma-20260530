"""Population-density vs. DYFI response-density comparison.

The felt-report "center of mass" sits ~80 km south of the seismo-acoustically
located source. Two hypotheses:
  (1) pure SAMPLING: more people (hence more "Did You Feel It?" reporters) live
      south of the source, so reports pile up south even for an isotropic wave;
  (2) real DIRECTIONALITY: the airwave was genuinely suppressed to the north
      (downwind ducting and/or a forward-directed airburst along a N->S track).

We separate them by normalizing reports by population. For a curated set of
population centers spanning all azimuths we sum the DYFI responses falling in a
catchment radius and form reports-per-100k. Matched pairs (similar population
AND similar distance, opposite sides of the source) act as controlled
experiments - most cleanly Manchester NH vs. Lowell MA (~116k each, ~35 km, NW
vs. SSW).

Run:  python -m src.felt_population
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from .dyfi_io import load_cdi_geo
from .utils import haversine_km, azimuth_deg

OUT_PNG = os.path.join(config.OUT_DIR, "population_vs_response.png")
OUT_JSON = os.path.join(config.OUT_DIR, "felt_population.json")
CATCHMENT_KM = 12.0   # ~one 10 km DYFI box around the city centroid

# (lat, lon, 2020 census population). Spread across azimuth & distance.
CITIES = {
    # --- north half (az ~300->090 through N) ---
    "Manchester NH":  (42.99, -71.46, 115_644),
    "Concord NH":     (43.21, -71.54,  43_976),
    "Portsmouth NH":  (43.07, -70.76,  21_956),
    "Dover NH":       (43.20, -70.87,  32_741),
    "Rochester NH":   (43.30, -70.98,  32_492),
    "Portland ME":    (43.66, -70.26,  68_408),
    "Biddeford ME":   (43.49, -70.45,  22_552),
    # --- near source / west ---
    "Nashua NH":      (42.77, -71.46,  91_322),
    "Lowell MA":      (42.63, -71.32, 115_554),
    "Lawrence MA":    (42.71, -71.16,  89_143),
    "Haverhill MA":   (42.78, -71.08,  67_787),
    # --- north-shore MA coast (mirror of NH seacoast) ---
    "Lynn MA":        (42.47, -70.95, 101_253),
    "Salem MA":       (42.52, -70.90,  44_480),
    # --- south half (Boston metro + I-95 to Providence) ---
    "Boston MA":      (42.36, -71.06, 675_647),
    "Cambridge MA":   (42.37, -71.11, 118_403),
    "Somerville MA":  (42.39, -71.10,  81_045),
    "Quincy MA":      (42.25, -71.00, 101_636),
    "Brockton MA":    (42.08, -71.02, 105_643),
    "Framingham MA":  (42.28, -71.42,  72_362),
    "Worcester MA":   (42.26, -71.80, 206_518),
    "Providence RI":  (41.82, -71.41, 190_934),
}

# Controlled comparisons: similar population AND distance, opposite sides.
MATCHED_PAIRS = [
    ("Manchester NH", "Lowell MA"),     # ~116k each, ~35 km, NW vs SSW
    ("Portland ME",   "Providence RI"), # ~equidistant (~100-125 km), N vs S
    ("Portsmouth NH", "Salem MA"),      # coastal, ~30-45 km, NE vs SE
]


def catchment_responses(boxes, lat, lon, radius=CATCHMENT_KM):
    return sum(b.nresp for b in boxes
               if haversine_km(b.lat, b.lon, lat, lon) <= radius)


def build(best):
    S = (best["lat"], best["lon"])
    boxes = load_cdi_geo(drop_suspect=True)
    rows = []
    for name, (lat, lon, pop) in CITIES.items():
        n = catchment_responses(boxes, lat, lon)
        d = haversine_km(lat, lon, S[0], S[1])
        az = azimuth_deg(S[0], S[1], lat, lon)
        ns = (lat - S[0]) * 111.0   # signed N(+)/S(-) offset, km
        rows.append({"city": name, "lat": lat, "lon": lon, "pop": pop,
                     "responses": int(n), "dist_km": round(d, 1),
                     "az_deg": round(az, 0), "ns_km": round(ns, 0),
                     "per_100k": round(n / pop * 1e5, 2)})
    return rows, S


def plot(rows, S, path=OUT_PNG):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5))
    north = [r for r in rows if r["ns_km"] >= 0]
    south = [r for r in rows if r["ns_km"] < 0]

    # Panel 1: population vs responses, colored by N/S
    for grp, col, mk, lab in [(south, "#1f77b4", "o", "south of source"),
                              (north, "#d62728", "^", "north of source")]:
        ax1.scatter([r["pop"] for r in grp], [r["responses"] for r in grp],
                    c=col, marker=mk, s=90, edgecolor="k", zorder=3, label=lab)
    for r in rows:
        ax1.annotate(r["city"].replace(" MA", "").replace(" NH", "").replace(" ME", ""),
                     (r["pop"], r["responses"]), fontsize=7.5,
                     xytext=(4, 3), textcoords="offset points")
    ax1.set_xscale("log")
    ax1.set_xlabel("city population (2020 census)  ~ population density")
    ax1.set_ylabel("DYFI responses within 12 km  ~ response density")
    ax1.set_title("Response density vs. population\n(north-of-source cities sit far below the trend)")
    ax1.legend(loc="upper left"); ax1.grid(alpha=0.3, which="both")

    # Panel 2: reports per 100k vs signed N/S offset
    for grp, col, mk in [(south, "#1f77b4", "o"), (north, "#d62728", "^")]:
        ax2.scatter([r["ns_km"] for r in grp], [r["per_100k"] for r in grp],
                    c=col, marker=mk, s=90, edgecolor="k", zorder=3)
    for r in rows:
        ax2.annotate(r["city"].replace(" MA", "").replace(" NH", "").replace(" ME", ""),
                     (r["ns_km"], r["per_100k"]), fontsize=7.5,
                     xytext=(4, 3), textcoords="offset points")
    ax2.axvline(0, color="gray", ls="--", lw=1)
    ax2.text(2, ax2.get_ylim()[1]*0.92, "source latitude", fontsize=8, color="gray")
    ax2.set_xlabel("signed distance from source latitude  (south  <-  0  ->  north, km)")
    ax2.set_ylabel("reports per 100,000 people")
    ax2.set_title("Per-capita reporting rate vs. N/S position\n(reporting collapses north of the source)")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    best = json.load(open(os.path.join(config.OUT_DIR, "location.json")))["best_fit"]
    rows, S = build(best)
    rows.sort(key=lambda r: -r["ns_km"])  # north -> south

    print(f"Source {S[0]:.3f},{S[1]:.3f}.  DYFI responses within {CATCHMENT_KM:.0f} km "
          "of each population center:\n")
    print(f"  {'city':14s} {'pop':>8} {'dist':>6} {'az':>4} {'N/S km':>7} "
          f"{'resp':>5} {'per100k':>8}")
    for r in rows:
        print(f"  {r['city']:14s} {r['pop']:8,d} {r['dist_km']:6.0f} {r['az_deg']:4.0f} "
              f"{r['ns_km']:7.0f} {r['responses']:5d} {r['per_100k']:8.2f}")

    # hemisphere per-capita rates
    def rate(grp):
        p = sum(r["pop"] for r in grp); n = sum(r["responses"] for r in grp)
        return n, p, (n / p * 1e5 if p else 0)
    nn, npop, nr = rate([r for r in rows if r["ns_km"] >= 0])
    sn, spop, sr = rate([r for r in rows if r["ns_km"] < 0])
    print(f"\n  NORTH of source: {nn:3d} resp / {npop:,} people = {nr:.2f} per 100k")
    print(f"  SOUTH of source: {sn:3d} resp / {spop:,} people = {sr:.2f} per 100k")
    print(f"  -> south reports {sr/nr:.1f}x more PER CAPITA than north "
          "(beyond the raw population imbalance).")

    print("\n  Matched pairs (similar population AND distance, opposite sides):")
    by = {r["city"]: r for r in rows}
    for a, b in MATCHED_PAIRS:
        ra, rb = by[a], by[b]
        print(f"    {a:14s} pop {ra['pop']:7,d} d={ra['dist_km']:3.0f}km -> "
              f"{ra['responses']:3d} resp ({ra['per_100k']:.2f}/100k)   vs   "
              f"{b:14s} pop {rb['pop']:7,d} d={rb['dist_km']:3.0f}km -> "
              f"{rb['responses']:3d} resp ({rb['per_100k']:.2f}/100k)")

    json.dump({"source": S, "catchment_km": CATCHMENT_KM, "cities": rows,
               "north_per_100k": round(nr, 2), "south_per_100k": round(sr, 2)},
              open(OUT_JSON, "w"), indent=2)
    plot(rows, S)
    print(f"\nWrote {OUT_JSON}\n      {OUT_PNG}")


if __name__ == "__main__":
    main()
