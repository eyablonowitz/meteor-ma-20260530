"""Recover missing near-field acoustic data and audit for other reliable sources.

Motivation: the near-field stations to the N/W of the epicenter (esp. LD.UNH at
33 km due north and NE.DUNH at 38 km) returned metadata but NO waveforms in the
primary IRIS download - exactly the stations that could test the apparent
northern 'shadow'. This module:

  1) AUDIT - queries every relevant FDSN datacenter (IRIS, EarthScope, USGS,
     RaspberryShake) and extra networks (AM citizen seismo/infrasound) for all
     stations within the search radius, reporting near-field coverage by azimuth
     and which datacenter actually holds each station's data.
  2) RECOVER - for stations we don't yet have waveforms for, tries each
     datacenter (and the federator) in turn, then merges anything recovered into
     data/raw/{waveforms_raw.mseed, inventory.xml, stations.csv}.

Run:  python -m src.refetch_acoustic
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

from obspy import UTCDateTime, Stream, read, read_inventory
from obspy.clients.fdsn import Client
from obspy.clients.fdsn.header import FDSNException

from . import config
from .utils import azimuth_deg, haversine_km
from .fetch_seismic import (ALL_CHANNELS, INV_PATH, MSEED_PATH, STATIONS_CSV,
                            write_stations_csv)

PICKS_CSV = os.path.join(config.OUT_DIR, "picks.csv")

# Datacenters to try, in priority order. RASPISHAKE serves the AM citizen network
# (RaspberryShake seismographs + RaspberryBoom infrasound) which is dense in
# populated areas and our best shot at near-field N/W coverage.
DATACENTERS = ["IRIS", "EARTHSCOPE", "USGS", "RASPISHAKE"]

# Networks to *discover*: our originals + AM (citizen). AM is queried only at
# RASPISHAKE/iris.
DISCOVER_NETWORKS = config.NETWORKS + ["AM"]

# Slightly broadened pressure/infrasound channel set (RaspberryBoom uses *DF;
# some microbarometers use EDF/GDF/CDF).
CHANNELS = ALL_CHANNELS + ",EDF,GDF,CDF,DDF"

NEAR_KM = 100.0
SRC_LAT = config.REF_POINTS["USGS_DYFI"]["lat"]
SRC_LON = config.REF_POINTS["USGS_DYFI"]["lon"]


def _client(name):
    try:
        return Client(name, timeout=120)
    except Exception as exc:  # pragma: no cover
        print(f"  [{name}] client init failed: {exc}", file=sys.stderr)
        return None


def have_stations_from_disk():
    """(net,sta) we already hold usable waveforms for (from picks.csv + mseed)."""
    have = set()
    if os.path.exists(PICKS_CSV):
        with open(PICKS_CSV) as fh:
            for r in csv.DictReader(fh):
                have.add((r["network"], r["station"]))
    if os.path.exists(MSEED_PATH):
        try:
            for tr in read(MSEED_PATH):
                have.add((tr.stats.network, tr.stats.station))
        except Exception:
            pass
    return have


def is_pressure(cha_code: str) -> bool:
    return len(cha_code) >= 2 and cha_code[1] in ("D",)


def discover():
    """Map (net,sta)->{dist,az,datacenters,seismic,pressure} across datacenters."""
    t1, t2 = UTCDateTime(config.WINDOW_START_UTC), UTCDateTime(config.WINDOW_END_UTC)
    found = {}
    for dc in DATACENTERS:
        cl = _client(dc)
        if cl is None:
            continue
        nets = DISCOVER_NETWORKS if dc in ("IRIS", "EARTHSCOPE", "RASPISHAKE") \
            else config.NETWORKS
        try:
            inv = cl.get_stations(
                network=",".join(nets), channel=CHANNELS,
                latitude=SRC_LAT, longitude=SRC_LON,
                maxradius=config.SEARCH_RADIUS_DEG,
                starttime=t1, endtime=t2, level="channel")
        except Exception as exc:
            print(f"  [{dc}] inventory query failed: {exc}", file=sys.stderr)
            continue
        nsta = 0
        for net in inv:
            for sta in net:
                key = (net.code, sta.code)
                d = haversine_km(sta.latitude, sta.longitude, SRC_LAT, SRC_LON)
                az = azimuth_deg(SRC_LAT, SRC_LON, sta.latitude, sta.longitude)
                rec = found.setdefault(key, {
                    "dist": d, "az": az, "lat": sta.latitude, "lon": sta.longitude,
                    "datacenters": set(), "seismic": False, "pressure": False})
                rec["datacenters"].add(dc)
                for cha in sta:
                    if is_pressure(cha.code):
                        rec["pressure"] = True
                    else:
                        rec["seismic"] = True
                nsta += 1
        print(f"  [{dc}] inventory: {nsta} station-epochs "
              f"(networks {','.join(nets)})")
    return found


def quad(az):
    az %= 360
    return ("N" if az < 45 or az >= 315 else "E" if az < 135 else
            "S" if az < 225 else "W")


def recover(targets):
    """Try each datacenter (+ federator) for the target (net,sta) waveforms."""
    t1, t2 = UTCDateTime(config.WINDOW_START_UTC), UTCDateTime(config.WINDOW_END_UTC)
    recovered = Stream()
    got = set()
    for dc in DATACENTERS:
        remaining = [k for k in targets if k not in got]
        if not remaining:
            break
        cl = _client(dc)
        if cl is None:
            continue
        bulk = [(n, s, "*", CHANNELS, t1, t2) for (n, s) in remaining]
        try:
            st = cl.get_waveforms_bulk(bulk)
        except FDSNException:
            st = Stream()
            for n, s in remaining:
                try:
                    st += cl.get_waveforms(n, s, "*", CHANNELS, t1, t2)
                except FDSNException:
                    continue
        except Exception as exc:
            print(f"  [{dc}] waveform query error: {exc}", file=sys.stderr)
            continue
        new = {(tr.stats.network, tr.stats.station) for tr in st}
        new -= got
        if new:
            print(f"  [{dc}] recovered {len(st)} traces; new stations: "
                  + ", ".join(f"{n}.{s}" for n, s in sorted(new)))
            recovered += st
            got |= new
    # federator last resort
    leftover = [k for k in targets if k not in got]
    if leftover:
        try:
            from obspy.clients.fdsn import RoutingClient
            rc = RoutingClient("iris-federator")
            bynet = defaultdict(set)
            for n, s in leftover:
                bynet[n].add(s)
            for n, stas in bynet.items():
                try:
                    st = rc.get_waveforms(network=n, station=",".join(sorted(stas)),
                                          location="*", channel=CHANNELS,
                                          starttime=t1, endtime=t2)
                    new = {(tr.stats.network, tr.stats.station) for tr in st} - got
                    if new:
                        print(f"  [federator] recovered new stations: "
                              + ", ".join(f"{a}.{b}" for a, b in sorted(new)))
                        recovered += st
                        got |= new
                except Exception:
                    continue
        except Exception as exc:
            print(f"  federator unavailable: {exc}", file=sys.stderr)
    return recovered, got


def merge_inventory(new_keys):
    """Fetch channel-level response metadata for newly recovered stations and
    merge into inventory.xml so downstream response removal works."""
    t1, t2 = UTCDateTime(config.WINDOW_START_UTC), UTCDateTime(config.WINDOW_END_UTC)
    inv = read_inventory(INV_PATH) if os.path.exists(INV_PATH) else None
    bynet = defaultdict(set)
    for n, s in new_keys:
        bynet[n].add(s)
    for dc in DATACENTERS:
        if not bynet:
            break
        cl = _client(dc)
        if cl is None:
            continue
        for n in list(bynet):
            try:
                add = cl.get_stations(network=n, station=",".join(sorted(bynet[n])),
                                      channel=CHANNELS, starttime=t1, endtime=t2,
                                      level="response")
                inv = add if inv is None else inv + add
                del bynet[n]
            except Exception:
                continue
    if inv is not None:
        inv.write(INV_PATH, format="STATIONXML")
    return inv


def main():
    have = have_stations_from_disk()
    print(f"Already hold waveforms for {len(have)} stations.\n")

    print("=== AUDIT: all acoustic stations within radius, by datacenter ===")
    found = discover()
    print(f"\nDiscovered {len(found)} unique stations across "
          f"{len(DATACENTERS)} datacenters.")

    # Anything new we didn't even have in metadata before?
    prior_meta = set()
    if os.path.exists(STATIONS_CSV):
        with open(STATIONS_CSV) as fh:
            for r in csv.DictReader(fh):
                prior_meta.add((r["network"], r["station"]))
    brand_new = {k for k in found if k not in prior_meta}
    print(f"Stations NOT in our previous metadata (newly discovered): "
          f"{len(brand_new)}")

    print(f"\nNEAR-FIELD (< {NEAR_KM:.0f} km) coverage by azimuth "
          "(* = we lack waveforms):")
    near = sorted([(k, v) for k, v in found.items() if v["dist"] < NEAR_KM],
                  key=lambda kv: kv[1]["az"])
    print(f"  {'sta':12s} {'dist':>6} {'az':>5} {'q':>2} {'kind':>10} "
          f"{'datacenters':>22}  have?")
    for k, v in near:
        kind = ("press+seis" if v["pressure"] and v["seismic"]
                else "infrasound" if v["pressure"] else "seismic")
        flag = "" if k in have else " *"
        print(f"  {k[0]+'.'+k[1]:12s} {v['dist']:6.1f} {v['az']:5.0f} "
              f"{quad(v['az']):>2} {kind:>10} {','.join(sorted(v['datacenters'])):>22}"
              f"  {'yes' if k in have else 'NO'}{flag}")

    # Recover everything within radius we don't have, prioritizing near-field.
    targets = sorted([k for k in found if k not in have],
                     key=lambda k: found[k]["dist"])
    print(f"\n=== RECOVER: attempting {len(targets)} stations lacking waveforms "
          "===")
    recovered, got = recover(targets)

    if not got:
        print("\nNo additional waveforms recovered. The missing stations have no "
              "open waveform holdings at any queried datacenter for this window.")
    else:
        print(f"\nRecovered waveforms for {len(got)} stations: "
              + ", ".join(f"{n}.{s}" for n, s in sorted(got)))
        # Save recovered data to its own file FIRST (crash-safe), splitting any
        # masked (gappy) traces since MSEED can't store masked arrays.
        recovered_clean = recovered.copy().split()
        recovered_clean.write(os.path.join(config.RAW_DIR, "waveforms_recovered.mseed"),
                              format="MSEED")
        # merge into the main mseed
        base = read(MSEED_PATH) if os.path.exists(MSEED_PATH) else Stream()
        base += recovered
        base.merge(method=1, fill_value=None)
        base = base.split()   # drop masked arrays produced by gap-filling merge
        base.write(MSEED_PATH, format="MSEED")
        inv = merge_inventory(got)
        if inv is not None:
            write_stations_csv(inv)
        print(f"Merged into {MSEED_PATH} and refreshed inventory + stations.csv.")
        near_nw = [(n, s) for (n, s) in got
                   if quad(found[(n, s)]["az"]) in ("N", "W")
                   and found[(n, s)]["dist"] < NEAR_KM]
        if near_nw:
            print("  >>> Includes NEAR-FIELD N/W stations (diagnostic for the "
                  "northern shadow): "
                  + ", ".join(f"{n}.{s}" for n, s in near_nw))
            print("  Next: re-run `python -m src.picks` then `src.station_coverage`.")


if __name__ == "__main__":
    main()
