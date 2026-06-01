"""Locate the acoustic source from arrival-time picks.

Model (point acoustic source, straight slant-path celerity):
    t_i = t0 + sqrt( horiz(src, sta_i)^2 + alt^2 ) / c
Unknowns: source latitude, longitude, altitude, emission time t0 (relative to the
NASA flash 18:06:00Z), and celerity c. We solve by weighted nonlinear least
squares with multi-start, iterative outlier rejection, and bootstrap uncertainty.

This resolves Q1: where was the source (incl. altitude) and is it the northern
NASA "NE MA / SE NH" point or the southern GOES "over the bays" flash centroid?

Run:  python -m src.locate
"""
from __future__ import annotations

import csv
import json
import os

import numpy as np
from scipy.optimize import least_squares

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from .utils import haversine_km, vectorized_slant_range_km, fmt_latlon

PICKS_CSV = os.path.join(config.OUT_DIR, "picks.csv")
LOCATION_JSON = os.path.join(config.OUT_DIR, "location.json")
LOCATION_PNG = os.path.join(config.OUT_DIR, "location_map.png")

# Bounds: lat, lon, alt(km), t0(s rel flash), c(km/s).
# c upper bound is generous: with stations spread over many azimuths the single
# straight-path celerity is an effective value, not the local sound speed.
LB = np.array([40.5, -73.0, 0.0, -150.0, 0.28])
UB = np.array([44.8, -68.5, 90.0, 150.0, 0.42])


def pick_sigma(kind: str, snr: float, triggered: bool) -> float:
    """Timing uncertainty (s) by pick quality. Infrasound is the cleaner clock."""
    if kind == "infrasound":
        if triggered and snr >= 10:
            return 2.0
        return 3.5 if triggered else 8.0
    # seismic (emergent air-coupled onset, noisy under the nor'easter)
    if triggered and snr >= 8:
        return 4.0
    return 7.0 if triggered else 15.0


def load_picks(path=PICKS_CSV):
    rows = []
    with open(path) as fh:
        for r in csv.DictReader(fh):
            rows.append({
                "code": f"{r['network']}.{r['station']}",
                "network": r["network"], "station": r["station"],
                "channel": r["channel"], "kind": r["kind"],
                "lat": float(r["lat"]), "lon": float(r["lon"]),
                "dist_km": float(r["dist_km"]),
                "t": float(r["pick_rel_s"]),
                "snr": float(r["snr"]),
                "triggered": r["triggered"] in ("True", "true", "1"),
            })
            rows[-1]["sigma"] = pick_sigma(rows[-1]["kind"], rows[-1]["snr"],
                                           rows[-1]["triggered"])
    return rows


def _predict(params, lats, lons):
    lat, lon, alt, t0, c = params
    slant = vectorized_slant_range_km(lats, lons, lat, lon, alt)
    return t0 + slant / c


def _residuals(params, lats, lons, tobs, sigma, c_fixed=None):
    if c_fixed is not None:
        params = np.array([params[0], params[1], params[2], params[3], c_fixed])
    return (_predict(params, lats, lons) - tobs) / sigma


def _solve_once(picks, x0, c_fixed=None):
    lats = np.array([p["lat"] for p in picks])
    lons = np.array([p["lon"] for p in picks])
    tobs = np.array([p["t"] for p in picks])
    sig = np.array([p["sigma"] for p in picks])
    if c_fixed is None:
        lb, ub, x0u = LB, UB, x0
    else:
        lb, ub, x0u = LB[:4], UB[:4], x0[:4]
    res = least_squares(_residuals, x0u, bounds=(lb, ub),
                        args=(lats, lons, tobs, sig, c_fixed), method="trf")
    x = res.x if c_fixed is None else np.append(res.x, c_fixed)
    return x, res.cost


def solve(picks, c_fixed=None, reject_sigma=3.5, max_iter=5, min_keep=9):
    """Multi-start weighted LS with iterative outlier rejection.
    Returns (best_params, inlier_picks, info)."""
    starts = []
    for dlat, dlon in [(0, 0), (0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4),
                       (0.6, -0.3), (-0.6, 0.3), (-1.0, 0.5)]:
        for alt0, c0 in ((30.0, 0.32), (60.0, 0.36)):
            starts.append(np.array([42.8 + dlat, -70.9 + dlon, alt0, -20.0, c0]))

    active = list(picks)
    best = None
    for _ in range(max_iter):
        # multi-start on the current inlier set
        cand = []
        for x0 in starts:
            try:
                x, cost = _solve_once(active, x0, c_fixed)
                cand.append((cost, x))
            except Exception:
                continue
        if not cand:
            return None
        cand.sort(key=lambda z: z[0])
        x = cand[0][1]

        lats = np.array([p["lat"] for p in active])
        lons = np.array([p["lon"] for p in active])
        tobs = np.array([p["t"] for p in active])
        sig = np.array([p["sigma"] for p in active])
        norm_resid = (_predict(x, lats, lons) - tobs) / sig
        keep = np.abs(norm_resid) <= reject_sigma
        best = x
        if keep.all() or keep.sum() < min_keep:
            break
        active = [p for p, k in zip(active, keep) if k]

    # final residual diagnostics on inliers
    lats = np.array([p["lat"] for p in active])
    lons = np.array([p["lon"] for p in active])
    tobs = np.array([p["t"] for p in active])
    sig = np.array([p["sigma"] for p in active])
    tpred = _predict(best, lats, lons)
    rms = float(np.sqrt(np.mean((tpred - tobs) ** 2)))
    wrms = float(np.sqrt(np.mean(((tpred - tobs) / sig) ** 2)))
    info = {"rms_s": rms, "weighted_rms": wrms, "n_inliers": len(active),
            "n_total": len(picks)}
    return best, active, info


def bootstrap(picks, n=400, c_fixed=None, seed=0):
    rng = np.random.default_rng(seed)
    samples = []
    arr = list(picks)
    for _ in range(n):
        idx = rng.integers(0, len(arr), len(arr))
        sub = [arr[i] for i in idx]
        try:
            out = solve(sub, c_fixed=c_fixed, max_iter=2)
        except Exception:
            out = None
        if out:
            samples.append(out[0])
    if not samples:
        return None
    S = np.array(samples)
    names = ["lat", "lon", "alt_km", "t0_s", "c_kms"]
    stats = {}
    for i, nm in enumerate(names):
        col = S[:, i]
        stats[nm] = {"median": float(np.median(col)),
                     "std": float(np.std(col)),
                     "p16": float(np.percentile(col, 16)),
                     "p84": float(np.percentile(col, 84))}
    return stats, S


def compare_references(lat, lon):
    out = {}
    for name, pt in config.REF_POINTS.items():
        out[name] = {
            "lat": pt["lat"], "lon": pt["lon"], "alt_km": pt["alt_km"],
            "horiz_km": round(haversine_km(lat, lon, pt["lat"], pt["lon"]), 1),
        }
    return out


def plot_map(best, inliers, boot_S, refs, path=LOCATION_PNG):
    lat, lon, alt, t0, c = best
    fig, ax = plt.subplots(figsize=(8.5, 8))

    # stations colored by time residual
    lats = np.array([p["lat"] for p in inliers])
    lons = np.array([p["lon"] for p in inliers])
    tobs = np.array([p["t"] for p in inliers])
    resid = _predict(best, lats, lons) - tobs
    sc = ax.scatter(lons, lats, c=resid, cmap="coolwarm", s=60,
                    vmin=-15, vmax=15, edgecolor="k", zorder=4)
    for p in inliers:
        ax.annotate(p["station"], (p["lon"], p["lat"]), fontsize=6,
                    xytext=(3, 3), textcoords="offset points")
    plt.colorbar(sc, ax=ax, label="arrival-time residual (pred - obs, s)", shrink=0.7)

    # bootstrap cloud
    if boot_S is not None:
        ax.scatter(boot_S[:, 1], boot_S[:, 0], s=3, color="purple", alpha=0.12,
                   zorder=3, label="bootstrap")
    # best fit
    ax.plot(lon, lat, "*", color="gold", ms=22, mec="k", zorder=6,
            label=f"best-fit source\n{fmt_latlon(lat, lon)}, h={alt:.0f} km")
    # reference points
    marks = {"USGS_DYFI": ("s", "tab:green"), "NASA_BREAKUP": ("^", "tab:blue"),
             "GOES_FLASH": ("v", "tab:red")}
    for name, (mk, col) in marks.items():
        pt = config.REF_POINTS[name]
        ax.plot(pt["lon"], pt["lat"], mk, color=col, ms=12, mec="k", zorder=5,
                label=f"{name} ({refs[name]['horiz_km']} km)")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Acoustic source localization vs. reference points")
    ax.legend(loc="upper left", fontsize=7)
    ax.grid(alpha=0.3)
    ax.set_aspect(1.0 / np.cos(np.radians(lat)))
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    picks = load_picks()
    print(f"Loaded {len(picks)} picks "
          f"({sum(p['kind']=='infrasound' for p in picks)} infrasound, "
          f"{sum(p['kind']=='seismic' for p in picks)} seismic)")

    solved = solve(picks)
    if not solved:
        print("Localization failed.")
        return
    best, inliers, info = solved
    lat, lon, alt, t0, c = best

    print(f"\nBest-fit acoustic source:")
    print(f"  location : {fmt_latlon(lat, lon)}")
    print(f"  altitude : {alt:.1f} km")
    print(f"  t0       : flash {t0:+.0f} s  (emission time)")
    print(f"  celerity : {c:.3f} km/s")
    print(f"  fit      : rms {info['rms_s']:.1f} s, weighted-rms {info['weighted_rms']:.2f}, "
          f"{info['n_inliers']}/{info['n_total']} inliers")
    dropped = sorted({p['code'] for p in picks} - {p['code'] for p in inliers})
    if dropped:
        print(f"  outliers : {', '.join(dropped)}")

    print("\nBootstrap uncertainty (400 resamples):")
    bstat, bS = bootstrap(inliers)
    for nm in ["lat", "lon", "alt_km", "t0_s", "c_kms"]:
        s = bstat[nm]
        print(f"  {nm:7s}: {s['median']:.3f} +/- {s['std']:.3f} "
              f"(16-84%: {s['p16']:.3f} .. {s['p84']:.3f})")

    refs = compare_references(lat, lon)
    print("\nDistance from best-fit source to reference points:")
    for name, d in refs.items():
        print(f"  {name:13s} {fmt_latlon(d['lat'], d['lon'])} alt {d['alt_km']:.0f} km"
              f"  ->  {d['horiz_km']} km away")
    nearest = min(refs, key=lambda k: refs[k]["horiz_km"])
    print(f"  => epicenter is closest to {nearest}; "
          f"{refs['GOES_FLASH']['horiz_km']:.0f} km from the GOES 'bays' flash")

    # celerity sensitivity: re-solve at fixed c = 0.30 and 0.34
    sens = {}
    for cf in (0.30, 0.34):
        s2 = solve(picks, c_fixed=cf)
        if s2:
            b2 = s2[0]
            sens[f"c={cf}"] = {"lat": round(b2[0], 3), "lon": round(b2[1], 3),
                               "alt_km": round(b2[2], 1), "t0_s": round(b2[3], 1)}
    if sens:
        print("\nCelerity sensitivity (fixed-c re-solves):")
        for k, v in sens.items():
            print(f"  {k}: {fmt_latlon(v['lat'], v['lon'])}, "
                  f"h={v['alt_km']} km, t0={v['t0_s']:+.0f} s")

    # Constraint assessment: which parameters are well-determined?
    epi_well = bstat["lat"]["std"] < 0.15 and bstat["lon"]["std"] < 0.25
    alt_span = bstat["alt_km"]["p84"] - bstat["alt_km"]["p16"]
    alt_constrained = alt_span < 40.0
    assessment = {
        "epicenter_well_constrained": bool(epi_well),
        "epicenter_1sigma_km": {
            "lat": round(bstat["lat"]["std"] * 111.0, 1),
            "lon": round(bstat["lon"]["std"] * 111.0 * np.cos(np.radians(lat)), 1)},
        "altitude_constrained": bool(alt_constrained),
        "altitude_note": (
            "Altitude/celerity/emission-time are degenerate with this network "
            "(nearest infrasound 96 km, no sub-60 km stations): the epicenter is "
            "well resolved but altitude is not independently determined. Fixing a "
            "physical celerity (0.30-0.34 km/s) implies a high-altitude source "
            "(tens of km) with emission ~1 min before the rounded 18:06 flash, "
            "consistent with a high-altitude airburst."),
    }
    print("\nConstraint assessment:")
    print(f"  epicenter well-constrained: {epi_well} "
          f"(~{assessment['epicenter_1sigma_km']['lat']} km N-S, "
          f"~{assessment['epicenter_1sigma_km']['lon']} km E-W, 1-sigma)")
    print(f"  altitude constrained: {alt_constrained} "
          f"(bootstrap 16-84% spans {bstat['alt_km']['p16']:.0f}-{bstat['alt_km']['p84']:.0f} km)")

    out = {
        "best_fit": {"lat": lat, "lon": lon, "alt_km": alt, "t0_s": t0,
                     "celerity_kms": c},
        "fit": info,
        "bootstrap": bstat,
        "references": refs,
        "celerity_sensitivity": sens,
        "assessment": assessment,
        "outliers": dropped,
        "inlier_stations": sorted({p["code"] for p in inliers}),
    }
    with open(LOCATION_JSON, "w") as fh:
        json.dump(out, fh, indent=2)
    plot_map(best, inliers, bS, refs)
    print(f"\nWrote {LOCATION_JSON}\n      {LOCATION_PNG}")


if __name__ == "__main__":
    main()
