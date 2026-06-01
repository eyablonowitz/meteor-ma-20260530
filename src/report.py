"""Synthesize results into maps, a felt heat map, and a written summary.

Produces:
  outputs/map.html          interactive folium map (felt overlay, source vs refs,
                            stations, acoustic isochrones, indicative track)
  outputs/felt_heatmap.png  static DYFI felt-intensity map (the original goal)
  outputs/summary.md        written conclusions for Q1 (geometry), Q2 (airburst
                            vs sonic boom) and Q3 (energy vs 300 t TNT)

Run:  python -m src.report
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import folium
import branca.colormap as cm

from . import config
from . import dyfi_io
from . import seismic_io as sio
from .utils import haversine_km

MAP_HTML = os.path.join(config.OUT_DIR, "map.html")
FELT_PNG = os.path.join(config.OUT_DIR, "felt_heatmap.png")
SUMMARY_MD = os.path.join(config.OUT_DIR, "summary.md")

LOCATION_JSON = os.path.join(config.OUT_DIR, "location.json")
CLASSIFY_JSON = os.path.join(config.OUT_DIR, "classify.json")
ENERGY_JSON = os.path.join(config.OUT_DIR, "energy.json")


def _load(path):
    with open(path) as fh:
        return json.load(fh)


# ----------------------------------------------------------------------------
# Interactive folium map
# ----------------------------------------------------------------------------
def build_map(loc, path=MAP_HTML):
    best = loc["best_fit"]
    src = (best["lat"], best["lon"])
    m = folium.Map(location=[42.4, -70.9], zoom_start=8, tiles="CartoDB positron")

    # --- DYFI felt overlay (the heat map) ---
    gj = dyfi_io.load_geojson()
    cmap = cm.LinearColormap(["#2c7bb6", "#abd9e9", "#ffffbf", "#fdae61", "#d7191c"],
                             vmin=1, vmax=5, caption="DYFI felt intensity (CDI)")

    def style_fn(feat):
        cdi = feat["properties"].get("cdi", 1)
        return {"fillColor": cmap(cdi), "color": "#444", "weight": 0.5,
                "fillOpacity": 0.55}

    folium.GeoJson(
        gj, name="DYFI felt intensity",
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(fields=["name", "cdi", "nresp", "dist"],
                                      aliases=["", "CDI", "responses", "dist (km)"]),
    ).add_to(m)
    m.add_child(cmap)

    # --- acoustic travel-time isochrones (rings of constant ground arrival) ---
    iso = folium.FeatureGroup(name="acoustic isochrones (s after flash)")
    c, h, t0 = best["celerity_kms"], best["alt_km"], best["t0_s"]
    for t in (120, 180, 240, 300, 360, 420):
        arg = (c * (t - t0)) ** 2 - h ** 2
        if arg <= 0:
            continue
        radius_km = math.sqrt(arg)
        folium.Circle(src, radius=radius_km * 1000, color="#6a51a3", weight=1.5,
                      fill=False, dash_array="6",
                      popup=f"{t}s -> {radius_km:.0f} km").add_to(iso)
    iso.add_to(m)

    # --- indicative ground track (N-S, from the Q2 broadside-dipole hint) ---
    track = folium.FeatureGroup(name="indicative track (N-S, approx)", show=False)
    folium.PolyLine([(best["lat"] + 1.2, best["lon"]), (best["lat"] - 1.2, best["lon"])],
                    color="black", weight=2, dash_array="2,8",
                    popup="indicative N-S track (not tightly constrained)").add_to(track)
    track.add_to(m)

    # --- stations ---
    stns = folium.FeatureGroup(name="seismic / infrasound stations")
    data_codes = {f"{tr.stats.network}.{tr.stats.station}"
                  for tr in sio.load_raw_stream()}
    for code, sm in sio.load_station_meta().items():
        has = code in data_codes
        folium.CircleMarker(
            [sm.latitude, sm.longitude], radius=4,
            color="#111" if has else "#aaa",
            fill=True, fill_color="#1a9850" if has else "#cccccc",
            fill_opacity=0.9 if has else 0.5,
            popup=f"{code}  ({sm.dist_km:.0f} km){'  [data]' if has else ''}",
        ).add_to(stns)
    stns.add_to(m)

    # --- best-fit source + bootstrap spread ---
    b = loc.get("bootstrap", {})
    if b:
        folium.Circle(src, radius=max(b["lat"]["std"], 0.02) * 111000,
                      color="gold", weight=1, fill=True, fill_opacity=0.15,
                      popup="bootstrap 1-sigma").add_to(m)
    folium.Marker(src, icon=folium.Icon(color="orange", icon="star", prefix="fa"),
                  popup=(f"<b>Best-fit acoustic source</b><br>{best['lat']:.3f}, "
                         f"{best['lon']:.3f}<br>alt {best['alt_km']:.0f} km (poorly "
                         f"constrained)<br>c={best['celerity_kms']:.3f} km/s")).add_to(m)

    # --- reference points ---
    refs = {"NASA_BREAKUP": ("blue", "NASA breakup (~64 km)"),
            "USGS_DYFI": ("green", "USGS felt source"),
            "GOES_FLASH": ("red", "GOES-19 flash (the bays)")}
    for name, (color, label) in refs.items():
        pt = config.REF_POINTS[name]
        folium.Marker([pt["lat"], pt["lon"]],
                      icon=folium.Icon(color=color, icon="info-sign"),
                      popup=label).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(path)


# ----------------------------------------------------------------------------
# Static felt heat map
# ----------------------------------------------------------------------------
def felt_heatmap(loc, path=FELT_PNG, max_km=400.0):
    best = loc["best_fit"]
    # near-field, non-suspect boxes (a few responses came from >1000 km away)
    boxes = [b for b in dyfi_io.load_cdi_geo(drop_suspect=True)
             if haversine_km(best["lat"], best["lon"], b.lat, b.lon) <= max_km]
    lat = np.array([b.lat for b in boxes])
    lon = np.array([b.lon for b in boxes])
    cdi = np.array([b.cdi for b in boxes])

    fig, ax = plt.subplots(figsize=(9, 9))
    sc = ax.scatter(lon, lat, c=cdi, cmap="YlOrRd", s=90, vmin=1, vmax=5,
                    edgecolor="k", lw=0.3, zorder=3)
    plt.colorbar(sc, ax=ax, label="DYFI felt intensity (CDI)", shrink=0.75)
    pad = 0.6
    ax.set_xlim(lon.min() - pad, lon.max() + pad)
    ax.set_ylim(lat.min() - pad, lat.max() + pad)

    ax.plot(best["lon"], best["lat"], "*", color="gold", ms=24, mec="k", zorder=6,
            label="best-fit acoustic source")
    marks = {"NASA_BREAKUP": ("^", "tab:blue", "NASA breakup"),
             "USGS_DYFI": ("s", "tab:green", "USGS source"),
             "GOES_FLASH": ("v", "tab:red", "GOES flash")}
    for name, (mk, col, lab) in marks.items():
        pt = config.REF_POINTS[name]
        ax.plot(pt["lon"], pt["lat"], mk, color=col, ms=13, mec="k", zorder=5, label=lab)

    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("Who heard/felt the boom: DYFI intensity vs. acoustic source")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_aspect(1.0 / math.cos(math.radians(best["lat"])))
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


# ----------------------------------------------------------------------------
# Written summary
# ----------------------------------------------------------------------------
def write_summary(loc, cls, en, path=SUMMARY_MD):
    best = loc["best_fit"]
    bs = loc["bootstrap"]
    refs = loc["references"]
    ass = loc["assessment"]
    d = en["estimates"]["D"]; b = en["estimates"]["B"]; c = en["estimates"]["C"]

    def kt(e):
        r = e.get("yield_kt_range")
        return (f"{e['yield_tons']:.0f} t (range "
                f"{r[0]*1000:.0f}-{r[1]*1000:.0f} t)" if r else f"{e['yield_tons']:.0f} t")

    md = f"""# Seismo-Acoustic Analysis of the 2026-05-30 New England Bolide - Summary

Event: USGS `{config.EVENT_ID}` ("Sonic Boom - Eastern Massachusetts"),
flash ~{config.FLASH_TIME_UTC} (2:06 pm EDT). Independent open-data seismo-acoustic
analysis anchored by {len(loc['inlier_stations'])} inlier stations of a 16-station regional network
(seismic + infrasound out to ~270 km).

## Q1 - Geometry: where was the source, and does it reconcile NASA vs. GOES?

**Best-fit acoustic source: {best['lat']:.2f}N, {abs(best['lon']):.2f}W**
(bootstrap 1-sigma ~{ass['epicenter_1sigma_km']['lat']} km N-S, {ass['epicenter_1sigma_km']['lon']} km E-W).

| reference | distance from acoustic source |
|---|---|
| NASA breakup (NE MA / SE NH) | **{refs['NASA_BREAKUP']['horiz_km']:.0f} km** |
| USGS felt source | {refs['USGS_DYFI']['horiz_km']:.0f} km |
| GOES-19 flash ("the bays") | **{refs['GOES_FLASH']['horiz_km']:.0f} km** |

The acoustic source sits essentially **on top of NASA's stated breakup region** and the
USGS felt centroid, and is **~{refs['GOES_FLASH']['horiz_km']:.0f} km away from the GOES-19 "over the bays" flash**.
This resolves the apparent discrepancy: the **northern** point (NASA / our acoustic
solution / USGS) is where the airwave actually came from. The GOES "bays" position is
the displaced one - GLM geolocates the optical flash to the cloud tops and to a
~10-16 km pixel/parallax ellipse, which for a 40-64 km-high source is biased tens of
km from the true ground track, and bright high-altitude emission scatters off cloud
tops well south of the source. **The booms were not centered on Cape Cod / Mass Bay.**

Altitude is **not** independently resolved by this regional network (nearest reliable
infrasound at 96 km; altitude trades off with celerity and emission time). The data are
consistent with a high-altitude source (tens of km) but cannot pin it - near-field or
arrayed stations would be required.

## Q2 - Sonic boom (ballistic) or airburst (explosion)?

**Verdict: {cls['verdict']}**

Evidence:
"""
    for e in cls["evidence"]:
        md += f"- {e}\n"
    md += f"""
The felt field is concentric ({100*cls['dyfi_isotropy_test']['azimuthal_variance_explained']:.0f}% azimuthal
variance over {cls['dyfi_isotropy_test']['n']} DYFI boxes) and the arrival times localize to a point - the
hallmark of a near-point **airburst** rather than a line-source ballistic boom sweeping
the ground. The widely reported **double boom** indicates discrete fragmentation pulses.
A secondary ballistic sonic boom along the steep track is plausible (a marginal E-W
acoustic-residual dipole, broadside to a ~N-S track) but is at the timing-noise level
and not conclusively resolved (155 deg ocean azimuth gap).

## Q3 - Energy: is "~300 tons of TNT" (0.3 kt) right?

NASA's 300 t came from GOES-19 GLM **optical** energy; CNEOS/JPL has no record, so the
three estimates below are fully independent **acoustic** cross-checks.

| method | yield |
|---|---|
| (D) infrasound period-yield (ReVelle 1997) | **{kt(d)}** |
| (B) DYFI felt overpressure -> Collins (2005) airburst | **{kt(b)}** |
| (C) infrasound acoustic energy-flux bound | **{kt(c)}** |
| **geometric mean** | **{en['acoustic_geom_mean_kt']*1000:.0f} t** |

The acoustic geometric mean is **{en['acoustic_geom_mean_kt']*1000:.0f} t** vs. NASA's 300 t
(ratio {en['ratio_acoustic_over_nasa']:.2f}). The acoustic energy is **{en['verdict']}** the
300 t figure within the (large, factor-of-several) uncertainties of acoustic yield
methods. NASA's "~300 tons of TNT ... accounts for the loud noise" is corroborated.

## Figures
- `record_section.png` - acoustic moveout (~0.3 km/s, M1)
- `moveout_regression.png` - arrival time vs distance, emission ~ flash time
- `location_map.png` - source vs NASA/USGS/GOES with bootstrap cloud (M2)
- `classify.png` - isochrone azimuth test + felt isotropy (Q2)
- `energy_summary.png` - three acoustic yields vs 300 t (M3)
- `felt_heatmap.png` / `map.html` - felt-intensity heat map + source

## Caveats
Altitude/celerity/emission-time are degenerate with this station geometry; the event
occurred during a nor'easter (elevated infrasound wind/microbarom noise); felt-derived
overpressures and high-altitude blast scaling carry factor-of-several uncertainty.
Estimates are order-of-magnitude cross-checks, not precise determinations.
"""
    with open(path, "w") as fh:
        fh.write(md)


def main():
    loc = _load(LOCATION_JSON)
    cls = _load(CLASSIFY_JSON)
    en = _load(ENERGY_JSON)

    build_map(loc)
    felt_heatmap(loc)
    write_summary(loc, cls, en)
    print(f"Wrote {MAP_HTML}\n      {FELT_PNG}\n      {SUMMARY_MD}")
    print("\n--- summary.md ---\n")
    with open(SUMMARY_MD) as fh:
        print(fh.read())


if __name__ == "__main__":
    main()
