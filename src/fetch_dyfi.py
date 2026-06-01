"""Download USGS 'Did You Feel It?' (DYFI) products for the event.

For event us7000spjy this gets the geocoded felt-intensity GeoJSON, the
intensity-vs-distance attenuation curve (key input for the blast-overpressure
energy estimate), and the per-aggregation CDI tables.

Saves into data/dyfi/ plus a small dyfi_meta.json summary.

Run:  python -m src.fetch_dyfi
"""
from __future__ import annotations

import json
import os
import sys

import requests

from . import config

DETAIL_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    f"?eventid={config.EVENT_ID}&format=geojson"
)

# Contents we want from the DYFI product (by content key).
WANT = [
    "dyfi_geo_10km.geojson",   # geocoded felt intensities, 10 km bins (heat map)
    "dyfi_geo_1km.geojson",    # finer geocoded bins
    "dyfi_zip.geojson",        # by ZIP
    "cdi_geo.txt",             # CDI by geocoded box: intensity, nresp, dist, lat/lon
    "cdi_zip.txt",             # CDI by ZIP
    "dyfi_plot_atten.json",    # intensity vs. distance (+/- scatter)  <- key for energy
    "dyfi_plot_numresp.json",  # number of responses vs. distance
]

META_PATH = os.path.join(config.DYFI_DIR, "dyfi_meta.json")


def get_event_detail() -> dict:
    r = requests.get(DETAIL_URL, timeout=60)
    r.raise_for_status()
    return r.json()


def download(url: str, dest: str):
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    mode = "wb"
    with open(dest, mode) as fh:
        fh.write(r.content)
    return len(r.content)


def main():
    print(f"Fetching event detail: {config.EVENT_ID}")
    detail = get_event_detail()
    props = detail["properties"]
    geom = detail.get("geometry", {}).get("coordinates", [None, None, None])

    dyfi_products = props.get("products", {}).get("dyfi")
    if not dyfi_products:
        print("  ERROR: no DYFI product on this event", file=sys.stderr)
        sys.exit(2)
    prod = dyfi_products[0]
    pprops = prod.get("properties", {})
    contents = prod.get("contents", {})

    meta = {
        "event_id": config.EVENT_ID,
        "title": props.get("title"),
        "type": props.get("type"),
        "time_ms": props.get("time"),
        "source_lon": geom[0], "source_lat": geom[1], "source_depth_km": geom[2],
        "maxmmi": pprops.get("maxmmi"),
        "numResp": pprops.get("numResp"),
        "downloaded": {},
    }

    print(f"  {meta['title']}")
    print(f"  source: {meta['source_lat']}, {meta['source_lon']} | "
          f"maxmmi={meta['maxmmi']} numResp={meta['numResp']}")

    got = 0
    for key in WANT:
        c = contents.get(key)
        if not c or "url" not in c:
            print(f"  - {key}: (not present)")
            continue
        dest = os.path.join(config.DYFI_DIR, key)
        try:
            n = download(c["url"], dest)
            meta["downloaded"][key] = {"bytes": n, "path": dest}
            got += 1
            print(f"  - {key}: {n} bytes")
        except requests.RequestException as exc:
            print(f"  - {key}: FAILED ({exc})", file=sys.stderr)

    with open(META_PATH, "w") as fh:
        json.dump(meta, fh, indent=2)
    print(f"Downloaded {got}/{len(WANT)} products -> {config.DYFI_DIR}")
    print(f"Meta -> {META_PATH}")
    if got == 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
