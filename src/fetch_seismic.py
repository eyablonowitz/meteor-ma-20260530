"""Download seismic + infrasound waveforms and station metadata via FDSN.

Pulls broadband/strong-motion seismic and microbarometer/infrasound channels for
stations within ~290 km of the USGS source, over the event time window, and
saves:
  data/raw/inventory.xml        StationXML (response-level)
  data/raw/waveforms_raw.mseed  raw MiniSEED (counts)
  data/raw/stations.csv         per-(net,sta,loc,cha) lat/lon/dist/azimuth table

Run:  python -m src.fetch_seismic
"""
from __future__ import annotations

import csv
import os
import sys

from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNException

from . import config
from .utils import azimuth_deg, haversine_km

INV_PATH = os.path.join(config.RAW_DIR, "inventory.xml")
MSEED_PATH = os.path.join(config.RAW_DIR, "waveforms_raw.mseed")
STATIONS_CSV = os.path.join(config.RAW_DIR, "stations.csv")

ALL_CHANNELS = config.SEISMIC_CHANNELS + "," + config.PRESSURE_CHANNELS


def get_client(name: str | None = None) -> Client:
    return Client(name or config.FDSN_CLIENT, timeout=120)


def fetch_inventory(client: Client) -> "obspy.Inventory":
    """Channel-level inventory within the search radius for the time window."""
    return client.get_stations(
        network=",".join(config.NETWORKS),
        channel=ALL_CHANNELS,
        latitude=config.SEARCH_CENTER_LAT,
        longitude=config.SEARCH_CENTER_LON,
        maxradius=config.SEARCH_RADIUS_DEG,
        starttime=UTCDateTime(config.WINDOW_START_UTC),
        endtime=UTCDateTime(config.WINDOW_END_UTC),
        level="response",
    )


def _bulk_from_inventory(inv, t1: UTCDateTime, t2: UTCDateTime):
    bulk, seen = [], set()
    for net in inv:
        for sta in net:
            for cha in sta:
                key = (net.code, sta.code, cha.location_code, cha.code)
                if key in seen:
                    continue
                seen.add(key)
                loc = cha.location_code if cha.location_code else ""
                bulk.append((net.code, sta.code, loc, cha.code, t1, t2))
    return bulk


def fetch_waveforms(client: Client, inv, t1: UTCDateTime, t2: UTCDateTime):
    """Bulk waveform download; fall back to per-request on bulk failure."""
    bulk = _bulk_from_inventory(inv, t1, t2)
    try:
        st = client.get_waveforms_bulk(bulk)
        if len(st):
            return st
        print("  bulk returned 0 traces; falling back to per-request", file=sys.stderr)
    except FDSNException as exc:
        print(f"  bulk request failed ({exc}); per-request fallback", file=sys.stderr)

    from obspy import Stream
    st = Stream()
    for net, sta, loc, cha, a, b in bulk:
        try:
            st += client.get_waveforms(net, sta, loc, cha, a, b)
        except FDSNException:
            continue
    return st


def fetch_missing_via_federator(inv, have_stations, t1, t2):
    """Best-effort recovery of stations whose data isn't at the primary node.

    Uses the EarthScope/IRIS federator to route per-network requests for any
    station present in the metadata but missing from the primary download.
    """
    from obspy import Stream
    try:
        from obspy.clients.fdsn import RoutingClient
        rc = RoutingClient("iris-federator")
    except Exception as exc:  # pragma: no cover - environment dependent
        print(f"  federator unavailable ({exc}); skipping supplement", file=sys.stderr)
        return Stream()

    missing = {}
    for net in inv:
        for sta in net:
            if (net.code, sta.code) in have_stations:
                continue
            missing.setdefault(net.code, set()).add(sta.code)
    if not missing:
        return Stream()

    print(f"  federator supplement for {sum(len(v) for v in missing.values())} "
          f"missing stations: "
          + ", ".join(f"{n}({len(s)})" for n, s in missing.items()))
    st = Stream()
    for net, stas in missing.items():
        try:
            st += rc.get_waveforms(
                network=net, station=",".join(sorted(stas)),
                location="*", channel=ALL_CHANNELS,
                starttime=t1, endtime=t2)
        except Exception:
            continue
    return st


def _channel_rows(inv):
    """Yield dicts of channel metadata joined with distance to the source."""
    src_lat = config.REF_POINTS["USGS_DYFI"]["lat"]
    src_lon = config.REF_POINTS["USGS_DYFI"]["lon"]
    for net in inv:
        for sta in net:
            for cha in sta:
                dist = haversine_km(cha.latitude, cha.longitude, src_lat, src_lon)
                yield {
                    "network": net.code,
                    "station": sta.code,
                    "location": cha.location_code or "",
                    "channel": cha.code,
                    "latitude": round(cha.latitude, 5),
                    "longitude": round(cha.longitude, 5),
                    "elevation_m": cha.elevation,
                    "sample_rate": cha.sample_rate,
                    "dist_km": round(dist, 2),
                    "azimuth_deg": round(azimuth_deg(src_lat, src_lon,
                                                     cha.latitude, cha.longitude), 1),
                }


def write_stations_csv(inv, path: str = STATIONS_CSV):
    rows = sorted(_channel_rows(inv), key=lambda r: (r["dist_km"], r["channel"]))
    fields = ["network", "station", "location", "channel", "latitude", "longitude",
              "elevation_m", "sample_rate", "dist_km", "azimuth_deg"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    t1, t2 = UTCDateTime(config.WINDOW_START_UTC), UTCDateTime(config.WINDOW_END_UTC)
    print(f"FDSN client: {config.FDSN_CLIENT}")
    print(f"Window: {t1} -> {t2}")
    print(f"Center: {config.SEARCH_CENTER_LAT}, {config.SEARCH_CENTER_LON} "
          f"r<={config.SEARCH_RADIUS_DEG} deg")

    client = get_client()
    print("Fetching station inventory...")
    inv = fetch_inventory(client)
    inv.write(INV_PATH, format="STATIONXML")
    rows = write_stations_csv(inv)

    n_sta = len({(r["network"], r["station"]) for r in rows})
    n_press = sum(1 for r in rows if r["channel"][1:2] == "D")
    print(f"  {len(rows)} channels across {n_sta} stations "
          f"({n_press} pressure/infrasound channels)")
    if rows:
        nearest = sorted({(r["network"], r["station"], r["dist_km"]) for r in rows},
                         key=lambda x: x[2])[:8]
        print("  nearest stations:", ", ".join(f"{n}.{s} {d}km" for n, s, d in nearest))

    print("Fetching waveforms...")
    st = fetch_waveforms(client, inv, t1, t2)
    have = {(tr.stats.network, tr.stats.station) for tr in st}
    print(f"  primary node: {len(st)} traces from {len(have)} stations")

    supplement = fetch_missing_via_federator(inv, have, t1, t2)
    if len(supplement):
        extra = {(tr.stats.network, tr.stats.station) for tr in supplement} - have
        print(f"  federator added {len(supplement)} traces "
              f"({len(extra)} new stations: {', '.join(f'{n}.{s}' for n, s in sorted(extra))})")
        st += supplement

    if not len(st):
        print("  WARNING: no waveform data returned.", file=sys.stderr)
        sys.exit(2)
    st.merge(method=1, fill_value=None)
    st.write(MSEED_PATH, format="MSEED")
    got = sorted({f"{tr.stats.network}.{tr.stats.station}" for tr in st})
    print(f"  {len(st)} traces from {len(got)} stations -> {MSEED_PATH}")
    print(f"  stations with data: {', '.join(got)}")


if __name__ == "__main__":
    main()
