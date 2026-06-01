"""Geometry and small shared helpers."""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np

EARTH_R_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle surface distance (km). Pure-python, no ObsPy dependency."""
    la1, lo1, la2, lo2 = map(math.radians, (lat1, lon1, lat2, lon2))
    d = (math.sin((la2 - la1) / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2)
    return 2 * EARTH_R_KM * math.asin(math.sqrt(d))


def azimuth_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2, degrees clockwise from north."""
    la1, la2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(la2)
    y = math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def slant_range_km(stat_lat: float, stat_lon: float,
                   src_lat: float, src_lon: float, src_alt_km: float) -> float:
    """3-D source->station distance: horizontal great-circle + vertical altitude."""
    horiz = haversine_km(stat_lat, stat_lon, src_lat, src_lon)
    return math.hypot(horiz, src_alt_km)


def vectorized_slant_range_km(stat_lat: np.ndarray, stat_lon: np.ndarray,
                              src_lat: float, src_lon: float, src_alt_km: float) -> np.ndarray:
    la1 = np.radians(stat_lat)
    lo1 = np.radians(stat_lon)
    la2 = math.radians(src_lat)
    lo2 = math.radians(src_lon)
    d = (np.sin((la2 - la1) / 2) ** 2
         + np.cos(la1) * math.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2)
    horiz = 2 * EARTH_R_KM * np.arcsin(np.sqrt(d))
    return np.hypot(horiz, src_alt_km)


def fmt_latlon(lat: float, lon: float) -> str:
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{abs(lat):.3f}{ns}, {abs(lon):.3f}{ew}"
