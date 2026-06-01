"""Three independent ACOUSTIC energy estimates, pressure-testing NASA's 300 t TNT.

NASA's "~300 tons of TNT" (0.3 kt) was derived from GOES-19 GLM *optical* energy.
CNEOS/JPL has no record for this event, so the acoustic estimates below are fully
independent cross-checks:

  (D) Infrasound period-yield   - ReVelle (1997)/AFTAC, period at max amplitude.
                                  log10(W_kt) = 3.34 log10(P) - 2.28   (W < 200 kt)
  (B) DYFI blast-overpressure   - invert the Collins et al. (2005) airburst
                                  overpressure law p0(E, z_b) for the felt-center
                                  peak overpressure (10-100 Pa, no glass breakage).
  (C) Seismic-amplitude bound   - air-coupled ground velocity -> incident
                                  overpressure (acoustic-to-seismic admittance) ->
                                  Collins inversion. Order-of-magnitude bound.

Run:  python -m src.energy
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from scipy.optimize import brentq

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from . import dyfi_io
from . import seismic_io as sio
from .locate import LOCATION_JSON
from .utils import slant_range_km, haversine_km

ENERGY_JSON = os.path.join(config.OUT_DIR, "energy.json")
ENERGY_PNG = os.path.join(config.OUT_DIR, "energy_summary.png")

# Period-yield relation coefficients: log10(W_kt) = A*log10(P) + B
PERIOD_YIELD = {
    "ReVelle1997 (W<200kt)": (3.34, -2.28),
    "Ens2012 a":             (3.75, -2.50),
    "Ens2012 b":             (3.28, -2.29),
}

# Felt-center peak overpressure bracket (Pa): widely rattled (no glass breakage).
DP_FELT_PA = (10.0, 100.0)
# Burst-altitude bracket (km): NASA 40 mi (64 km); allow down to 40 km.
ZB_KM = (40.0, 64.0)


# ----------------------------------------------------------------------------
# Collins et al. (2005) airburst overpressure
# ----------------------------------------------------------------------------
def collins_p0(E_kt: float, zb_m: float) -> float:
    """Peak overpressure (Pa) directly under an airburst of energy E_kt at
    altitude zb_m (Collins et al. 2005, ground-zero limit)."""
    zb1 = zb_m / (E_kt ** (1.0 / 3.0))            # energy-scaled burst altitude (m)
    return 3.14e11 * zb1 ** (-2.6) + 1.8e7 * zb1 ** (-1.13)


def collins_p_at_range(E_kt: float, zb_m: float, r_m: float) -> float:
    """Overpressure (Pa) at horizontal ground range r_m below/around the burst."""
    zb1 = zb_m / (E_kt ** (1.0 / 3.0))
    p0 = 3.14e11 * zb1 ** (-2.6) + 1.8e7 * zb1 ** (-1.13)
    beta = 34.87 * zb1 ** (-1.73)
    return p0 * math.exp(-beta * r_m / (E_kt ** (1.0 / 3.0)))


def invert_collins_E(dp_pa: float, zb_m: float, r_m: float = 0.0) -> float:
    """Solve for energy (kt) giving overpressure dp_pa at range r_m, altitude zb_m."""
    def f(logE):
        E = 10 ** logE
        p = collins_p0(E, zb_m) if r_m <= 0 else collins_p_at_range(E, zb_m, r_m)
        return p - dp_pa
    try:
        logE = brentq(f, -5, 4, maxiter=200)
        return 10 ** logE
    except ValueError:
        return float("nan")


# ----------------------------------------------------------------------------
# (D) Infrasound period-yield
# ----------------------------------------------------------------------------
def measure_period_and_amp(tr_pa, pick_utc, win_pre=8.0, win_post=70.0,
                           band=(0.15, 4.0), peak_halfwin_s=12.0):
    """Period at maximum amplitude (s) and peak-to-peak pressure (Pa).

    The "period at max amplitude" is measured by zero-crossings of the waveform
    around the envelope peak - this is robust to the red (wind/microbarom) noise
    that biases an FFT spectral-peak estimate toward long periods, which matters
    here because the event happened during a nor'easter.
    """
    from scipy.signal import hilbert

    tr = tr_pa.copy()
    tr.detrend("demean")
    tr.detrend("linear")
    tr.taper(0.05)
    nyq = 0.5 * tr.stats.sampling_rate
    tr.filter("bandpass", freqmin=band[0], freqmax=min(band[1], 0.9 * nyq),
              corners=4, zerophase=True)
    seg = tr.slice(pick_utc - win_pre, pick_utc + win_post)
    if seg.stats.npts < 16:
        return None
    data = seg.data.astype(float)
    sr = seg.stats.sampling_rate
    p2p = float(data.max() - data.min())

    env = np.abs(hilbert(data))
    ip = int(np.argmax(env))
    half = int(peak_halfwin_s * sr)
    a, b = max(0, ip - half), min(data.size, ip + half)
    sub = data[a:b] - np.mean(data[a:b])
    zc = np.where(np.diff(np.signbit(sub)))[0]
    if zc.size < 2:
        return None
    # full period = 2 x median half-period (zero-crossing spacing)
    period = float(2.0 * np.median(np.diff(zc)) / sr)
    return {"period_s": period, "p2p_pa": p2p, "amp_pa": p2p / 2.0}


def period_yield(best):
    inv = sio.load_inventory()
    st = sio.load_raw_stream()
    meta = sio.load_station_meta()
    infra = sio.select_infrasound(st, prefer_band="BDF")
    infra_pa = sio.remove_response(infra, inv)  # -> Pa

    # arrival times + SNR from picks.csv (use only confident infrasound picks)
    import csv
    from obspy import UTCDateTime
    picks, snr = {}, {}
    with open(os.path.join(config.OUT_DIR, "picks.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["kind"] == "infrasound":
                code = f"{r['network']}.{r['station']}"
                picks[code] = UTCDateTime(r["pick_utc"])
                snr[code] = float(r["snr"])

    MIN_SNR = 5.0
    rows = []
    for tr in infra_pa:
        code = f"{tr.stats.network}.{tr.stats.station}"
        if code not in picks or code not in meta or snr.get(code, 0) < MIN_SNR:
            continue
        m = measure_period_and_amp(tr, picks[code])
        if not m or not np.isfinite(m["period_s"]):
            continue
        m["code"] = code
        m["range_km"] = slant_range_km(meta[code].latitude, meta[code].longitude,
                                       best["lat"], best["lon"], best["alt_km"])
        rows.append(m)

    if not rows:
        return None
    periods = np.array([r["period_s"] for r in rows])
    p_mean = float(np.exp(np.mean(np.log(periods))))   # geometric mean

    est = {}
    for name, (A, B) in PERIOD_YIELD.items():
        est[name] = 10 ** (A * math.log10(p_mean) + B)   # kt
    # primary + spread across relations
    primary = est["ReVelle1997 (W<200kt)"]
    return {
        "method": "infrasound period-yield (ReVelle 1997 / AFTAC)",
        "per_station": [{"code": r["code"], "period_s": round(r["period_s"], 2),
                         "amp_pa": round(r["amp_pa"], 3),
                         "range_km": round(r["range_km"], 1)} for r in rows],
        "geom_mean_period_s": round(p_mean, 2),
        "period_range_s": [round(float(periods.min()), 2), round(float(periods.max()), 2)],
        "yield_kt_by_relation": {k: round(v, 4) for k, v in est.items()},
        "yield_kt": primary,
        "yield_kt_range": [round(min(est.values()), 4), round(max(est.values()), 4)],
        "yield_tons": primary * 1000.0,
    }


# ----------------------------------------------------------------------------
# (B) DYFI blast-overpressure inversion
# ----------------------------------------------------------------------------
def dyfi_blast(best):
    boxes = dyfi_io.load_cdi_geo()
    meta = dyfi_io.load_meta()
    # nearest felt boxes (for the "ground-zero" overpressure approximation)
    dists = sorted(haversine_km(best["lat"], best["lon"], b.lat, b.lon) for b in boxes)
    near_km = float(np.median(dists[:5])) if len(dists) >= 5 else float(dists[0])

    corners = []
    for dp in DP_FELT_PA:
        for zb in ZB_KM:
            E = invert_collins_E(dp, zb * 1000.0, r_m=0.0)
            corners.append(E)
    corners = [c for c in corners if np.isfinite(c)]
    E_lo, E_hi = min(corners), max(corners)
    # central estimate: geometric-mean overpressure & altitude
    dp_c = math.sqrt(DP_FELT_PA[0] * DP_FELT_PA[1])
    zb_c = math.sqrt(ZB_KM[0] * ZB_KM[1])
    E_c = invert_collins_E(dp_c, zb_c * 1000.0)

    return {
        "method": "DYFI felt overpressure -> Collins (2005) airburst inversion",
        "assumed_peak_overpressure_pa": list(DP_FELT_PA),
        "assumed_burst_altitude_km": list(ZB_KM),
        "maxmmi": meta.get("maxmmi"), "numResp": meta.get("numResp"),
        "nearest_felt_km": round(near_km, 1),
        "yield_kt": round(E_c, 4),
        "yield_kt_range": [round(E_lo, 4), round(E_hi, 4)],
        "yield_tons": E_c * 1000.0,
    }


# ----------------------------------------------------------------------------
# (C) Acoustic energy-flux bound (infrasound amplitude)
# ----------------------------------------------------------------------------
# Inverting the Collins near-source blast law at 60-270 km (the far field) is
# invalid, so the seismic/acoustic AMPLITUDE constraint is cast as an acoustic
# energy-flux bound: the time-integrated acoustic intensity at range R, spread
# over the wavefront, divided by the bolide acoustic efficiency.
RHO_AIR = 1.2          # kg/m^3 (ground)
C_AIR = 340.0          # m/s
ACOUSTIC_EFFICIENCY = (1e-4, 1e-2)   # Ens et al. (2012): integral eta >= 0.01%, ~0.1% best


def acoustic_flux_bound(best, min_snr=8.0):
    inv = sio.load_inventory()
    st = sio.load_raw_stream()
    meta = sio.load_station_meta()
    infra = sio.select_infrasound(st, prefer_band="BDF")
    infra_pa = sio.remove_response(infra, inv)

    import csv
    from obspy import UTCDateTime
    picks, snr = {}, {}
    with open(os.path.join(config.OUT_DIR, "picks.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["kind"] == "infrasound":
                code = f"{r['network']}.{r['station']}"
                picks[code] = UTCDateTime(r["pick_utc"]); snr[code] = float(r["snr"])

    rows = []
    for tr in infra_pa:
        code = f"{tr.stats.network}.{tr.stats.station}"
        if code not in picks or code not in meta or snr.get(code, 0) < min_snr:
            continue
        seg = tr.copy()
        seg.detrend("demean"); seg.detrend("linear")
        nyq = 0.5 * seg.stats.sampling_rate
        seg.filter("bandpass", freqmin=0.1, freqmax=min(8.0, 0.9 * nyq),
                   corners=4, zerophase=True)
        w = seg.slice(picks[code] - 5, picks[code] + 70)
        if w.stats.npts < 16:
            continue
        dp = w.data.astype(float)
        dt = 1.0 / w.stats.sampling_rate
        fluence = float(np.sum(dp ** 2) * dt / (RHO_AIR * C_AIR))   # J/m^2
        R = slant_range_km(meta[code].latitude, meta[code].longitude,
                           best["lat"], best["lon"], best["alt_km"]) * 1000.0
        E_ac = 2.0 * math.pi * R ** 2 * fluence    # J radiated into a hemisphere
        rows.append({"code": code, "range_km": round(R / 1000, 1),
                     "fluence_J_m2": fluence, "E_ac_J": E_ac})
    if not rows:
        return None
    E_ac_gm = float(np.exp(np.mean(np.log([r["E_ac_J"] for r in rows]))))
    E_lo = E_ac_gm / ACOUSTIC_EFFICIENCY[1] / config.TNT_TON_J / 1000.0   # kt
    E_hi = E_ac_gm / ACOUSTIC_EFFICIENCY[0] / config.TNT_TON_J / 1000.0
    E_c = math.sqrt(E_lo * E_hi)
    return {
        "method": "infrasound acoustic energy-flux bound (fluence x area / efficiency)",
        "acoustic_efficiency_range": list(ACOUSTIC_EFFICIENCY),
        "radiated_acoustic_energy_J": E_ac_gm,
        "per_station": [{"code": r["code"], "range_km": r["range_km"],
                         "fluence_J_m2": round(r["fluence_J_m2"], 4)} for r in rows],
        "yield_kt": round(E_c, 4),
        "yield_kt_range": [round(E_lo, 4), round(E_hi, 4)],
        "yield_tons": E_c * 1000.0,
        "note": "Order-of-magnitude bound: acoustic efficiency spans ~1e-4..1e-2 "
                "and hemispherical spreading is assumed.",
    }


def plot_summary(estimates, path=ENERGY_PNG):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    labels, centers, los, his = [], [], [], []
    for label, e in estimates:
        if not e:
            continue
        c = e["yield_kt"]
        if not (np.isfinite(c) and c > 0):
            continue
        labels.append(label)
        centers.append(c)
        rng = e.get("yield_kt_range") or [c, c]
        # ensure the bar brackets the marker (central can fall outside corner range)
        los.append(max(min(rng[0], c), 1e-4))
        his.append(max(rng[1], c))
    x = np.arange(len(labels))
    centers = np.array(centers)
    yerr = [centers - np.array(los), np.array(his) - centers]
    ax.errorbar(x, centers, yerr=yerr, fmt="o", ms=10, capsize=6, color="tab:blue",
                lw=2, label="acoustic estimate (range)")
    ax.axhline(config.NASA_YIELD_KT, color="tab:red", ls="--", lw=2,
               label=f"NASA GLM-optical: {config.NASA_YIELD_TONS:.0f} t = "
                     f"{config.NASA_YIELD_KT:.2f} kt")
    ax.axhspan(config.NASA_YIELD_KT / 3, config.NASA_YIELD_KT * 3, color="tab:red",
               alpha=0.10, label="NASA value x/ 3")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=12, ha="right", fontsize=9)
    ax.set_ylabel("Energy yield (kt TNT)")
    ax.set_title("Independent acoustic energy estimates vs. NASA 300 t TNT")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.3, which="both", axis="y")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    with open(LOCATION_JSON) as fh:
        best = json.load(fh)["best_fit"]
    print(f"Using located source: {best['lat']:.3f}, {best['lon']:.3f}, "
          f"h={best['alt_km']:.0f} km\n")

    d = period_yield(best)
    b = dyfi_blast(best)
    c = acoustic_flux_bound(best)

    def show(tag, e):
        if not e:
            print(f"[{tag}] no result"); return
        rng = e.get("yield_kt_range")
        rng_s = f" (range {rng[0]:.3f}-{rng[1]:.3f} kt)" if rng else ""
        print(f"[{tag}] {e['method']}")
        print(f"      yield = {e['yield_kt']:.3f} kt = {e['yield_tons']:.0f} t TNT{rng_s}")

    print("Q3: pressure-testing NASA's ~300 t TNT (0.3 kt) with ACOUSTIC energy\n")
    if d:
        print(f"(D) period-yield: geom-mean period {d['geom_mean_period_s']} s "
              f"(range {d['period_range_s'][0]}-{d['period_range_s'][1]} s), "
              f"{len(d['per_station'])} infrasound stations")
    show("D", d)
    show("B", b)
    show("C", c)

    estimates = [("(D) infrasound\nperiod-yield", d),
                 ("(B) DYFI blast\noverpressure", b),
                 ("(C) acoustic\nflux bound", c)]
    valid = [(lab, e) for lab, e in estimates if e]
    yields = [e["yield_kt"] for _, e in valid
              if np.isfinite(e["yield_kt"]) and e["yield_kt"] > 0]
    gm = float(np.exp(np.mean(np.log(yields)))) if yields else float("nan")

    print(f"\nGeometric mean of acoustic estimates: {gm:.3f} kt = {gm*1000:.0f} t TNT")
    ratio = gm / config.NASA_YIELD_KT
    verdict = ("CONSISTENT with" if 1/3 <= ratio <= 3 else
               "HIGHER than" if ratio > 3 else "LOWER than")
    print(f"NASA value: {config.NASA_YIELD_KT:.2f} kt. "
          f"Acoustic/NASA ratio = {ratio:.2f} -> acoustic estimates are "
          f"{verdict} the 300 t figure (within method uncertainty).")

    out = {"located_source": best, "estimates": {"D": d, "B": b, "C": c},
           "acoustic_geom_mean_kt": gm, "nasa_kt": config.NASA_YIELD_KT,
           "ratio_acoustic_over_nasa": ratio, "verdict": verdict}
    with open(ENERGY_JSON, "w") as fh:
        json.dump(out, fh, indent=2)
    plot_summary(estimates)
    print(f"\nWrote {ENERGY_JSON}\n      {ENERGY_PNG}")


if __name__ == "__main__":
    main()
