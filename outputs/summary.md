# Seismo-Acoustic Analysis of the 2026-05-30 New England Bolide - Summary

Event: USGS `us7000spjy` ("Sonic Boom - Eastern Massachusetts"),
flash ~2026-05-30T18:06:00Z (2:06 pm EDT). Independent open-data seismo-acoustic
analysis anchored by 9 inlier stations of a 16-station regional network
(seismic + infrasound out to ~270 km). The directionality analysis (Q2b)
additionally uses 44 `AM` RaspberryShake/RaspberryBoom citizen stations
recovered from the RaspberryShake datacenter (used for detection/amplitude
only, not the timing inversion).

## Q1 - Geometry: where was the source, and does it reconcile NASA vs. GOES?

**Best-fit acoustic source: 42.91N, 71.04W**
(bootstrap 1-sigma ~4.9 km N-S, 9.8 km E-W).

| reference | distance from acoustic source |
|---|---|
| NASA breakup (NE MA / SE NH) | **16 km** |
| USGS felt source | 16 km |
| GOES-19 flash ("the bays") | **117 km** |

The acoustic source sits essentially **on top of NASA's stated breakup region** and the
USGS felt centroid, and is **~117 km away from the GOES-19 "over the bays" flash**.
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

**Verdict: AIRBURST-DOMINATED, with a real southward-beamed component (see Q2b). The felt/heard pressure wave is best explained by a near-point, high-altitude fragmentation: the source localizes to a point and the double boom indicates a fragmentation cascade. It is NOT azimuthally isotropic - the wave was markedly stronger to the south (robust per-capita + citizen-sensor evidence). Real ERA5 winds do NOT support a southward wind-duct (see Q2b), so the bias most likely reflects forward-directed blast + ballistic energy along the ~N->S entry geometry rather than ducting.**

Evidence:
- acoustic residuals show only a MARGINAL azimuthal dipole (amp 18 s ~ timing scatter 16 s, 30% of variance, toward 86 deg); with a 155 deg azimuth gap (ocean) this is suggestive, not conclusive, of a ballistic component broadside to a ~N-S track
- DYFI felt pattern ~azimuthally isotropic after distance detrend (8% of variance) -> concentric, point-like felt field
- widely reported DOUBLE boom -> discrete fragmentation pulses (airburst cascade), not a single smooth sonic boom

The arrival times localize to a point and the widely reported **double boom**
indicates discrete fragmentation pulses - the hallmark of a near-point
**airburst**. The original distance-detrended DYFI isotropy test looked
concentric (8% azimuthal variance) but was effectively blind to the north (it
detrended by distance over mostly-southern boxes and could not see the absence
of northern reports); Q2b shows the field is in fact strongly direction-biased.

## Q2b - Directionality: the pressure wave was beamed SOUTH

The felt "center of mass" sits ~80 km south of the source, but that by itself is
a population artifact (more reporters live south). Two population-free tests show
the wave was **genuinely** stronger to the south:

- **Per-capita felt rate** (`population_vs_response.png`): normalizing DYFI
  responses by city population, the south reports **~30x more per capita** than
  the north. Matched pairs at equal distance and population settle it -
  Manchester NH vs Lowell MA (~116k each, ~35 km): **0 vs 8** responses;
  Portland ME vs Providence RI: **0 vs 33**. The deficit varies smoothly with
  azimuth (low to W/NW/N, high to S/SSE), not along the state line, so it is not
  a reporting-culture artifact.
- **Objective citizen sensors** (`beaming_test.png`, `station_coverage.png`):
  recovering the `AM` RaspberryShake/RaspberryBoom network (44 stations,
  including the previously unsampled near-north) gives an instrument test free of
  population. Among **identical** RaspberryShake sensors < 100 km, the airwave
  *is* detected to the north (RED1B, 37 km, apparent celerity 0.28 km/s) but is
  **~16x weaker** in seismic SNR than to the south (median SNR 4.8 N vs 78 S);
  near-field RaspberryBoom **infrasound is 100-1000x stronger** to the south
  (SNR 800-2300 at az 195-215) than anywhere N/W. So it is a strong *gradient*,
  not a hard shadow.

**Mechanism - does wind ducting explain it? Tested against REAL ERA5 winds.**
The wind-independent threshold holds (`raytrace_profiles.png`,
`raytrace_duct_vs_azimuth.png`): with US Standard Atmosphere 1976 temperature the
stratopause sound speed (330 m/s) is *below* the ground value (340 m/s), so a
stratospheric duct to the ground needs a **downwind wind >= ~10.5 m/s**. To test
the *actual* winds we pulled ERA5 reanalysis over the source
(`raytrace_era5_wind.png`, `raytrace_era5_duct_vs_azimuth.png`,
`raytrace_era5_profiles.png`). ERA5 lags real time by ~5 days, so the event day
was not yet published (latest 2026-05-27 12Z); we used the 3 most recent same-hour
analyses (**05-25/26/27 12Z**, ending 3 days before the event) as a synoptic proxy,
carrying the day-to-day spread as an error band.

The proxy winds were **zonal, not southward**: a strong tropospheric jet-stream
core (~49 m/s) toward the **east**, and a weak, summer-reversed stratosphere
(~6 m/s, *below* the 10.5 m/s threshold) toward the **WSW**. So the near-field
(tropospheric) duct points **east** and the far-field (stratospheric) duct points
**west**; **neither aims at the southern high-SNR stations** (beaming-alignment
score ~0). With these winds, simple ducting does **not** explain the southward
enhancement.

This reframes the mechanism. The robustly *observed* southward bias (per-capita
felt rate + identical-sensor citizen SNR) is therefore more likely dominated by
**source/trajectory geometry** - forward/downward-directed blast and ballistic
Mach-cone energy along the ~N->S entry - than by wind ducting, *unless* the
event-day winds differed materially from the 3-day proxy (tropospheric winds are
highly variable day to day, as the spread band shows). The strong **far-north**
infrasound returns (I63A 141 km, G62A 271 km) are not explained by the proxy
stratospheric duct (which points W) and remain consistent with azimuth-insensitive
**thermospheric** returns. Settling this needs the **event-day** winds: NOAA GFS
analysis is available now, and ERA5 will cover 2026-05-30 in ~3-5 days - re-running
`python -m src.fetch_era5 && python -m src.raytrace` auto-switches from the proxy
to the true day once published. (The parameterized southward-jet scenario in
`raytrace_paths.png` is kept only to illustrate what a ducting geometry *would*
look like; it is not the measured state.)

## Q3 - Energy: is "~300 tons of TNT" (0.3 kt) right?

NASA's 300 t came from GOES-19 GLM **optical** energy; CNEOS/JPL has no record, so the
three estimates below are fully independent **acoustic** cross-checks.

| method | yield |
|---|---|
| (D) infrasound period-yield (ReVelle 1997) | **65 t (range 53-65 t)** |
| (B) DYFI felt overpressure -> Collins (2005) airburst | **68 t (range 2-2908 t)** |
| (C) infrasound acoustic energy-flux bound | **1469 t (range 147-14694 t)** |
| **geometric mean** | **186 t** |

The acoustic geometric mean is **186 t** vs. NASA's 300 t
(ratio 0.62). The acoustic energy is **CONSISTENT with** the
300 t figure within the (large, factor-of-several) uncertainties of acoustic yield
methods. NASA's "~300 tons of TNT ... accounts for the loud noise" is corroborated.

## Figures
- `record_section.png` - acoustic moveout (~0.3 km/s, M1)
- `moveout_regression.png` - arrival time vs distance, emission ~ flash time
- `location_map.png` - source vs NASA/USGS/GOES with bootstrap cloud (M2)
- `classify.png` - isochrone azimuth test + felt isotropy (Q2)
- `energy_summary.png` - three acoustic yields vs 300 t (M3)
- `felt_heatmap.png` / `map.html` - felt-intensity heat map + source
- `population_vs_response.png` - per-capita felt rate vs N/S (Q2b)
- `beaming_test.png` - near-field detection/SNR by azimuth, AM network (Q2b)
- `station_coverage.png` - full acoustic coverage & SNR by azimuth (Q2b)
- `raytrace_profiles.png` / `raytrace_paths.png` / `raytrace_duct_vs_azimuth.png`
  - climatology/scenario ducting + the wind-independent duct threshold (Q2b)
- `raytrace_era5_wind.png` - **real** ERA5 u/v/speed/direction profile over the
  source (3-day synoptic proxy), with day-to-day spread band (Q2b)
- `raytrace_era5_duct_vs_azimuth.png` - **real**-wind duct lobes (tropospheric E,
  stratospheric W) vs observed station SNR -> neither points south (Q2b)
- `raytrace_era5_profiles.png` - ERA5 effective sound speed by direction (Q2b)
- `flash_to_boom_delay.png` - predicted vs reported ~300-360 s boom delay

## Caveats
Altitude/celerity/emission-time are degenerate with this station geometry; the event
occurred during a nor'easter (elevated infrasound wind/microbarom noise); felt-derived
overpressures and high-altitude blast scaling carry factor-of-several uncertainty.
The Q2b directionality *observation* is robust (per-capita felt rate +
identical-sensor citizen SNR agree on a strong southward gradient). The *mechanism*
is now constrained by **real ERA5 winds**, which do NOT support a southward duct:
the proxy winds are zonal (tropospheric jet E, weak reversed stratosphere W), so the
southward bias is attributed to source/trajectory geometry rather than ducting. The
key caveat is that ERA5 has not yet published the event day (~5-day latency), so the
ray-trace uses the 3 most recent same-hour analyses (05-25/26/27, ending 3 days
before the event) as a synoptic proxy; tropospheric winds vary day to day, so the
true event-day duct geometry could differ. Event-day NOAA GFS analysis (available
now) or ERA5 once 2026-05-30 is published would settle it; the fetch auto-upgrades
from proxy to the real day. ERA5 winds reach ~48 km (1 hPa); above that, temperature
falls back to USSA-76 and winds taper to zero, so thermospheric returns are not
modeled. RaspberryShake timing (NTP) is used only for detection/amplitude, never the
source inversion. Estimates are order-of-magnitude cross-checks, not precise
determinations.
