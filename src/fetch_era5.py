"""Fetch real ERA5 reanalysis winds + temperature for the event, via the
Copernicus Climate Data Store (CDS) API.

Requires ~/.cdsapirc with the user's CDS url + personal access token.

We pull pressure-level u/v wind, temperature, and geopotential over a small box
around the acoustic source at the flash time (2026-05-30 18:00 UTC). ERA5
pressure levels run 1000->1 hPa (surface to ~48 km), covering the troposphere
and full stratospheric duct region; geopotential gives the geometric height of
each level. Output: data/raw/era5_profile.nc

Run:  python -m src.fetch_era5
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta

from . import config

ERA5_NC = os.path.join(config.RAW_DIR, "era5_profile.nc")
ERA5_META = os.path.join(config.RAW_DIR, "era5_meta.json")

# Box around the source (N, W, S, E). ~3x4 deg keeps the request small.
SRC_LAT = 42.9
SRC_LON = -71.04
AREA = [SRC_LAT + 1.5, SRC_LON - 2.0, SRC_LAT - 1.5, SRC_LON + 2.0]

PRESSURE_LEVELS = [
    "1", "2", "3", "5", "7", "10", "20", "30", "50", "70", "100", "125", "150",
    "175", "200", "225", "250", "300", "350", "400", "450", "500", "550", "600",
    "650", "700", "750", "775", "800", "825", "850", "875", "900", "925", "950",
    "975", "1000",
]


def _build_request(days, time_hhmm):
    return {
        "product_type": ["reanalysis"],
        "variable": ["u_component_of_wind", "v_component_of_wind",
                     "temperature", "geopotential"],
        "pressure_level": PRESSURE_LEVELS,
        "year": sorted({f"{d.year:04d}" for d in days}),
        "month": sorted({f"{d.month:02d}" for d in days}),
        "day": sorted({f"{d.day:02d}" for d in days}),
        "time": [time_hhmm],
        "area": AREA,
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def _parse_cutoff(msg):
    """Pull 'latest date available ... is: YYYY-MM-DD HH:MM' from a CDS error."""
    m = re.search(r"latest date available[^:]*:\s*([0-9-]+)\s+([0-9:]+)", msg)
    if not m:
        return None
    return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M")


LICENCE_URL = ("https://cds.climate.copernicus.eu/datasets/"
               "reanalysis-era5-pressure-levels?tab=download#manage-licences")


def _licence_error(exc):
    s = str(exc).lower()
    return "licence" in s or "license" in s or "403" in s


def _retrieve(client, request, target):
    """Retrieve; raise SystemExit with actionable text on a licence (403) error."""
    try:
        client.retrieve("reanalysis-era5-pressure-levels", request, target)
    except Exception as exc:
        if _licence_error(exc):
            print("\nERA5 retrieval blocked: the dataset LICENCE is not yet accepted "
                  "on your CDS account.", file=sys.stderr)
            print("One-time fix (logged in to CDS):\n"
                  f"  1. Open {LICENCE_URL}\n"
                  "  2. Under 'Terms of use' / 'Manage licences', Accept the\n"
                  "     'Licence to use Copernicus Products'.\n"
                  "  3. Re-run:  python -m src.fetch_era5", file=sys.stderr)
            sys.exit(3)
        raise


def main():
    import cdsapi

    event = datetime.strptime(config.FLASH_TIME_UTC, "%Y-%m-%dT%H:%M:%SZ")
    client = cdsapi.Client()

    # --- Attempt 1: the actual event day/hour ---
    primary_days = [event]
    primary_hhmm = f"{event.hour:02d}:00"
    print(f"CDS request: ERA5 pressure levels @ {event:%Y-%m-%d %H}:00 UTC")
    print(f"  area (N,W,S,E) = {AREA}; {len(PRESSURE_LEVELS)} levels; u/v/T/geopotential")

    used = {"mode": "event", "days": [event.strftime("%Y-%m-%d")], "time": primary_hhmm}
    try:
        _retrieve(client, _build_request(primary_days, primary_hhmm), ERA5_NC)
    except Exception as exc:
        cutoff = _parse_cutoff(str(exc))
        if cutoff is None:
            print(f"\nERA5 retrieval FAILED (non-latency): {exc}", file=sys.stderr)
            sys.exit(2)

        # --- Attempt 2: synoptic proxy = 3 most recent same-hour analyses <= cutoff ---
        # On the cutoff day only hours <= cutoff.hour exist, so the latest synoptic
        # hour common to all 3 proxy days is the largest 6-hourly step <= cutoff.hour.
        hh = (cutoff.hour // 6) * 6
        proxy_days = [cutoff.replace(hour=0, minute=0, second=0) - timedelta(days=k)
                      for k in (2, 1, 0)]
        proxy_hhmm = f"{hh:02d}:00"
        lag = (event.date() - cutoff.date()).days
        print(f"\nEvent day not yet in ERA5 (latency). Latest available: {cutoff:%Y-%m-%d %H:%M}.")
        print(f"Falling back to a synoptic proxy: 3 most recent {proxy_hhmm} UTC analyses")
        print(f"  {[d.strftime('%Y-%m-%d') for d in proxy_days]} "
              f"(ends {lag} days before the event).")
        _retrieve(client, _build_request(proxy_days, proxy_hhmm), ERA5_NC)
        used = {"mode": "proxy",
                "days": [d.strftime("%Y-%m-%d") for d in proxy_days],
                "time": proxy_hhmm,
                "cutoff": cutoff.strftime("%Y-%m-%d %H:%M"),
                "lag_days": lag}

    used["area_NWSE"] = AREA
    used["event_utc"] = config.FLASH_TIME_UTC
    with open(ERA5_META, "w") as fh:
        json.dump(used, fh, indent=2)

    sz = os.path.getsize(ERA5_NC) / 1e6
    print(f"\nSaved {ERA5_NC} ({sz:.2f} MB)")
    print(f"      {ERA5_META} -> {used['mode']} ({', '.join(used['days'])} @ {used['time']})")


if __name__ == "__main__":
    main()
