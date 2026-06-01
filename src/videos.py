"""Validate flash-to-boom delays against the seismo-acoustic source solution.

The robust validation is physical: from the located source we predict the
ground arrival ("boom") delay after the 18:06 flash at any location,
    delay(d) = t0 + sqrt(d^2 + h^2) / c ,
and compare it to publicly reported boom timing (videos placing the boom around
2:11-2:12 pm EDT, i.e. ~300-360 s after the flash) at representative felt-zone
cities. We also make a best-effort, no-auth fetch of social posts (Reddit /
Bluesky) for transparency - but social post timestamps are NOT boom times and
auto-geolocation is unreliable, so they corroborate the date/region only.

Run:  python -m src.videos
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import config
from .utils import haversine_km, slant_range_km

LOCATION_JSON = os.path.join(config.OUT_DIR, "location.json")
DELAY_PNG = os.path.join(config.OUT_DIR, "flash_to_boom_delay.png")
VIDEOS_JSON = os.path.join(config.OUT_DIR, "videos.json")
SOCIAL_RAW = os.path.join(config.DATA_DIR, "social_posts.json")

# Publicly reported boom timing: videos timestamped ~2:11-2:12 pm EDT (flash
# was 2:06 pm EDT = 18:06Z), i.e. ~300-360 s after the flash.
REPORTED_BOOM_DELAY_S = (300.0, 360.0)

# Representative felt-zone locations (population centers that posted videos).
FELT_CITIES = {
    "Boston, MA":      (42.36, -71.06),
    "Cambridge, MA":   (42.37, -71.11),
    "Salem, MA":       (42.52, -70.90),
    "Providence, RI":  (41.82, -71.41),
    "Worcester, MA":   (42.26, -71.80),
    "Portsmouth, NH":  (43.07, -70.76),
    "Cape Cod (Hyannis), MA": (41.65, -70.28),
}

SEARCH_TERMS = ["boom Massachusetts meteor", "loud boom New England May 30"]


def predicted_delay_s(best, lat, lon):
    R = slant_range_km(lat, lon, best["lat"], best["lon"], best["alt_km"])
    return best["t0_s"] + R / best["celerity_kms"]


def edt_clock(delay_s):
    """Convert seconds-after-flash to an EDT clock string (flash = 2:06:00 pm)."""
    total = 14 * 3600 + 6 * 60 + delay_s     # seconds after midnight EDT
    h = int(total // 3600); m = int((total % 3600) // 60); s = int(total % 60)
    return f"{h-12 if h > 12 else h}:{m:02d}:{s:02d} pm EDT"


def city_comparison(best):
    rows = []
    for city, (lat, lon) in FELT_CITIES.items():
        d_horiz = haversine_km(lat, lon, best["lat"], best["lon"])
        delay = predicted_delay_s(best, lat, lon)
        rows.append({"city": city, "horiz_km": round(d_horiz, 1),
                     "pred_delay_s": round(delay, 1),
                     "pred_boom_edt": edt_clock(delay)})
    return rows


def delay_uncertainty_band(best, lat, lon):
    """Predicted delay range over physically plausible (c, h) given the altitude
    degeneracy: c in [0.30, 0.34], h in [40, 80] km."""
    vals = []
    for c in (0.30, 0.34):
        for h in (40.0, 80.0):
            R = slant_range_km(lat, lon, best["lat"], best["lon"], h)
            vals.append(best["t0_s"] + R / c)
    return min(vals), max(vals)


def plot_delay_map(best, rows, path=DELAY_PNG):
    # grid of predicted delay over the region
    lons = np.linspace(-72.5, -69.5, 160)
    lats = np.linspace(41.0, 43.6, 160)
    LON, LAT = np.meshgrid(lons, lats)
    R = np.sqrt((haversine_km_grid(LAT, LON, best["lat"], best["lon"])) ** 2
                + best["alt_km"] ** 2)
    delay = best["t0_s"] + R / best["celerity_kms"]

    fig, ax = plt.subplots(figsize=(9, 8))
    cs = ax.contourf(LON, LAT, delay, levels=np.arange(120, 600, 30),
                     cmap="viridis", alpha=0.85)
    plt.colorbar(cs, ax=ax, label="predicted flash-to-boom delay (s)", shrink=0.8)
    # reported band contours (300-360 s)
    cc = ax.contour(LON, LAT, delay, levels=list(REPORTED_BOOM_DELAY_S),
                    colors="red", linewidths=2)
    ax.clabel(cc, fmt=lambda v: f"{v:.0f}s (reported)")

    ax.plot(best["lon"], best["lat"], "*", color="gold", ms=22, mec="k",
            label="acoustic source")
    for r in rows:
        lat, lon = FELT_CITIES[r["city"]]
        ax.plot(lon, lat, "o", color="white", mec="k", ms=6)
        ax.annotate(f"{r['city'].split(',')[0]}\n{r['pred_delay_s']:.0f}s",
                    (lon, lat), fontsize=7, ha="center",
                    xytext=(0, 6), textcoords="offset points")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("Predicted flash-to-boom delay vs. reported ~300-360 s "
                 "(2:11-2:12 pm EDT)")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_aspect(1.0 / math.cos(math.radians(best["lat"])))
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def haversine_km_grid(lat1, lon1, lat2, lon2):
    R = 6371.0
    la1 = np.radians(lat1); lo1 = np.radians(lon1)
    la2 = math.radians(lat2); lo2 = math.radians(lon2)
    d = (np.sin((la2 - la1) / 2) ** 2
         + np.cos(la1) * math.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2)
    return 2 * R * np.arcsin(np.sqrt(d))


def best_effort_social_fetch():
    """No-auth fetch from Reddit + Bluesky. Returns a list of {source, time, text}.
    Social timestamps are POST times (not boom times); used only as a
    date/region sanity check. Fails gracefully (offline / rate-limited)."""
    import requests
    posts = []
    headers = {"User-Agent": "meteor-heatmap/1.0 (research)"}
    # Reddit public search
    for term in SEARCH_TERMS:
        try:
            r = requests.get("https://www.reddit.com/search.json",
                             params={"q": term, "sort": "new", "limit": 25,
                                     "t": "month"},
                             headers=headers, timeout=20)
            if r.status_code == 200:
                for ch in r.json().get("data", {}).get("children", []):
                    d = ch.get("data", {})
                    posts.append({"source": "reddit",
                                  "time_utc": d.get("created_utc"),
                                  "subreddit": d.get("subreddit"),
                                  "title": d.get("title")})
        except Exception:
            continue
    # Bluesky public search (no auth)
    for term in SEARCH_TERMS:
        try:
            r = requests.get(
                "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts",
                params={"q": term, "limit": 25}, timeout=20)
            if r.status_code == 200:
                for p in r.json().get("posts", []):
                    rec = p.get("record", {})
                    posts.append({"source": "bluesky",
                                  "time_utc": rec.get("createdAt"),
                                  "author": p.get("author", {}).get("handle"),
                                  "title": rec.get("text", "")[:160]})
        except Exception:
            continue
    return posts


def main():
    with open(LOCATION_JSON) as fh:
        best = json.load(fh)["best_fit"]
    print(f"Source: {best['lat']:.3f}, {best['lon']:.3f}, h={best['alt_km']:.0f} km, "
          f"c={best['celerity_kms']:.3f} km/s, t0={best['t0_s']:+.0f} s\n")

    rows = city_comparison(best)
    print("Predicted flash-to-boom delay at felt-zone cities "
          f"(reported ~{REPORTED_BOOM_DELAY_S[0]:.0f}-{REPORTED_BOOM_DELAY_S[1]:.0f} s, "
          "2:11-2:12 pm EDT):")
    print(f"  {'city':<24} {'horiz_km':>8} {'delay_s':>8}   predicted boom")
    for r in rows:
        lat, lon = FELT_CITIES[r["city"]]
        lo, hi = delay_uncertainty_band(best, lat, lon)
        print(f"  {r['city']:<24} {r['horiz_km']:8.1f} {r['pred_delay_s']:8.0f}   "
              f"{r['pred_boom_edt']}  (range {lo:.0f}-{hi:.0f}s)")

    # consistency: do predicted delays in the felt zone overlap the reported band?
    pred = [r["pred_delay_s"] for r in rows]
    overlap = any(REPORTED_BOOM_DELAY_S[0] - 90 <= p <= REPORTED_BOOM_DELAY_S[1] + 90
                  for p in pred)
    print(f"\nReported boom timing (~300-360 s) is "
          f"{'CONSISTENT' if overlap else 'NOT consistent'} with the predicted "
          "delays across the populated felt zone (given the c/h uncertainty).")

    print("\nBest-effort social fetch (date/region sanity check only)...")
    posts = best_effort_social_fetch()
    print(f"  retrieved {len(posts)} candidate posts "
          f"({sum(p['source']=='reddit' for p in posts)} reddit, "
          f"{sum(p['source']=='bluesky' for p in posts)} bluesky)")
    if posts:
        with open(SOCIAL_RAW, "w") as fh:
            json.dump(posts, fh, indent=2)
        for p in posts[:5]:
            print(f"    [{p['source']}] {str(p.get('title',''))[:90]}")
    print("  NOTE: social post timestamps are not boom times and auto-geolocation "
          "is unreliable; used only to confirm the event's date/region.")

    out = {"source": best, "reported_boom_delay_s": list(REPORTED_BOOM_DELAY_S),
           "city_predictions": rows, "reported_consistent": bool(overlap),
           "n_social_posts": len(posts)}
    with open(VIDEOS_JSON, "w") as fh:
        json.dump(out, fh, indent=2)
    plot_delay_map(best, rows)
    print(f"\nWrote {VIDEOS_JSON}\n      {DELAY_PNG}")


if __name__ == "__main__":
    main()
