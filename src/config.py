"""Central configuration and physical constants for the bolide analysis.

All event facts here are sourced from public reporting / USGS / NASA for the
2026-05-30 New England daylight bolide ("Sonic Boom - Eastern Massachusetts",
USGS event us7000spjy). Values flagged "approx" are quick-look reference points
used only for plotting/comparison, NOT inputs to the inversion.
"""
from __future__ import annotations

import os

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")          # MiniSEED + StationXML
DYFI_DIR = os.path.join(DATA_DIR, "dyfi")        # USGS DYFI products
OUT_DIR = os.path.join(REPO_ROOT, "outputs")     # figures, maps, summaries

for _d in (DATA_DIR, RAW_DIR, DYFI_DIR, OUT_DIR):
    os.makedirs(_d, exist_ok=True)

# Keep matplotlib's + fontconfig's caches inside the repo (the user's home cache
# dir may not be writable, e.g. under a sandbox). Set before any matplotlib import.
_MPL_CACHE = os.path.join(REPO_ROOT, ".mplcache")
_XDG_CACHE = os.path.join(REPO_ROOT, ".cache")
for _c in (_MPL_CACHE, _XDG_CACHE):
    os.makedirs(_c, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", _MPL_CACHE)
os.environ.setdefault("XDG_CACHE_HOME", _XDG_CACHE)

# --------------------------------------------------------------------------
# Event constants
# --------------------------------------------------------------------------
EVENT_ID = "us7000spjy"

# NASA/GOES bright-flash time: 2026-05-30 14:06 EDT == 18:06 UTC.
FLASH_TIME_UTC = "2026-05-30T18:06:00Z"

# Origin-time prior for the inversion (we let t0 float around the flash time).
ORIGIN_TIME_PRIOR_UTC = FLASH_TIME_UTC

# Reference source points (lat, lon, alt_km). Used for comparison overlays.
# - USGS_DYFI: USGS-assigned approximate source for the felt event (depth 0).
# - NASA_BREAKUP: "fragmented ~40 mi (64 km) over NE MA / SE NH" (approx coords).
# - GOES_FLASH: widely shared GLM flash centroid reported "over the bays /
#   southeastern MA"; GLM geolocates to a ~16 km ellipsoid so for a 40-64 km
#   source it can be mislocated by ~50-80 km toward the NNE (parallax). approx.
REF_POINTS = {
    "USGS_DYFI":   {"lat": 42.8,  "lon": -70.9,  "alt_km": 0.0},
    "NASA_BREAKUP":{"lat": 42.9,  "lon": -70.85, "alt_km": 64.0},
    "GOES_FLASH":  {"lat": 41.95, "lon": -70.45, "alt_km": 40.0},  # approx, parallax-biased
}

# --------------------------------------------------------------------------
# FDSN data acquisition
# --------------------------------------------------------------------------
FDSN_CLIENT = "IRIS"          # EarthScope/IRIS DMC federated services
FDSN_FALLBACKS = ["EARTHSCOPE", "USGS"]

# Networks with open data covering New England.
NETWORKS = ["NE", "LD", "IU", "N4", "PN", "US"]

# Broadband / strong-motion seismic channels (air-coupled ground motion).
SEISMIC_CHANNELS = "BH?,HH?,EH?,HN?"
# Microbarometer / infrasound (pressure) channels.
PRESSURE_CHANNELS = "LDO,BDO,BDF,HDF,LDF"

# Station search geometry centered on the USGS source.
SEARCH_CENTER_LAT = REF_POINTS["USGS_DYFI"]["lat"]
SEARCH_CENTER_LON = REF_POINTS["USGS_DYFI"]["lon"]
SEARCH_RADIUS_DEG = 2.6        # ~290 km

# Waveform time window (UTC). Wide enough to capture acoustic arrivals out to
# ~300 km: at ~0.30 km/s celerity, 300 km ~= 1000 s ~= 16.7 min after t0.
WINDOW_START_UTC = "2026-05-30T18:04:00Z"
WINDOW_END_UTC = "2026-05-30T18:28:00Z"

# --------------------------------------------------------------------------
# Acoustic propagation constants
# --------------------------------------------------------------------------
SOUND_SPEED_GROUND_KMS = 0.340     # ~343 m/s at 15 C, sea level
# Effective celerity for a high-altitude source's direct/refracted path to the
# ground (rays traverse colder, thinner air). Used as the prior; the inversion
# can also solve for celerity.
CELERITY_KMS = 0.300               # 300 m/s typical near-source acoustic celerity
CELERITY_BOUNDS_KMS = (0.270, 0.345)

# Seismic P-wave reference (to distinguish seismic vs. acoustic moveout).
P_VELOCITY_KMS = 6.0

# --------------------------------------------------------------------------
# Energy reference
# --------------------------------------------------------------------------
TNT_TON_J = 4.184e9                # joules per ton TNT
NASA_YIELD_TONS = 300.0            # NASA "~300 tons of TNT"
NASA_YIELD_KT = NASA_YIELD_TONS / 1000.0
NASA_YIELD_J = NASA_YIELD_TONS * TNT_TON_J

# Ambient pressure at common burst altitudes (Pa) for altitude-scaled blast laws
# (US Standard Atmosphere 1976, approximate).
P0_SEA_LEVEL_PA = 101325.0
AMBIENT_PRESSURE_PA = {0: 101325.0, 10: 26500.0, 20: 5530.0,
                       30: 1200.0, 40: 287.0, 50: 79.8, 64: 16.5}


def tons_tnt(joules: float) -> float:
    """Convert energy in joules to tons of TNT equivalent."""
    return joules / TNT_TON_J
