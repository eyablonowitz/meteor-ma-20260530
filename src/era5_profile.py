"""Turn the raw ERA5 NetCDF into a single vertical profile at the source:
temperature T(z), eastward wind u(z), northward wind v(z) on geometric height.

ERA5 pressure-level fields come on isobaric surfaces; we use the retrieved
geopotential to place each level at its true geometric height, average over the
small lat/lon box (and over the proxy days), and report the day-to-day spread of
the winds as an uncertainty band. Variable/coord names differ between CDS netCDF
vintages, so detection is defensive.
"""
from __future__ import annotations

import json
import os

import numpy as np

from . import config

ERA5_NC = os.path.join(config.RAW_DIR, "era5_profile.nc")
ERA5_META = os.path.join(config.RAW_DIR, "era5_meta.json")

G0 = 9.80665          # m/s^2, standard gravity (geopotential definition)
R_EARTH_M = 6371000.0


def _pick(ds, *names):
    for n in names:
        if n in ds.variables or n in getattr(ds, "coords", {}):
            return n
    raise KeyError(f"none of {names} found in ERA5 file (have {list(ds.variables)})")


def geopotential_to_geometric_km(z_gp_m2s2):
    """Geopotential (m^2/s^2) -> geometric height (km)."""
    h_gp = z_gp_m2s2 / G0                       # geopotential height (m)
    z_geo = R_EARTH_M * h_gp / (R_EARTH_M - h_gp)
    return z_geo / 1000.0


def load_era5_profile(path=ERA5_NC):
    """Return dict with ascending-height arrays at the source point:
    z_km, T_K, u_ms, v_ms, and per-level day-to-day std u_std, v_std (m/s)."""
    import xarray as xr

    ds = xr.open_dataset(path)
    uname = _pick(ds, "u", "u_component_of_wind")
    vname = _pick(ds, "v", "v_component_of_wind")
    tname = _pick(ds, "t", "temperature")
    zname = _pick(ds, "z", "geopotential")
    latname = _pick(ds, "latitude", "lat")
    lonname = _pick(ds, "longitude", "lon")
    # optional time dimension (proxy = several days)
    tdim = None
    for cand in ("valid_time", "time", "forecast_reference_time"):
        if cand in ds.dims:
            tdim = cand
            break

    horiz_mean = {latname: "mean", lonname: "mean"}

    def prof(name, reduce_time):
        da = ds[name].mean(dim=[latname, lonname])
        if tdim and tdim in da.dims:
            return da.mean(dim=tdim) if reduce_time else da
        return da

    u = prof(uname, True); v = prof(vname, True)
    t = prof(tname, True); z = prof(zname, True)
    # per-level day-to-day spread (std across the proxy days), if a time dim exists
    if tdim:
        u_all = ds[uname].mean(dim=[latname, lonname])
        v_all = ds[vname].mean(dim=[latname, lonname])
        u_std = u_all.std(dim=tdim).values if tdim in u_all.dims else np.zeros_like(u.values)
        v_std = v_all.std(dim=tdim).values if tdim in v_all.dims else np.zeros_like(v.values)
    else:
        u_std = np.zeros_like(u.values); v_std = np.zeros_like(v.values)

    z_km = geopotential_to_geometric_km(z.values)
    order = np.argsort(z_km)
    out = {
        "z_km": z_km[order],
        "T_K": t.values[order],
        "u_ms": u.values[order],
        "v_ms": v.values[order],
        "u_std": np.asarray(u_std)[order],
        "v_std": np.asarray(v_std)[order],
    }
    ds.close()
    out["meta"] = load_meta()
    return out


def load_meta(path=ERA5_META):
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return {}


def layer_mean_wind(prof, z0=20.0, z1=50.0):
    """Mean (u,v) over a height band; returns (u,v,speed,toward_az_deg)."""
    z = prof["z_km"]
    m = (z >= z0) & (z <= z1)
    u = float(np.mean(prof["u_ms"][m])); v = float(np.mean(prof["v_ms"][m]))
    spd = float(np.hypot(u, v))
    az = (np.degrees(np.arctan2(u, v))) % 360.0   # direction wind blows TOWARD
    return u, v, spd, float(az)


def available(path=ERA5_NC):
    return os.path.exists(path)


if __name__ == "__main__":
    if not available():
        raise SystemExit("No ERA5 file yet; run `python -m src.fetch_era5` first.")
    p = load_era5_profile()
    print("ERA5 profile at source:", p["meta"].get("mode"), p["meta"].get("days"))
    print(f"{'z_km':>7} {'T_K':>7} {'u_ms':>7} {'v_ms':>7}")
    for zk, T, u, v in zip(p["z_km"], p["T_K"], p["u_ms"], p["v_ms"]):
        print(f"{zk:7.2f} {T:7.1f} {u:7.1f} {v:7.1f}")
    u, v, spd, az = layer_mean_wind(p)
    print(f"\nStratospheric (20-50 km) mean wind: {spd:.1f} m/s toward az {az:.0f} deg")
