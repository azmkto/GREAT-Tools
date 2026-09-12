"""Indonesia choropleth reports for environmental-issue monitoring.

Extracted from `Visual_Report_LH_Ver2.ipynb`, where two visualization cells carried
byte-identical copies of eight helper functions between them. Both reports draw the same
choropleth and the same style of horizontal bar chart; they differ only in layout and a
handful of styling parameters, so the panels live in the private `_panel_*` helpers and the
two public functions just arrange them:

    env_one_bar   map + 1 bar chart          figsize (38, 9)
    env_two_bar    map + 2 bar charts         figsize (30, 14)

Both expect a frame with `Provinsi` and `Isu_Inti` columns. Neither is in a raw export --
derive them first with `great.classify_issue()` and `great.resolve_frame()`.

Needs the `[geo]` extra: `geopandas`, `shapely`, `requests`. This module is deliberately not
imported by `great/viz/__init__.py`, so `from great.viz import prep` does not drag in GDAL.
"""
import os
import pathlib

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
from shapely.geometry import MultiPolygon

from .. import palette
from ..geo import (
    GEO_FIX,
    ISLAND_ORDER,
    KNOWN_PROVINCES,
    PROVINCE_FIX,
    PULAU_MAP,
    _canonicalize,
)

__all__ = [
    "load_indonesia_geojson", "province_counts", "island_counts",
    "env_one_bar", "env_two_bar",
]

# The upstream province boundaries. Third party -- a network call happens on first use, and
# the file is cached afterwards. 38 provinces is post-2022 Indonesia (the four new Papuan
# provinces included).
GEOJSON_URL = (
    "https://raw.githubusercontent.com/denyherianto/"
    "indonesia-geojson-topojson-maps-with-38-provinces/main/"
    "GeoJSON/indonesia-38-provinces.geojson"
)
GEOJSON_FILENAME = "indonesia_38_provinsi.geojson"
EXPECTED_PROVINCE_COUNT = 38

# Three provinces whose representative_point() lands in the sea, so the count badge would
# float offshore. Hand-placed (lon, lat).
MANUAL_BADGE_POSITION = {
    "KEPULAUAN RIAU": (104.05, 1.30),
    "BALI": (115.15, -8.05),
    "NUSA TENGGARA BARAT": (117.55, -8.20),
}

# Column names the upstream GeoJSON might use for the province name.
_PROVINCE_COLUMN_CANDIDATES = [
    "Provinsi", "Propinsi", "PROVINSI", "PROPINSI",
    "NAME_1", "WADMPR", "provinsi", "name", "NAME",
]

_UNKNOWN = "TIDAK DIKETAHUI"


# =========================================================
# NAME NORMALISATION
# =========================================================
def _build_ci_map(mapping):
    """Uppercase, whitespace-collapsed version of a province mapping.

    Only the GeoJSON side still needs this. The data side goes through
    `great.geo`'s own normaliser, which has handled case since 0.3.0.
    Non-string values (the `np.nan` entries in `PROVINCE_FIX`) pass through untouched.
    """
    out = {}
    for key, value in mapping.items():
        norm_key = " ".join(str(key).strip().upper().split())
        out[norm_key] = " ".join(value.strip().upper().split()) if isinstance(value, str) else value
    return out


_GEO_FIX_CI = _build_ci_map(GEO_FIX)   # for the GeoJSON's province column

# PULAU_MAP keys are Title Case; the normalisers below return uppercase. Values stay as
# written because they are used as bar-chart labels.
_PULAU_MAP_CI = {str(k).strip().upper(): v for k, v in PULAU_MAP.items()}


def _normalize_data_name(name):
    """Canonical province name for a value coming from the export data.

    Delegates to `great.geo`, so there is one definition of what a province is called.
    Falls back to the uppercase form when the value is not a province at all, which keeps
    unresolved values ("Tidak Terdeteksi") distinguishable in the join.
    """
    canonical = _canonicalize(name)
    if canonical in KNOWN_PROVINCES:
        return canonical.upper()
    return " ".join(str(name).strip().upper().split())


def _normalize_geo_name(name):
    """Normalise a province name coming from the GeoJSON.

    Kept separate from the data side: the upstream GeoJSON spells several provinces its own
    way ("Daerah Istimewa Yogyakarta"), which is what `GEO_FIX` exists to absorb.
    """
    key = " ".join(str(name).strip().upper().split())
    fixed = _GEO_FIX_CI.get(key, key)
    if pd.isna(fixed):
        return _UNKNOWN
    canonical = _canonicalize(fixed)
    return canonical.upper() if canonical in KNOWN_PROVINCES else key


def _detect_province_column(map_gdf):
    """Find whichever column holds the province name in this GeoJSON."""
    for column in _PROVINCE_COLUMN_CANDIDATES:
        if column in map_gdf.columns:
            return column
    return None


# =========================================================
# GEOJSON LOADING
# =========================================================
def _cache_dir():
    """Per-user cache directory, created on demand.

    The notebook version wrote into the current working directory, which litters whatever
    folder the notebook happened to be launched from and re-downloads once per project.
    """
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_CACHE_HOME") or "~/.cache"
    path = pathlib.Path(base).expanduser() / "great"
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_indonesia_geojson(force=False):
    """Return the 38-province GeoJSON as a GeoDataFrame, downloading once and caching.

    `force=True` re-downloads even when a cached copy exists. A cached file whose feature
    count is not 38 is treated as corrupt and re-fetched.

    Raises RuntimeError rather than returning an empty frame, so a network failure surfaces
    at the call site instead of becoming a silently blank map.
    """
    path = _cache_dir() / GEOJSON_FILENAME

    def download():
        response = requests.get(GEOJSON_URL, timeout=30)
        response.raise_for_status()
        path.write_bytes(response.content)

    if force or not path.exists():
        try:
            download()
        except Exception as exc:
            raise RuntimeError(f"could not download the province GeoJSON: {exc}") from exc

    try:
        map_gdf = gpd.read_file(path)
    except Exception:
        path.unlink(missing_ok=True)
        download()
        map_gdf = gpd.read_file(path)

    if len(map_gdf) != EXPECTED_PROVINCE_COUNT:
        # Cached copy is truncated or from a different source -- refetch once.
        path.unlink(missing_ok=True)
        download()
        map_gdf = gpd.read_file(path)

    return map_gdf


# =========================================================
# AGGREGATION
# =========================================================
def province_counts(data, province_col="Provinsi"):
    """Case counts per province, with names normalised for joining against the GeoJSON.

    Returns a frame of [`province_col`, 'jumlah_kasus', 'provinsi_normalized'].
    """
    if province_col not in data.columns:
        raise KeyError(f"column {province_col!r} not found -- derive it first, see the module docstring")
    counts = data.groupby(province_col).size().reset_index(name="jumlah_kasus")
    counts["provinsi_normalized"] = counts[province_col].apply(_normalize_data_name)
    return counts


def island_counts(data, province_col="Provinsi", order="count"):
    """Case counts per island, mapped through `great.geo.PULAU_MAP`.

    `order='count'` sorts ascending by value, which is what a horizontal bar chart wants
    (largest bar on top). `order='geographic'` uses `great.geo.ISLAND_ORDER` instead --
    west to east, so the chart reads like the map beside it.

    Returns a Series indexed by island name.
    """
    provinces = data[province_col].apply(_normalize_data_name)
    counts = provinces.map(_PULAU_MAP_CI).value_counts()

    if order == "geographic":
        present = [island for island in ISLAND_ORDER if island in counts.index]
        extra = [island for island in counts.index if island not in ISLAND_ORDER]
        # reversed, because barh draws the first entry at the bottom
        return counts.reindex(list(reversed(present + extra)))
    return counts.sort_values(ascending=True)


def _map_with_counts(data, province_col="Provinsi"):
    """The GeoJSON joined to per-province case counts, zero-filled where absent."""
    map_gdf = load_indonesia_geojson()
    prov_col = _detect_province_column(map_gdf)
    if prov_col is None:
        raise RuntimeError(
            f"no province-name column in the GeoJSON; looked for {_PROVINCE_COLUMN_CANDIDATES}"
        )

    map_gdf["provinsi_normalized"] = map_gdf[prov_col].apply(_normalize_geo_name)
    counts = province_counts(data, province_col)
    map_gdf = map_gdf.merge(
        counts[["provinsi_normalized", "jumlah_kasus"]],
        on="provinsi_normalized", how="left",
    )
    map_gdf["jumlah_kasus"] = map_gdf["jumlah_kasus"].fillna(0)
    return map_gdf, prov_col


def _main_point(geometry):
    """A representative point inside the largest polygon of a (multi)polygon."""
    if isinstance(geometry, MultiPolygon):
        largest = max(geometry.geoms, key=lambda geom: geom.area)
        return largest.representative_point()
    return geometry.representative_point()


# =========================================================
# PANELS
# =========================================================
def _panel_choropleth(ax, map_gdf, prov_col, title, *, colorbar=False,
                      proportional_badges=False, missing_color="#ffffe0",
                      badge_size=18, badge_growth=5, fit_bounds=False, title_size=None):
    """The Indonesia map, shaded by case count, with a numbered badge per active province."""
    title_size = palette.TITLE_SIZE if title_size is None else title_size

    legend_kwds = ({"label": "Jumlah kasus/isu", "shrink": 0.55, "pad": 0.02}
                   if colorbar else None)
    map_gdf.plot(
        column="jumlah_kasus", cmap=palette.CMAP_NAME, linewidth=0.5, edgecolor="black",
        ax=ax, legend=colorbar, legend_kwds=legend_kwds,
        missing_kwds={"color": missing_color, "edgecolor": "black", "linewidth": 0.5},
    )

    if fit_bounds:
        minx, miny, maxx, maxy = map_gdf.total_bounds
        pad_x, pad_y = (maxx - minx) * 0.03, (maxy - miny) * 0.05
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.set_aspect("equal")

    max_value = map_gdf["jumlah_kasus"].max() or 1

    for _, row in map_gdf.iterrows():
        value = row["jumlah_kasus"]
        if value <= 0:
            continue

        province = _normalize_geo_name(row[prov_col])
        if province in MANUAL_BADGE_POSITION:
            x, y = MANUAL_BADGE_POSITION[province]
        else:
            point = _main_point(row.geometry)
            x, y = point.x, point.y

        if proportional_badges:
            # sqrt so the badge area, not the radius, tracks the count. badge_size is the
            # floor; the busiest province lands at badge_size + badge_growth.
            size = badge_size + (value / max_value) ** 0.5 * badge_growth
            pad = 0.3
        else:
            size, pad = badge_size, 0.25

        ax.text(
            x, y, f"{int(value)}", ha="center", va="center", zorder=10,
            fontsize=size, fontweight="bold", color="black",
            bbox=dict(boxstyle=f"circle,pad={pad}", facecolor="white",
                      edgecolor="black", linewidth=0.8 if not proportional_badges else 0.6),
        )

    ax.set_title(title, fontsize=title_size, fontweight="bold", pad=20)
    ax.axis("off")


def _panel_bars(ax, counts, title, *, colors, title_size=None, label_size=10,
                tick_size=11, xlabel="Jumlah Kasus", serif=False):
    """A horizontal bar chart with a value label on the end of each bar."""
    title_size = palette.TITLE_SIZE if title_size is None else title_size

    bars = ax.barh(counts.index, counts.values, color=colors, height=0.7)

    ax.set_title(title, fontsize=title_size, fontweight="bold", pad=12,
                 **({"family": "serif"} if serif else {}))
    ax.set_xlabel(xlabel, fontsize=max(tick_size, 11), fontweight="bold")
    ax.tick_params(axis="y", labelsize=tick_size, length=0)
    ax.tick_params(axis="x", labelsize=tick_size)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.grid(True, linestyle="-", alpha=0.3, color="#e0e0e0")
    ax.set_axisbelow(True)

    max_value = counts.max() if len(counts) else 1
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max_value * 0.015, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", va="center", ha="left",
                fontsize=label_size, fontweight="bold")


def _flat_bar_colors(counts, base="#FFFACD", highlight="#800020"):
    """Pale bars with the largest one picked out -- the weekly report's styling."""
    if len(counts) <= 1:
        return [highlight]
    return [base] * (len(counts) - 1) + [highlight]


def _ramp_bar_colors(counts):
    """Bars shaded along the shared colormap, scaled to the largest -- the daily styling."""
    top = counts.max() or 1
    return plt.colormaps[palette.CMAP_NAME]([value / top for value in counts.values])


def _period(start_date, end_date):
    return f"{start_date} - {end_date}"


# =========================================================
# REPORTS
# =========================================================
def env_one_bar(data, start_date, end_date, *, province_col="Provinsi",
                              issue_col="Isu_Inti", badge_size=18, show=True):
    """Map plus one bar chart: where the issues are, and which issues they are.

    Parameters
    ----------
    data : frame with `province_col` and `issue_col`; see the module docstring for deriving them.
    start_date, end_date : pre-formatted period labels, e.g. from `great.viz.prep.prepare_data`.
    badge_size : font size of the count label inside each province's badge. Every badge in
        this report is the same size, so this is exactly the size you get. The white circle
        is drawn in units of font size, so it scales with the number -- but past roughly 25
        the hand-placed badges for Kepulauan Riau, Bali and Nusa Tenggara Barat start
        crowding their neighbours.
    show : call `plt.show()` before returning.

    Returns the Figure.
    """
    fig, (ax_map, ax_issue) = plt.subplots(
        1, 2, figsize=(38, 9), gridspec_kw={"width_ratios": [1.3, 1]}
    )

    map_gdf, prov_col = _map_with_counts(data, province_col)
    _panel_choropleth(
        ax_map, map_gdf, prov_col,
        f"Persebaran Isu Lingkungan di Indonesia\n{_period(start_date, end_date)}",
        colorbar=False, proportional_badges=False, missing_color="#ffffe0",
        badge_size=badge_size, title_size=26,
    )

    counts = data[issue_col].value_counts().sort_values(ascending=True)
    _panel_bars(
        ax_issue, counts,
        f"Distribusi Nasional Isu Lingkungan di Indonesia\n{_period(start_date, end_date)}",
        colors=_flat_bar_colors(counts), title_size=26, label_size=10, tick_size=11,
    )

    plt.tight_layout()
    if show:
        plt.show()
    return fig


def env_two_bar(data, start_date, end_date, *, province_col="Provinsi",
                             issue_col="Isu_Inti", island_order="count",
                             badge_size=18, badge_growth=5, show=True):
    """Map plus two stacked bar charts: issues nationally, and cases per island.

    Same arguments as `env_one_bar`, plus:

    island_order : 'count' (largest bar on top) or 'geographic' (west to east, matching
        `great.geo.ISLAND_ORDER`, so the chart reads in the same order as the map).
    badge_size : here badges scale with the count, so this is the size of the *smallest*
        badge, not a fixed size. The largest province gets `badge_size + badge_growth`.
    badge_growth : how many points the busiest province's badge gains over the quietest.
        Set it to 0 for uniform badges like the weekly report's.

    Returns the Figure.
    """
    fig = plt.figure(figsize=(30, 14))
    gs = fig.add_gridspec(2, 2, width_ratios=[3.2, 1], height_ratios=[1, 1],
                          hspace=0.35, wspace=0.1)

    ax_map = fig.add_subplot(gs[:, 0])
    ax_issue = fig.add_subplot(gs[0, 1])
    ax_island = fig.add_subplot(gs[1, 1])

    map_gdf, prov_col = _map_with_counts(data, province_col)
    _panel_choropleth(
        ax_map, map_gdf, prov_col, "Persebaran Isu Lingkungan di Indonesia",
        colorbar=True, proportional_badges=True, missing_color="#d9d9d9",
        badge_size=badge_size, badge_growth=badge_growth, fit_bounds=True, title_size=20,
    )

    issue = data[issue_col].value_counts().sort_values(ascending=True)
    _panel_bars(
        ax_issue, issue, "Distribusi Nasional Isu Lingkungan di Indonesia",
        colors=_ramp_bar_colors(issue), title_size=20, label_size=18, tick_size=14,
        xlabel="Jumlah kasus",
    )

    islands = island_counts(data, province_col, order=island_order)
    _panel_bars(
        ax_island, islands, "Distribusi Kasus Isu Lingkungan per Pulau",
        colors=_ramp_bar_colors(islands), title_size=20, label_size=18, tick_size=14,
        xlabel="Jumlah kasus",
    )

    plt.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.05)
    if show:
        plt.show()
    return fig
