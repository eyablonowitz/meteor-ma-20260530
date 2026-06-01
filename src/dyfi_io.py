"""Parsers for the downloaded USGS DYFI products."""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass

from . import config

CDI_GEO = os.path.join(config.DYFI_DIR, "cdi_geo.txt")
ATTEN = os.path.join(config.DYFI_DIR, "dyfi_plot_atten.json")
META = os.path.join(config.DYFI_DIR, "dyfi_meta.json")
GEO_10KM = os.path.join(config.DYFI_DIR, "dyfi_geo_10km.geojson")


@dataclass
class CdiBox:
    cdi: float
    nresp: int
    dist_km: float          # USGS hypocentral distance (depth 0 -> epicentral)
    lat: float
    lon: float
    stddev: float
    city: str
    state: str
    suspect: bool


def load_meta() -> dict:
    with open(META) as fh:
        return json.load(fh)


def load_cdi_geo(path: str = CDI_GEO, drop_suspect: bool = True) -> list[CdiBox]:
    """Parse cdi_geo.txt. Columns:
    Geocoded box, CDI, No. responses, Hypocentral distance, Lat, Lon,
    Suspect?, Std dev, City, State
    """
    out: list[CdiBox] = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            row = next(csv.reader([line]))
            if len(row) < 8:
                continue
            try:
                box = CdiBox(
                    cdi=float(row[1]), nresp=int(float(row[2])),
                    dist_km=float(row[3]), lat=float(row[4]), lon=float(row[5]),
                    suspect=bool(int(float(row[6]))) if row[6] != "" else False,
                    stddev=float(row[7]) if row[7] != "" else 0.0,
                    city=row[8] if len(row) > 8 else "",
                    state=row[9] if len(row) > 9 else "",
                )
            except (ValueError, IndexError):
                continue
            if drop_suspect and box.suspect:
                continue
            out.append(box)
    return out


def load_atten(path: str = ATTEN) -> dict:
    """Return {legend: [(dist_km, intensity), ...]} for each atten dataset."""
    with open(path) as fh:
        raw = json.load(fh)
    out = {}
    for ds in raw.get("datasets", []):
        out[ds.get("legend", "data")] = [(p["x"], p["y"]) for p in ds["data"]]
    return out


def load_geojson(path: str = GEO_10KM) -> dict:
    with open(path) as fh:
        return json.load(fh)
