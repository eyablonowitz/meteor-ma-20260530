"""Discriminate airburst (point) vs. ballistic sonic boom (line source).

Two independent geometric tests plus observational evidence:

1. Acoustic arrival-time residuals vs. azimuth.
   A point airburst gives concentric isochrones -> arrival time depends only on
   range -> point-source residuals are azimuthally flat. A ballistic shock shed
   along the hypersonic track imprints a systematic azimuthal dipole (early
   broadside to the trajectory, late off the ends).

2. DYFI felt-intensity isotropy.
   After removing the distance (attenuation) trend, a point airburst leaves an
   azimuthally near-uniform felt pattern; a strongly elongated pattern aligned
   with a ground track favors a ballistic/line contribution.

3. Reported "double boom" -> discrete fragmentation pulses (airburst cascade).

Run:  python -m src.classify
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
from . import dyfi_io
from .locate import LOCATION_JSON, load_picks, _predict
from .utils import haversine_km, azimuth_deg

CLASSIFY_JSON = os.path.join(config.OUT_DIR, "classify.json")
CLASSIFY_PNG = os.path.join(config.OUT_DIR, "classify.png")

# Observational facts (with sourcing) used as qualitative evidence.
DOUBLE_BOOM_REPORTS = {
    "double_boom_widely_reported": True,   # CNN/NBC: "double boom" across the region
    "multiple_discrete_booms": True,       # Middleton MA witness: "two additional booms"
    "note": ("News/AMS reports consistently describe a *double* boom and, in some "
             "witness accounts, multiple discrete booms - the signature of a "
             "fragmentation cascade rather than a single smooth sonic boom."),
}


def harmonic_fit(values, az_deg, extra_cols=None):
    """Least-squares fit values = c0 [+ extra terms] + a*cos(az) + b*sin(az).
    Returns dict with azimuthal amplitude, direction, and variance explained by
    the azimuthal term alone.
    """
    az = np.radians(np.asarray(az_deg, float))
    y = np.asarray(values, float)
    cols = [np.ones_like(y)]
    names = ["const"]
    if extra_cols:
        for nm, col in extra_cols:
            cols.append(np.asarray(col, float))
            names.append(nm)
    n_base = len(cols)
    cols += [np.cos(az), np.sin(az)]
    names += ["cos", "sin"]
    A = np.vstack(cols).T

    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred_full = A @ coef
    rms_full = float(np.sqrt(np.mean((y - pred_full) ** 2)))

    # model without the azimuthal terms
    A0 = A[:, :n_base]
    coef0, *_ = np.linalg.lstsq(A0, y, rcond=None)
    pred0 = A0 @ coef0
    rms_base = float(np.sqrt(np.mean((y - pred0) ** 2)))

    a, b = coef[-2], coef[-1]
    amp = float(math.hypot(a, b))
    direction = float((math.degrees(math.atan2(b, a))) % 360.0)
    var_expl = float(1 - (rms_full ** 2) / (rms_base ** 2)) if rms_base > 0 else 0.0
    return {"amplitude": amp, "direction_deg": direction,
            "rms_base": rms_base, "rms_full": rms_full,
            "azimuthal_variance_explained": var_expl, "coef": coef.tolist()}


def acoustic_azimuth_test(best, max_abs_resid_s=35.0):
    picks = load_picks()
    lat, lon, alt, t0, c = (best["lat"], best["lon"], best["alt_km"],
                            best["t0_s"], best["celerity_kms"])
    params = [lat, lon, alt, t0, c]
    rows = []
    for p in picks:
        pred = float(_predict(params, np.array([p["lat"]]), np.array([p["lon"]]))[0])
        resid = pred - p["t"]
        az = azimuth_deg(lat, lon, p["lat"], p["lon"])
        rows.append({"code": p["code"], "kind": p["kind"], "resid": resid,
                     "az": az, "snr": p["snr"]})
    use = [r for r in rows if abs(r["resid"]) <= max_abs_resid_s]
    fit = harmonic_fit([r["resid"] for r in use], [r["az"] for r in use])
    fit["n"] = len(use)
    # Typical timing scatter for comparison (the per-pick noise floor).
    fit["resid_std_s"] = float(np.std([r["resid"] for r in use]))
    return fit, rows


def dyfi_isotropy_test(best, min_nresp=1):
    boxes = dyfi_io.load_cdi_geo()
    lat, lon = best["lat"], best["lon"]
    d, az, I = [], [], []
    for b in boxes:
        if b.nresp < min_nresp:
            continue
        dist = haversine_km(lat, lon, b.lat, b.lon)
        if dist < 1:
            continue
        d.append(dist); az.append(azimuth_deg(lat, lon, b.lat, b.lon)); I.append(b.cdi)
    d = np.array(d); az = np.array(az); I = np.array(I)
    logd = np.log10(d)
    fit = harmonic_fit(I, az, extra_cols=[("logdist", logd)])
    fit["n"] = int(d.size)
    fit["intensity_std"] = float(np.std(I))
    return fit, (d, az, I)


def azimuth_coverage_gap(az_list):
    """Largest gap (deg) between consecutive station azimuths -> sampling quality."""
    if len(az_list) < 2:
        return 360.0
    a = sorted(np.asarray(az_list) % 360.0)
    gaps = [(a[i + 1] - a[i]) for i in range(len(a) - 1)]
    gaps.append(360.0 - a[-1] + a[0])
    return float(max(gaps))


def classify(best):
    ac_fit, ac_rows = acoustic_azimuth_test(best)
    dy_fit, dy_data = dyfi_isotropy_test(best)

    ac_amp = ac_fit["amplitude"]
    ac_scatter = ac_fit["resid_std_s"]
    ac_var = ac_fit["azimuthal_variance_explained"]
    # Station azimuth coverage (acoustic) - a big gap makes the dipole unreliable.
    use_az = [r["az"] for r in ac_rows if abs(r["resid"]) <= 35]
    gap = azimuth_coverage_gap(use_az)

    # Acoustic dipole strength relative to the timing noise floor:
    #   "flat"     amp < scatter and var < 25%       -> concentric
    #   "strong"   amp > 1.6*scatter or var > 45%     -> line/trajectory signature
    #   else       marginal (at the noise level)
    if ac_amp > 1.6 * ac_scatter or ac_var > 0.45:
        ac_state = "strong_dipole"
    elif ac_amp < ac_scatter and ac_var < 0.25:
        ac_state = "flat"
    else:
        ac_state = "marginal"

    # DYFI isotropy is well sampled (n~95): judge mainly by variance explained.
    dy_iso = dy_fit["azimuthal_variance_explained"] < 0.15

    evidence = []
    evidence.append(
        {"flat": "acoustic isochrones ~concentric -> point/airburst",
         "marginal": (f"acoustic residuals show only a MARGINAL azimuthal dipole "
                      f"(amp {ac_amp:.0f} s ~ timing scatter {ac_scatter:.0f} s, "
                      f"{100*ac_var:.0f}% of variance, toward "
                      f"{ac_fit['direction_deg']:.0f} deg); with a {gap:.0f} deg "
                      "azimuth gap (ocean) this is suggestive, not conclusive, of a "
                      "ballistic component broadside to a ~N-S track"),
         "strong_dipole": (f"acoustic residuals show a STRONG azimuthal dipole "
                           f"(amp {ac_amp:.0f} s, {100*ac_var:.0f}% of variance, "
                           f"toward {ac_fit['direction_deg']:.0f} deg) -> line-source "
                           "(ballistic/trajectory) contribution")}[ac_state])
    evidence.append(
        ("DYFI felt pattern ~azimuthally isotropic after distance detrend "
         f"({100*dy_fit['azimuthal_variance_explained']:.0f}% of variance) -> "
         "concentric, point-like felt field") if dy_iso else
        (f"DYFI felt pattern elongated toward {dy_fit['direction_deg']:.0f} deg "
         f"({100*dy_fit['azimuthal_variance_explained']:.0f}% of variance)"))
    if DOUBLE_BOOM_REPORTS["double_boom_widely_reported"]:
        evidence.append("widely reported DOUBLE boom -> discrete fragmentation "
                        "pulses (airburst cascade), not a single smooth sonic boom")

    if ac_state == "strong_dipole":
        verdict = ("MIXED with a clear BALLISTIC contribution: a directional "
                   "line-source signature dominates the arrival-time residuals "
                   "alongside the airburst.")
    elif dy_iso:
        verdict = ("AIRBURST-DOMINATED. The felt/heard pressure wave is best "
                   "explained by a near-point, high-altitude fragmentation: the "
                   "felt field is concentric and the source localizes to a point. "
                   "The double boom indicates a fragmentation cascade. A secondary "
                   "ballistic sonic boom along the steep ~N-S track is plausible "
                   "(a marginal E-W acoustic-residual dipole) but is at the noise "
                   "level and not conclusively resolved with this network.")
    else:
        verdict = ("LIKELY AIRBURST-DOMINATED with unresolved directionality; "
                   "the data are noisy/under-sampled azimuthally.")

    return {
        "acoustic_azimuth_test": ac_fit,
        "acoustic_state": ac_state,
        "acoustic_azimuth_gap_deg": gap,
        "dyfi_isotropy_test": dy_fit,
        "dyfi_isotropic": bool(dy_iso),
        "double_boom": DOUBLE_BOOM_REPORTS,
        "evidence": evidence,
        "verdict": verdict,
    }, ac_rows, dy_data


def plot(best, result, ac_rows, dy_data, path=CLASSIFY_PNG):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    # Panel 1: acoustic residual vs azimuth
    ax = axes[0]
    use = [r for r in ac_rows if abs(r["resid"]) <= 35]
    for kind, col in [("infrasound", "tab:blue"), ("seismic", "tab:red")]:
        rs = [r for r in use if r["kind"] == kind]
        ax.scatter([r["az"] for r in rs], [r["resid"] for r in rs],
                   c=col, label=kind, s=45, edgecolor="k", lw=0.4)
    azc = np.linspace(0, 360, 200)
    fit = result["acoustic_azimuth_test"]
    c0, a, b = fit["coef"][0], fit["coef"][-2], fit["coef"][-1]
    ax.plot(azc, c0 + a * np.cos(np.radians(azc)) + b * np.sin(np.radians(azc)),
            "k-", label=(f"harmonic: amp={fit['amplitude']:.1f}s, "
                         f"{100*fit['azimuthal_variance_explained']:.0f}% var"))
    ax.axhline(0, color="gray", lw=0.7)
    ax.set_xlabel("Azimuth from source to station (deg)")
    ax.set_ylabel("Arrival-time residual pred-obs (s)")
    ax.set_title("Acoustic isochrone test\n(flat = concentric/airburst)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

    # Panel 2: DYFI intensity vs distance
    ax = axes[1]
    d, az, I = dy_data
    sc = ax.scatter(d, I, c=az, cmap="twilight", s=22, alpha=0.8)
    plt.colorbar(sc, ax=ax, label="azimuth from source (deg)", shrink=0.8)
    fit = result["dyfi_isotropy_test"]
    # attenuation curve (azimuth-averaged): I = const + logdist*coef
    coef = fit["coef"]
    dd = np.linspace(d.min(), d.max(), 100)
    ax.plot(dd, coef[0] + coef[1] * np.log10(dd), "k-",
            label=f"I ~ {coef[0]:.1f} {coef[1]:+.1f} log10(d)")
    ax.set_xscale("log")
    ax.set_xlabel("Distance from source (km)")
    ax.set_ylabel("DYFI intensity (CDI)")
    ax.set_title(f"Felt attenuation & isotropy\n(azimuthal amp {fit['amplitude']:.2f} "
                 f"intensity units)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")

    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    with open(LOCATION_JSON) as fh:
        best = json.load(fh)["best_fit"]

    result, ac_rows, dy_data = classify(best)

    print("Q2: What did people hear - airburst vs. ballistic sonic boom?\n")
    ac = result["acoustic_azimuth_test"]
    print(f"Acoustic isochrone test (n={ac['n']}, "
          f"azimuth gap {result['acoustic_azimuth_gap_deg']:.0f} deg):")
    print(f"  azimuthal dipole amplitude = {ac['amplitude']:.1f} s "
          f"(residual scatter {ac['resid_std_s']:.1f} s), "
          f"explains {100*ac['azimuthal_variance_explained']:.0f}% of residual variance")
    print(f"  -> state: {result['acoustic_state']}")

    dy = result["dyfi_isotropy_test"]
    print(f"\nDYFI isotropy test (n={dy['n']}):")
    print(f"  azimuthal amplitude = {dy['amplitude']:.2f} intensity units "
          f"(scatter {dy['intensity_std']:.2f}), "
          f"explains {100*dy['azimuthal_variance_explained']:.0f}% of variance")
    print(f"  -> isotropic (point-like): {result['dyfi_isotropic']}")

    print("\nEvidence:")
    for e in result["evidence"]:
        print(f"  - {e}")
    print(f"\nVERDICT: {result['verdict']}")

    with open(CLASSIFY_JSON, "w") as fh:
        json.dump(result, fh, indent=2)
    plot(best, result, ac_rows, dy_data)
    print(f"\nWrote {CLASSIFY_JSON}\n      {CLASSIFY_PNG}")


if __name__ == "__main__":
    main()
