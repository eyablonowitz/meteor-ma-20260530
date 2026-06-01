"""Effective-sound-speed ray trace: does wind ducting explain the directional
(southward) acoustic field we measured?

Physics (standard infrasound 'effective sound speed' approximation for
near-horizontal propagation in a horizontally-stratified moving atmosphere):

    c_eff(z, phi) = c(z) + w(z) . n_hat(phi)

where c(z) is the adiabatic sound speed from temperature and the second term is
the component of the horizontal wind along the propagation azimuth phi. A ray
launched at elevation angle theta0 from the ground has conserved horizontal
slowness p = cos(theta0)/c_eff(0); it refracts back to the ground (a 'duct')
only where c_eff(z) >= c_eff(0)/cos(theta0). A stratospheric duct therefore
exists for a given azimuth only if c_eff somewhere in the stratosphere exceeds
its ground value - which, because the stratopause is COLDER than the ground,
requires a sufficiently strong DOWNWIND wind. Upwind, the duct closes -> shadow.

Two wind sources are used:
  1. A parameterized climatology scenario (tropospheric + stratospheric jets) -
     kept for comparison and to compute the wind-independent duct threshold.
  2. REAL ERA5 reanalysis winds (if `python -m src.fetch_era5` has been run):
     measured u(z), v(z), T(z) over the source. ERA5 lags real time by ~5 days,
     so for a just-happened event we use the most recent same-hour analyses as a
     synoptic proxy (see src/fetch_era5.py); the day-to-day spread is carried as
     an uncertainty band. ERA5 pressure levels reach ~48 km (1 hPa); above that
     temperature falls back to USSA-76 and winds taper to zero.

Temperature (no-ERA5 path): US Standard Atmosphere 1976 (analytic, 0-85 km).

Run:  python -m src.fetch_era5   # once, real winds
      python -m src.raytrace     # climatology + ERA5 (if fetched)
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

OUT_PROF = os.path.join(config.OUT_DIR, "raytrace_profiles.png")
OUT_RAYS = os.path.join(config.OUT_DIR, "raytrace_paths.png")
OUT_AZ = os.path.join(config.OUT_DIR, "raytrace_duct_vs_azimuth.png")
OUT_JSON = os.path.join(config.OUT_DIR, "raytrace.json")
SNR_CSV = os.path.join(config.OUT_DIR, "station_snr.csv")

# ERA5-driven outputs
OUT_E_WIND = os.path.join(config.OUT_DIR, "raytrace_era5_wind.png")
OUT_E_PROF = os.path.join(config.OUT_DIR, "raytrace_era5_profiles.png")
OUT_E_AZ = os.path.join(config.OUT_DIR, "raytrace_era5_duct_vs_azimuth.png")
OUT_E_JSON = os.path.join(config.OUT_DIR, "raytrace_era5.json")

# US Standard Atmosphere 1976 temperature layers (base height km, base T K,
# lapse K/km), valid to 84.852 km.
USSA = [(0.0, 288.15, -6.5), (11.0, 216.65, 0.0), (20.0, 216.65, 1.0),
        (32.0, 228.65, 2.8), (47.0, 270.65, 0.0), (51.0, 270.65, -2.8),
        (71.0, 214.65, -2.0)]


def temperature(z_km):
    z = np.atleast_1d(z_km).astype(float)
    T = np.full_like(z, np.nan)
    for i, (h0, T0, lapse) in enumerate(USSA):
        h1 = USSA[i + 1][0] if i + 1 < len(USSA) else 85.0
        m = (z >= h0) & (z <= h1)
        T[m] = T0 + lapse * (z[m] - h0)
    T[z > 85.0] = USSA[-1][1] + USSA[-1][2] * (85.0 - USSA[-1][0])
    return T


def sound_speed(z_km):
    """Adiabatic sound speed (m/s) from USSA-76 temperature."""
    return 20.046 * np.sqrt(temperature(z_km))


def gauss_jet(z, center, sigma, speed):
    return speed * np.exp(-0.5 * ((z - center) / sigma) ** 2)


def wind_vector(z_km, trop, strat):
    """Return (east, north) wind components (m/s) vs height from two jets.
    trop/strat are dicts: {center, sigma, speed, toward_az_deg}."""
    z = np.atleast_1d(z_km).astype(float)
    east = np.zeros_like(z); north = np.zeros_like(z)
    for jet in (trop, strat):
        spd = gauss_jet(z, jet["center"], jet["sigma"], jet["speed"])
        az = math.radians(jet["toward_az_deg"])
        east += spd * math.sin(az)
        north += spd * math.cos(az)
    return east, north


def c_eff(z_km, prop_az_deg, east, north, c=None):
    """Effective sound speed along propagation azimuth prop_az."""
    if c is None:
        c = sound_speed(z_km)
    phi = math.radians(prop_az_deg)
    w_par = east * math.sin(phi) + north * math.cos(phi)   # along-prop component
    return c + w_par


def duct_threshold_ms():
    """Min downwind wind (m/s) to open a stratospheric duct from the ground:
    c_ground - max(c in stratosphere 20-60 km)."""
    z = np.linspace(0, 85, 1701)
    c = sound_speed(z)
    c0 = c[0]
    strat = c[(z >= 20) & (z <= 60)]
    return float(c0 - strat.max()), float(c0), float(strat.max())


def trace_ray(theta0_deg, z, ceff, zmax_turn=84.0, dz_step=0.1):
    """Forward-step a ground-launched ray; return (x_km[], z_km[]) and whether it
    ducts (turns) below zmax_turn. Effective-sound-speed approximation."""
    ceff0 = ceff[0]
    p = math.cos(math.radians(theta0_deg)) / ceff0
    zi = np.arange(0, 85, dz_step)
    ci = np.interp(zi, z, ceff)
    mu = p * ci
    turn = np.argmax(mu >= 1.0)
    ducts = bool(np.any(mu >= 1.0) and zi[turn] <= zmax_turn)
    if not np.any(mu >= 1.0):
        turn = len(zi) - 1
    mu_up = np.clip(mu[:turn + 1], 0, 0.999999)
    dxdz = mu_up / np.sqrt(1 - mu_up ** 2)
    x_up = np.concatenate([[0], np.cumsum(0.5 * (dxdz[1:] + dxdz[:-1]) * dz_step)])
    z_up = zi[:turn + 1]
    # mirror back down to ground
    x_dn = x_up[-1] + (x_up[-1] - x_up[::-1])
    z_dn = z_up[::-1]
    x = np.concatenate([x_up, x_dn[1:]])
    zz = np.concatenate([z_up, z_dn[1:]])
    return x, zz, ducts, (x_up[-1] * 2 if ducts else np.nan)


def duct_profile_vs_az(z, east, north, c, n_az=72):
    """For each propagation azimuth, the ducting capability in two layers:
      - stratospheric (20-60 km) -> far-field returns (~150-300 km)
      - tropospheric (4-18 km)   -> near-field returns (felt zone, <~150 km)
    Returns azs and, per layer, strength (max c_eff/c_eff0 - 1) + first-return km.
    Strength > 0 means c_eff aloft exceeds the ground value -> rays refract back."""
    azs = np.linspace(0, 360, n_az, endpoint=False)
    strat_s = []; strat_r = []; trop_s = []; trop_r = []
    in_strat = (z >= 20) & (z <= 60)
    in_trop = (z >= 4) & (z <= 18)
    for az in azs:
        ce = c_eff(z, az, east, north, c)
        ce0 = ce[0]
        strat_s.append(float(ce[in_strat].max() / ce0 - 1.0))
        trop_s.append(float(ce[in_trop].max() / ce0 - 1.0))
        # first return by layer: scan launch angles, classify turn height
        sret = np.nan; tret = np.nan
        for th in np.arange(2, 80, 1.0):
            x, zz, ducts, X = trace_ray(th, z, ce)
            if not (ducts and np.isfinite(X)):
                continue
            zturn = zz.max()
            if zturn >= 20:
                sret = X if np.isnan(sret) else min(sret, X)
            else:
                tret = X if np.isnan(tret) else min(tret, X)
        strat_r.append(sret); trop_r.append(tret)
    return (azs, np.array(strat_s), np.array(strat_r),
            np.array(trop_s), np.array(trop_r))


def load_strong_weak():
    """Observed strong/weak arrival azimuths from station_snr.csv (best SNR)."""
    rows = []
    if not os.path.exists(SNR_CSV):
        return rows
    import csv
    with open(SNR_CSV) as fh:
        for r in csv.DictReader(fh):
            def f(k):
                v = r.get(k, ""); return float(v) if v not in ("", None) else None
            snr = max([v for v in (f("seis_snr"), f("inf_snr")) if v is not None],
                      default=None)
            if snr is None:
                continue
            rows.append({"code": r["code"], "az": float(r["az"]),
                         "dist": float(r["dist"]), "snr": snr})
    return rows


# ---- scenarios ----------------------------------------------------------
# Inferred-downwind scenario: stratospheric jet blowing toward the south (the
# observed enhancement direction). Tropospheric jet also southward (nor'easter
# deep low-level flow). Magnitudes are plausible (jet 30-40 m/s).
SCN = {
    "trop":  {"center": 10.0, "sigma": 4.0, "speed": 25.0, "toward_az_deg": 185.0},
    "strat": {"center": 50.0, "sigma": 13.0, "speed": 38.0, "toward_az_deg": 190.0},
}


def main():
    z = np.linspace(0, 85, 1701)
    c = sound_speed(z)
    east, north = wind_vector(z, SCN["trop"], SCN["strat"])

    thr, c0, cstrat = duct_threshold_ms()
    print("US Standard Atmosphere 1976 sound speed:")
    print(f"  ground c0 = {c0:.1f} m/s ; stratopause max c = {cstrat:.1f} m/s")
    print(f"  => a stratospheric duct to the ground needs a DOWNWIND wind of "
          f">= {thr:.1f} m/s (upwind it stays closed -> shadow).")
    print(f"  scenario stratospheric jet: {SCN['strat']['speed']:.0f} m/s toward "
          f"az {SCN['strat']['toward_az_deg']:.0f} (>= threshold -> ducts downwind).\n")

    # duct strength & return range vs azimuth (stratospheric layer for climatology)
    azs, strength, fret, _trop_s, _trop_r = duct_profile_vs_az(z, east, north, c)
    south_i = int(np.argmin(np.abs(azs - 185)))
    north_i = int(np.argmin(np.abs(azs - 5)))
    print("Effective-sound-speed duct by direction (scenario):")
    print(f"  toward SOUTH (az~185): duct strength {strength[south_i]*100:+.1f}% "
          f"-> {'DUCTS' if strength[south_i] > 0 else 'no duct'}, "
          f"first return ~{fret[south_i]:.0f} km")
    print(f"  toward NORTH (az~5):   duct strength {strength[north_i]*100:+.1f}% "
          f"-> {'DUCTS' if strength[north_i] > 0 else 'NO duct (shadow)'}, "
          f"first return ~{fret[north_i] if np.isfinite(fret[north_i]) else float('nan'):.0f} km")

    # representative rays downwind (S) vs upwind (N)
    ce_s = c_eff(z, 185, east, north, c)
    ce_n = c_eff(z, 5, east, north, c)

    obs = load_strong_weak()
    print(f"\nObserved arrivals loaded: {len(obs)} stations.")

    # ---- figures ----
    plot_profiles(z, c, ce_s, ce_n)
    plot_paths(z, ce_s, ce_n)
    plot_az(azs, strength, fret, obs)

    json.dump({
        "ussa_ground_c_ms": c0, "ussa_stratopause_c_ms": cstrat,
        "duct_threshold_downwind_ms": thr,
        "scenario": SCN,
        "south_duct_strength_pct": round(strength[south_i] * 100, 2),
        "south_first_return_km": None if not np.isfinite(fret[south_i]) else round(fret[south_i], 1),
        "north_duct_strength_pct": round(strength[north_i] * 100, 2),
        "north_first_return_km": None if not np.isfinite(fret[north_i]) else round(fret[north_i], 1),
    }, open(OUT_JSON, "w"), indent=2)
    print(f"\nWrote {OUT_JSON}\n      {OUT_PROF}\n      {OUT_RAYS}\n      {OUT_AZ}")

    # ---- ERA5-driven run (real winds), if the reanalysis has been fetched ----
    try:
        from . import era5_profile as e5
    except Exception:
        e5 = None
    if e5 is not None and e5.available():
        run_era5(e5, obs)
    else:
        print("\n(ERA5 not fetched yet -> skipping real-wind run. "
              "Run `python -m src.fetch_era5` then re-run.)")


# ===================== ERA5 (real-wind) ray trace =========================
WIND_TAPER_KM = 15.0   # taper ERA5 winds to 0 over this span above the ERA5 top


def era5_blended_atmosphere(prof, z):
    """Blend ERA5 (0..top) with USSA-76 above: return c(z), east(z), north(z), top."""
    ze = prof["z_km"]; top = float(ze.max())
    T = np.interp(z, ze, prof["T_K"])
    T[z > top] = temperature(z[z > top])            # USSA-76 above the ERA5 top
    c = 20.046 * np.sqrt(T)
    east = np.interp(z, ze, prof["u_ms"])
    north = np.interp(z, ze, prof["v_ms"])
    # taper winds to zero above the ERA5 ceiling (no measured winds up there)
    fade = np.clip(1.0 - (z - top) / WIND_TAPER_KM, 0.0, 1.0)
    above = z > top
    east[above] *= fade[above]; north[above] *= fade[above]
    return c, east, north, top


def run_era5(e5, obs):
    prof = e5.load_era5_profile()
    meta = prof.get("meta", {})
    mode = meta.get("mode", "?")
    days = ", ".join(meta.get("days", []))
    tag = (f"ERA5 {mode}: {days} @ {meta.get('time','')} UTC"
           + (f" ({meta.get('lag_days')} d before event)" if meta.get("lag_days") else ""))
    print(f"\n=== ERA5 real-wind ray trace [{tag}] ===")

    z = np.linspace(0, 85, 1701)
    c, east, north, top = era5_blended_atmosphere(prof, z)
    print(f"  ERA5 ceiling ~{top:.1f} km (1 hPa); USSA-76 temperature above it.")

    u_s, v_s, spd_s, az_s = e5.layer_mean_wind(prof, 20, 50)
    u_t, v_t, spd_t, az_t = e5.layer_mean_wind(prof, 0, 12)
    print(f"  stratospheric (20-50 km) mean wind: {spd_s:.1f} m/s toward az {az_s:.0f} deg")
    print(f"  tropospheric  (0-12 km)  mean wind: {spd_t:.1f} m/s toward az {az_t:.0f} deg")

    azs, strat_s, strat_r, trop_s, trop_r = duct_profile_vs_az(z, east, north, c)

    def describe(name, strength, ret):
        di = int(np.argmax(strength))
        daz = float(azs[di])
        ddts = "DUCTS" if strength[di] > 0 else "no duct anywhere"
        rr = ret[di]
        print(f"  {name}: strongest toward az {daz:.0f} deg "
              f"({strength[di]*100:+.1f}%, {ddts}"
              + (f", first return ~{rr:.0f} km)" if np.isfinite(rr) else ")"))
        return di, daz

    strat_i, strat_az = describe("stratospheric (far-field)", strat_s, strat_r)
    trop_i, trop_az = describe("tropospheric  (near-field)", trop_s, trop_r)

    # combined ducting capability (whichever layer returns to ground) for the
    # alignment test: does ANY real-wind duct point at the high-SNR stations?
    combined = np.maximum(strat_s, trop_s)
    corr = beaming_alignment(obs, combined, azs)
    if corr:
        print(f"  beaming alignment (high- vs low-SNR stations): "
              f"strong-minus-weak duct strength = {corr['strong_minus_weak']:+.4f} "
              f"(~0 -> winds do NOT aim a duct at the strong stations)")

    # profiles toward the strongest near-field (tropospheric) duct vs opposite
    up_az = (trop_az + 180) % 360
    ce_down = c_eff(z, trop_az, east, north, c)
    ce_up = c_eff(z, up_az, east, north, c)

    plot_era5_wind(prof, az_s, spd_s, tag)
    plot_profiles(z, c, ce_down, ce_up, path=OUT_E_PROF,
                  labels=(f"toward az {trop_az:.0f} (tropo downwind)",
                          f"toward az {up_az:.0f} (tropo upwind)"),
                  title="ERA5 effective sound speed by direction\n"
                        "(red fill = c_eff > ground -> ducts; tropospheric duct -> E)")
    plot_era5_az(azs, strat_s, trop_s, obs, strat_az, trop_az,
                 title=f"ERA5 real-wind duct lobes vs observed SNR\n{tag}")

    json.dump({
        "tag": tag, "meta": meta, "era5_top_km": round(top, 2),
        "strat_mean_wind_ms": round(spd_s, 1), "strat_toward_az_deg": round(az_s, 1),
        "trop_mean_wind_ms": round(spd_t, 1), "trop_toward_az_deg": round(az_t, 1),
        "strat_duct_az_deg": round(strat_az, 1),
        "strat_duct_strength_pct": round(strat_s[strat_i] * 100, 2),
        "strat_first_return_km": None if not np.isfinite(strat_r[strat_i]) else round(strat_r[strat_i], 1),
        "trop_duct_az_deg": round(trop_az, 1),
        "trop_duct_strength_pct": round(trop_s[trop_i] * 100, 2),
        "trop_first_return_km": None if not np.isfinite(trop_r[trop_i]) else round(trop_r[trop_i], 1),
        "beaming_alignment": corr,
    }, open(OUT_E_JSON, "w"), indent=2)
    print(f"  Wrote {OUT_E_JSON}\n        {OUT_E_WIND}\n        {OUT_E_PROF}\n        {OUT_E_AZ}")


def beaming_alignment(obs, strength, azs):
    """Quantify whether high-SNR stations sit in the predicted downwind lobe.
    Compares mean predicted duct strength sampled at strong- vs weak-SNR azimuths."""
    if not obs:
        return None
    snrs = np.array([o["snr"] for o in obs])
    med = np.median(snrs)
    strong = [o for o in obs if o["snr"] >= med]
    weak = [o for o in obs if o["snr"] < med]

    def lobe_at(az):
        return float(np.interp(az % 360, azs, strength, period=360))

    s_strong = np.mean([lobe_at(o["az"]) for o in strong]) if strong else float("nan")
    s_weak = np.mean([lobe_at(o["az"]) for o in weak]) if weak else float("nan")
    return {"n_strong": len(strong), "n_weak": len(weak),
            "mean_duct_strength_strong": round(s_strong, 4),
            "mean_duct_strength_weak": round(s_weak, 4),
            "strong_minus_weak": round(s_strong - s_weak, 4)}


def plot_era5_az(azs, strat_s, trop_s, obs, strat_az, trop_az, path=OUT_E_AZ, title=None):
    """Both duct lobes (tropospheric=near-field, stratospheric=far-field) from the
    REAL winds, overlaid on observed station SNR. The question the plot answers:
    do either of the real-wind duct lobes point at the high-SNR stations?"""
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    th = np.radians(azs)
    pos_t = np.clip(trop_s, 0, None); pos_s = np.clip(strat_s, 0, None)
    scale = 45.0 / max(pos_t.max(), pos_s.max(), 1e-6)
    for pos, col, lab in [(pos_t, "tab:blue", "tropospheric duct (near-field)"),
                          (pos_s, "tab:red", "stratospheric duct (far-field)")]:
        r = np.append(pos, pos[0]) * scale
        ax.plot(np.append(th, th[0]), r, "-", color=col, lw=2, label=lab)
        ax.fill(np.append(th, th[0]), r, color=col, alpha=0.12)
    if obs:
        snrs = np.array([o["snr"] for o in obs])
        norm = plt.Normalize(0, np.log10(snrs.max() + 1))
        for o in obs:
            ax.scatter(math.radians(o["az"]), min(o["dist"], 60),
                       c=[np.log10(o["snr"] + 1)], cmap="viridis", norm=norm,
                       s=45, edgecolor="k", linewidth=0.4, zorder=5)
        sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
        cb = fig.colorbar(sm, ax=ax, pad=0.10, shrink=0.7)
        cb.set_label("log10(observed SNR+1)  (radius = min(dist,60) km)")
    ax.set_title(title or "ERA5 real-wind duct lobes vs observed SNR", fontsize=10)
    ax.legend(loc="upper right", fontsize=8, bbox_to_anchor=(1.18, 1.10))
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_era5_wind(prof, az_s, spd_s, tag, path=OUT_E_WIND):
    z = prof["z_km"]; u = prof["u_ms"]; v = prof["v_ms"]
    us = prof.get("u_std"); vs = prof.get("v_std")
    spd = np.hypot(u, v)
    direction = (np.degrees(np.arctan2(u, v))) % 360.0   # toward
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 8), sharey=True)
    a1.plot(u, z, "-", color="tab:green", lw=2, label="u (eastward)")
    a1.plot(v, z, "-", color="tab:purple", lw=2, label="v (northward)")
    if us is not None and np.any(us > 0):
        a1.fill_betweenx(z, u - us, u + us, color="tab:green", alpha=0.15)
        a1.fill_betweenx(z, v - vs, v + vs, color="tab:purple", alpha=0.15)
    a1.axvline(0, color="0.6", lw=1)
    a1.axhspan(20, 50, color="gold", alpha=0.10)
    a1.set_xlabel("wind component (m/s)"); a1.set_ylabel("altitude (km)")
    a1.set_ylim(0, 80); a1.legend(fontsize=9); a1.grid(alpha=0.3)
    a1.set_title("ERA5 wind components\n(shading = day-to-day spread)")

    a2.plot(spd, z, "k-", lw=2)
    a2.axhspan(20, 50, color="gold", alpha=0.10)
    for zi, di, si in zip(z[::3], direction[::3], spd[::3]):
        if si > 3 and zi <= 78:
            dx = math.sin(math.radians(di)); dy = math.cos(math.radians(di))
            a2.annotate("", xy=(si * 0.18 * dx + si, zi + 1.6 * dy),
                        xytext=(si, zi),
                        arrowprops=dict(arrowstyle="->", color="tab:red", lw=0.8))
    a2.set_xlabel("wind speed (m/s)")
    a2.set_xlim(left=0); a2.set_ylim(0, 80); a2.grid(alpha=0.3)
    a2.set_title(f"speed & toward-direction\nstrat(20-50km): {spd_s:.0f} m/s -> az {az_s:.0f}")
    fig.suptitle(f"Real measured winds over the source ({tag})", fontsize=11)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_profiles(z, c, ce_s, ce_n, path=OUT_PROF, labels=None, title=None):
    lab_s, lab_n = labels or ("c_eff toward SOUTH (downwind)",
                              "c_eff toward NORTH (upwind)")
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.plot(c, z, "k-", lw=2, label="c(z) no wind")
    ax.plot(ce_s, z, "-", color="tab:red", lw=2, label=lab_s)
    ax.plot(ce_n, z, "-", color="tab:blue", lw=2, label=lab_n)
    ax.axvline(c[0], color="gray", ls="--", lw=1)
    ax.text(c[0] + 1, 78, "ground c0", color="gray", fontsize=8, rotation=90)
    # shade where downwind c_eff exceeds ground value (ducting layer)
    duct = ce_s >= c[0]
    ax.fill_betweenx(z, c[0], ce_s, where=duct, color="tab:red", alpha=0.15)
    ax.set_xlabel("sound speed (m/s)"); ax.set_ylabel("altitude (km)")
    ax.set_ylim(0, 85); ax.set_xlim(270, 400)
    ax.set_title(title or ("Effective sound speed: downwind duct vs. upwind shadow\n"
                 "(red fill = c_eff > ground value -> rays refract back down)"))
    ax.legend(loc="upper right", fontsize=9); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_paths(z, ce_s, ce_n, path=OUT_RAYS):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 6), sharey=True)
    for ax, ce, lab, col in [(a1, ce_s, "SOUTH (downwind)", "tab:red"),
                             (a2, ce_n, "NORTH (upwind)", "tab:blue")]:
        ducted_any = False
        for th in np.arange(5, 60, 4.0):
            x, zz, ducts, X = trace_ray(th, z, ce)
            ax.plot(x, zz, color=col if ducts else "0.6", lw=0.9,
                    alpha=0.9 if ducts else 0.5)
            ducted_any |= ducts
        ax.axhspan(20, 60, color="gold", alpha=0.08)
        ax.set_xlim(0, 320); ax.set_ylim(0, 75)
        ax.set_xlabel("ground range (km)")
        ax.set_title(f"{lab}\n" + ("stratospheric returns" if ducted_any
                                   else "no return below 84 km -> SHADOW"))
        ax.grid(alpha=0.3)
    a1.set_ylabel("altitude (km)")
    fig.suptitle("Ground-launched rays (effective-sound-speed approx): "
                 "downwind ducts to the ground, upwind escapes", fontsize=11)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_az(azs, strength, fret, obs, path=OUT_AZ, title=None):
    fig = plt.figure(figsize=(10, 9))
    ax = fig.add_subplot(111, projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    th = np.radians(azs)
    # duct strength as radius shading (positive only)
    pos = np.clip(strength, 0, None)
    ax.plot(np.append(th, th[0]), np.append(pos, pos[0]) * 1000, "-",
            color="tab:red", lw=2, label="duct strength (x1000, downwind lobe)")
    ax.fill(np.append(th, th[0]), np.append(pos, pos[0]) * 1000,
            color="tab:red", alpha=0.15)
    # observed stations: radius=distance scaled, color by SNR
    if obs:
        snrs = np.array([o["snr"] for o in obs])
        norm = plt.Normalize(0, np.log10(snrs.max() + 1))
        for o in obs:
            ax.scatter(math.radians(o["az"]), min(o["dist"], 60),
                       c=[np.log10(o["snr"] + 1)], cmap="viridis", norm=norm,
                       s=45, edgecolor="k", linewidth=0.4, zorder=5)
        sm = plt.cm.ScalarMappable(cmap="viridis", norm=norm)
        cb = fig.colorbar(sm, ax=ax, pad=0.10, shrink=0.7)
        cb.set_label("log10(observed SNR+1)  (radius = min(dist,60) km)")
    ax.set_title(title or ("Predicted downwind duct lobe (red) vs. observed arrival SNR\n"
                 "scenario stratospheric+tropospheric jets toward ~S; N at top"),
                 fontsize=10)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()
