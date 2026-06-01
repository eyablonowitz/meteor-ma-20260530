# Seismo-Acoustic Analysis of the 2026-05-30 New England Bolide

On Saturday **2026-05-30 ~18:06 UTC (2:06 pm EDT)** a daylight bolide (large
meteor) fragmented over New England. A loud "double boom" and a pressure wave
that rattled buildings were reported across eastern Massachusetts and Rhode
Island. NASA put the breakup at ~40 mi (64 km) altitude over NE MA / SE NH and
estimated the energy at **~300 tons of TNT** (derived from GOES-19 GLM *optical*
energy). USGS logged it as event **`us7000spjy`** — type *"other event /
Sonic Boom"*, no earthquake — but the air-coupled pressure wave **was** recorded
on seismometers.

This project uses **open seismo-acoustic data** to independently answer:

1. **Geometry** — where was the acoustic source (lat/lon/**altitude**) and what
   was the trajectory? Resolves the apparent NASA ("NE MA / SE NH") vs. GOES
   ("over the bays") location discrepancy.
2. **What did people hear/feel** — a near-spherical **airburst blast** from the
   fragmentation, a **ballistic sonic boom** along the hypersonic track, or both?
3. **Energy** — is **300 tons of TNT** consistent with *acoustic* energy
   estimates that are independent of the GLM-optical number?

CNEOS/JPL's USG-sensor fireball database has **no record** for this event, so the
acoustic estimates here are fully independent of NASA's figure.

## Approach (acoustic-first)

Seismo-acoustic records are the anchor: GPS-disciplined timestamps (ms) and exact
station coordinates. Dense near-field stations (`LD.UNH` 33 km, `NE.DUNH` 38 km,
`PN.PPWIN` 43 km, `NE.BCX` 56 km, `NE.WES` 58 km, `IU.HRV` 63 km incl. an `LDO`
microbarometer) let us:

- Confirm an **acoustic** arrival (~0.30 km/s moveout, vs. >3 km/s seismic).
- Invert arrival times for **source lat/lon/altitude/t0** (resolves Q1, Q2).
- Estimate energy three independent ways and compare to 300 t TNT:
  - **Infrasound period-yield** (`IU.HRV`, `N4` `BDF` arrays).
  - **Blast-overpressure inversion** from USGS DYFI intensity-vs-distance.
  - **Seismic/acoustic amplitude** bound.

## Setup

ObsPy needs a CPython with published numpy/scipy wheels. Use a dedicated venv
(Python 3.11-3.13; the system default 3.14 may lack wheels):

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

## Usage

```bash
source venv/bin/activate

python -m src.fetch_seismic     # download MiniSEED + StationXML -> data/raw/
python -m src.fetch_dyfi        # download USGS DYFI products    -> data/dyfi/
python -m src.picks             # pick air-coupled arrivals; record-section plot
python -m src.locate            # invert for source lat/lon/alt/t0
python -m src.classify          # airburst vs. ballistic sonic boom
python -m src.energy            # 3 acoustic energy estimates vs. 300 t TNT
python -m src.report            # maps + figures + written summary -> outputs/
python -m src.videos            # flash-to-boom delay validation (+ best-effort social)

# Directionality / "is the southward beaming real?" (Q2b)
python -m src.felt_population   # per-capita felt rate vs population (N/S deficit)
python -m src.refetch_acoustic  # audit datacenters; recover AM citizen-network data
python -m src.beaming_test      # near-field detection/SNR by azimuth (AM-to-AM)
python -m src.station_coverage  # full coverage & SNR by azimuth (needs beaming_test)
python -m src.fetch_era5        # REAL ERA5 winds over the source (needs ~/.cdsapirc)
python -m src.raytrace          # effective-sound-speed ducting: climatology + ERA5
```

> `fetch_era5` needs a free Copernicus CDS account: put your endpoint + Personal
> Access Token in `~/.cdsapirc` and accept the *"Licence to use Copernicus
> Products"* on the dataset page. ERA5 lags real time ~5 days, so for a just-happened
> event `fetch_era5` auto-falls back to the most recent same-hour analyses as a
> synoptic proxy (recorded in `data/raw/era5_meta.json`); once the event day is
> published it uses the true day. If ERA5 is absent, `raytrace` runs the
> climatology scenario only.

## Layout

```
src/config.py        event constants, networks/channels, physical constants
src/utils.py         geodesy helpers (distance, slant range, azimuth)
src/fetch_seismic.py FDSN waveform + inventory download
src/fetch_dyfi.py    USGS DYFI product download
src/picks.py         bandpass + STA/LTA arrival picks, record section
src/locate.py        grid/optimizer source localization
src/classify.py      airburst vs. ballistic discrimination
src/energy.py        infrasound, DYFI-blast, acoustic-flux yields
src/report.py        folium maps, summary figures, conclusions
src/videos.py        flash-to-boom delay validation; best-effort social fetch
src/felt_population.py  per-capita felt-rate vs population (Q2b directionality)
src/refetch_acoustic.py datacenter audit + AM citizen-network recovery
src/beaming_test.py  near-field detection/SNR by azimuth (AM-to-AM control)
src/station_coverage.py full acoustic coverage & SNR by azimuth (incl. AM)
src/fetch_era5.py    ERA5 reanalysis fetch via Copernicus CDS (event-day or proxy)
src/era5_profile.py  ERA5 NetCDF -> source T(z)/u(z)/v(z) on geometric height
src/raytrace.py      effective-sound-speed ducting (USSA-76 climatology + ERA5)
src/seismic_io.py    shared loaders + instrument-response removal
src/dyfi_io.py       DYFI product parsers
data/raw/            MiniSEED + StationXML (gitignored)
data/dyfi/           DYFI geojson/json/txt (gitignored)
outputs/             figures, maps, summary.md
```

## Caveats

Anecdote-derived overpressures, daytime GLM detection limits, and high-altitude
blast scaling all carry factor-of-several uncertainty. Estimates are reported
with error bars; the aim is order-of-magnitude cross-checks, not a precise yield.
