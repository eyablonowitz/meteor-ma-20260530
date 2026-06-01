"""Shared loaders for the downloaded seismic/infrasound data.

Centralizes reading the raw MiniSEED + StationXML + stations.csv and provides
instrument-response removal and convenience selectors used by the analysis
modules.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass

from obspy import Stream, UTCDateTime, read, read_inventory

from . import config

INV_PATH = os.path.join(config.RAW_DIR, "inventory.xml")
MSEED_PATH = os.path.join(config.RAW_DIR, "waveforms_raw.mseed")
STATIONS_CSV = os.path.join(config.RAW_DIR, "stations.csv")


@dataclass
class StationMeta:
    network: str
    station: str
    latitude: float
    longitude: float
    elevation_m: float
    dist_km: float
    azimuth_deg: float

    @property
    def code(self) -> str:
        return f"{self.network}.{self.station}"


def load_inventory():
    return read_inventory(INV_PATH)


def load_raw_stream() -> Stream:
    return read(MSEED_PATH)


def load_station_meta() -> dict[str, StationMeta]:
    """One StationMeta per network.station (lat/lon/dist are channel-invariant)."""
    out: dict[str, StationMeta] = {}
    with open(STATIONS_CSV) as fh:
        for r in csv.DictReader(fh):
            code = f"{r['network']}.{r['station']}"
            if code in out:
                continue
            out[code] = StationMeta(
                network=r["network"], station=r["station"],
                latitude=float(r["latitude"]), longitude=float(r["longitude"]),
                elevation_m=float(r["elevation_m"]), dist_km=float(r["dist_km"]),
                azimuth_deg=float(r["azimuth_deg"]),
            )
    return out


def is_pressure(channel: str) -> bool:
    """Microbarometer/infrasound channels have band code with 'D' as 2nd char."""
    return len(channel) >= 2 and channel[1] == "D"


def is_seismic(channel: str) -> bool:
    return not is_pressure(channel)


def select_vertical_seismic(st: Stream) -> Stream:
    """One vertical seismic trace per station (prefer HHZ > BHZ > EHZ > *Z)."""
    by_station: dict[str, list] = {}
    for tr in st:
        if is_pressure(tr.stats.channel) or not tr.stats.channel.endswith("Z"):
            continue
        by_station.setdefault(f"{tr.stats.network}.{tr.stats.station}", []).append(tr)
    order = {"HHZ": 0, "BHZ": 1, "EHZ": 2}
    out = Stream()
    for code, traces in by_station.items():
        traces.sort(key=lambda t: (order.get(t.stats.channel, 9),
                                    -t.stats.sampling_rate,
                                    t.stats.location))
        out += traces[0]
    return out


def select_infrasound(st: Stream, prefer_band: str = "BDF") -> Stream:
    """One infrasound/pressure trace per station (prefer 40 sps BDF, else LDO)."""
    by_station: dict[str, list] = {}
    for tr in st:
        if not is_pressure(tr.stats.channel):
            continue
        by_station.setdefault(f"{tr.stats.network}.{tr.stats.station}", []).append(tr)
    out = Stream()
    for code, traces in by_station.items():
        traces.sort(key=lambda t: (0 if t.stats.channel == prefer_band else 1,
                                    -t.stats.sampling_rate, t.stats.location))
        out += traces[0]
    return out


def remove_response(st: Stream, inv=None, output: str = "VEL",
                    pre_filt=(0.05, 0.1, 18.0, 20.0)) -> Stream:
    """Return a response-removed copy. Seismic -> VEL/ACC/DISP; pressure -> 'DEF'
    (physical pressure units via the channel's response/sensitivity)."""
    if inv is None:
        inv = load_inventory()
    work = st.copy()
    work.detrend("demean")
    out = Stream()
    for tr in work:
        try:
            if is_pressure(tr.stats.channel):
                tr.remove_response(inventory=inv, output="DEF")
            else:
                tr.remove_response(inventory=inv, output=output, pre_filt=pre_filt)
            out += tr
        except Exception:
            # No matching response epoch; skip rather than fail the whole stream.
            continue
    return out


def event_window(pad_before_s: float = 0.0, pad_after_s: float = 0.0):
    """(t0_guess, win_start, win_end) UTCDateTimes for the event."""
    t0 = UTCDateTime(config.ORIGIN_TIME_PRIOR_UTC)
    return (t0,
            UTCDateTime(config.WINDOW_START_UTC) - pad_before_s,
            UTCDateTime(config.WINDOW_END_UTC) + pad_after_s)
