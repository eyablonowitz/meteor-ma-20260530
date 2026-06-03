# Seismo-Acoustic Analysis of the 2026-05-30 New England Bolide

On Saturday **2026-05-30 ~18:06 UTC (2:06 pm EDT)** a daylight bolide (large
meteor) fragmented over New England. A loud "double boom" and a pressure wave
that rattled buildings were reported across eastern Massachusetts and Rhode
Island. NASA put the breakup at 40 mi (64 km) altitude over NE MA / SE NH and
estimated the energy at 300 tons of TNT (believed to be derived from GOES-19 GLM *optical*
energy). USGS logged it as event `**us7000spjy`** — type *"other event /
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

## Story and Video

In addition to the data analysis, this repo was created to be a learning tool.
The goal was to learn about the meteor itself, but also techniques to use AI-assisted
coding in the anaysis. See [story.md](STORY.md) for a narrative take on how this unfolded.

Along similiar lines, this repo also contains code to build a learning video aimed middle/high school students.
See [video/README.md.](video/README.md) for more details. 
The resulting [video can be found on YouTube](https://www.youtube.com/watch?v=zvLkeRWiATA).

## Motivation

I heard and felt the boom as did many of my friends and neighbors.  I'm a software 
engineer not a scientist. But some of the conflicting information that came out got 
me really interested in digging in.  For example, did the meteor explode over Cape Cod 
Bay as many asserted based on widely circulated satellite data?  Or over the MA-NH 
eastern border as NASA tweeted:
https://x.com/NASASpaceAlerts/status/2060854183155106193

And how did NASA figure out that the explosion was the equivalent of 300 tons of TNT?

## AI use

This work was also a chance for me to extend my AI coding skills in new directions 
(science and video production). AI (mostly Claude Opus 4.8 in Cursor) played a big part in this. 
I leaned heavily on AI to help me work through areas of the science I did not understand.
In other cases, I was primarily driving the inquiry with the AI just acting as a code assistant.
Either way, often AI would do some analysis, draw some conclusions, but leave some critical question
unexplored. So the process required my critical thinking to ask those questions and push the analysis
forward. 

It was similar with the video. I sketched out the script, but AI helped me turn it into a 
storyboard. And then we iterated in the script/storyboard until we were ready to write 
some code. Once we were able to produce a rough-cut video, we went through several rapid 
stages of iteration to get to the script, animations that you see now. The whole thing 
took several hours. But it would have taken weeks without AI.

 All-in-all, this really felt like collaboration with AI. I'm genuinely conflicted about how 
 much pride and ownership to feel in the final product. So in addition to this being a 
 learning / teaching tool about a meteor, my hope is that it can also stimulate discussion 
 about AI in amateur/student science and creative work.

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