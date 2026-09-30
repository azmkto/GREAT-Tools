"""Indonesia choropleth reports for environmental-issue monitoring.

Extracted from `Visual_Report_LH_Ver2.ipynb`, where two visualization cells carried
byte-identical copies of eight helper functions between them. The reports draw the same
choropleth and the same style of horizontal bar chart; they differ only in layout and a
handful of styling parameters, so the panels live in the private `_panel_*` helpers and the
public functions just arrange them:

    env_daily     map | issue bars over island bars             figsize (30, 14)
    env_weekly    map | issue bars (| pie)                      figsize (38, 9) or (47, 9)
    env_monthly   map on top; island bars | issue bars (| pie)  figsize (30, 20)

The pie appears only when one issue dominates, see `dominant_issue()`. Every report draws
the same map: no colorbar, same-size count badges. All drop rows classified
'Noise/Tidak Relevan' before counting.

All expect a frame with `Provinsi` and `Isu_Inti` columns. Neither is in a raw export --
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
from ..issues import _NOISE
from ..geo import (
    GEO_FIX,
    KNOWN_PROVINCES,
    PROVINCE_FIX,
    PULAU_MAP,
    _canonicalize,
)

__all__ = [
    "load_indonesia_geojson", "province_counts", "island_counts",
    "env_daily", "env_weekly", "env_monthly", "dominant_issue",
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

# Provinces whose representative_point() lands in the sea (so the badge would float offshore)
# or crowds a neighbour. Hand-placed (lon, lat).
MANUAL_BADGE_POSITION = {
    "KEPULAUAN RIAU": (104.05, 1.30),
    "BALI": (115.15, -8.05),
    "NUSA TENGGARA BARAT": (117.55, -8.20),
    # West Java's provinces are too small for three badges side by side: Jakarta goes up
    # into the Java Sea, Banten west, Jawa Barat east; Yogyakarta drops below Jawa Tengah's.
    "DKI JAKARTA": (106.85, -5.35),
    "BANTEN": (105.75, -6.55),
    "JAWA BARAT": (107.75, -7.05),
    "DI YOGYAKARTA": (110.40, -8.45),
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
    """Post counts per province, with names normalised for joining against the GeoJSON.

    Returns a frame of [`province_col`, 'jumlah_unggahan', 'provinsi_normalized'].
    """
    if province_col not in data.columns:
        raise KeyError(f"column {province_col!r} not found -- derive it first, see the module docstring")
    counts = data.groupby(province_col).size().reset_index(name="jumlah_unggahan")
    counts["provinsi_normalized"] = counts[province_col].apply(_normalize_data_name)
    return counts


def island_counts(data, province_col="Provinsi"):
    """Post counts per island, mapped through `great.geo.PULAU_MAP`.

    Sorted ascending, which is what a horizontal bar chart wants (largest bar on top).
    Returns a Series indexed by island name.
    """
    provinces = data[province_col].apply(_normalize_data_name)
    return provinces.map(_PULAU_MAP_CI).value_counts().sort_values(ascending=True)


def dominant_issue(counts, ratio=2.0):
    """The top issue if it is at least `ratio` times the second one, else None.

    5,727 vs 717 (8x) -> the top issue; 1,000 vs 600 (1.7x) -> None.
    `counts` is a Series of post counts per issue, e.g. `data['Isu_Inti'].value_counts()`.
    """
    top = counts.nlargest(2)
    if len(top) == 2 and top.iloc[0] >= ratio * top.iloc[1]:
        return top.index[0]
    return None


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
        counts[["provinsi_normalized", "jumlah_unggahan"]],
        on="provinsi_normalized", how="left",
    )
    map_gdf["jumlah_unggahan"] = map_gdf["jumlah_unggahan"].fillna(0)
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
def _panel_choropleth(ax, map_gdf, prov_col, title, *, badge_size, title_size):
    """The Indonesia map, shaded by post count, with a same-size numbered badge per active province.

    One style for every report: no colorbar, provinces with zero posts at the pale end of the
    colormap, the view fitted to the islands.
    """
    map_gdf.plot(column="jumlah_unggahan", cmap=palette.CMAP_NAME, linewidth=0.5,
                 edgecolor="black", ax=ax)

    minx, miny, maxx, maxy = map_gdf.total_bounds
    pad_x, pad_y = (maxx - minx) * 0.03, (maxy - miny) * 0.05
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)
    ax.set_aspect("equal")

    for _, row in map_gdf.iterrows():
        value = row["jumlah_unggahan"]
        if value <= 0:
            continue

        province = _normalize_geo_name(row[prov_col])
        if province in MANUAL_BADGE_POSITION:
            x, y = MANUAL_BADGE_POSITION[province]
        else:
            point = _main_point(row.geometry)
            x, y = point.x, point.y

        # pad is the gap between number and circle, in font-size units: kept tight so
        # neighbouring badges (Jakarta, Banten, Jawa Barat) don't overlap
        ax.text(
            x, y, f"{int(value)}", ha="center", va="center", zorder=10,
            fontsize=badge_size, fontweight="bold", color="black",
            bbox=dict(boxstyle="circle,pad=0.12", facecolor="white",
                      edgecolor="black", linewidth=0.8),
        )

    ax.set_title(title, fontsize=title_size, fontweight="bold", pad=20)
    ax.axis("off")


def _panel_bars(ax, counts, title, *, colors):
    """A horizontal bar chart with a value label on the end of each bar."""
    bars = ax.barh(counts.index, counts.values, color=colors, height=0.7)

    ax.set_title(title, fontsize=palette.PANEL_TITLE_SIZE, fontweight="bold", pad=12)
    ax.set_xlabel("Jumlah Unggahan", fontsize=palette.PANEL_TICK_SIZE, fontweight="bold")
    ax.tick_params(axis="y", labelsize=palette.PANEL_TICK_SIZE, length=0)
    ax.tick_params(axis="x", labelsize=palette.PANEL_TICK_SIZE)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.xaxis.grid(True, linestyle="-", alpha=0.3, color="#e0e0e0")
    ax.set_axisbelow(True)

    max_value = counts.max() if len(counts) else 1
    for bar in bars:
        width = bar.get_width()
        ax.text(width + max_value * 0.015, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", va="center", ha="left",
                fontsize=palette.PANEL_VALUE_SIZE, fontweight="bold")


def _ramp_bar_colors(counts):
    """Bars shaded along the shared colormap, scaled to the largest."""
    top = counts.max() or 1
    return plt.colormaps[palette.CMAP_NAME]([value / top for value in counts.values])


def _panel_issue_pie(ax, provinces, issue, *, top_n=9):
    """Which provinces one issue comes from: the top `top_n`, the rest as "Lainnya".

    "Provinsi Tidak Spesifik" is a wedge of its own; "Tidak Terdeteksi" (no location found at all)
    goes into "Lainnya", so the pie still adds up to every post of the issue.
    """
    counts = provinces.value_counts().drop("Tidak Terdeteksi", errors="ignore")
    shown = counts.iloc[:top_n].copy()
    other = len(provinces) - shown.sum()
    if other > 0:
        shown["Lainnya"] = other
    total = shown.sum()

    # 0.40..0.98 along the colormap, relative to the busiest province; 0 marks "Lainnya"
    shades = [0.0 if name == "Lainnya" else 0.40 + 0.58 * value / counts.iloc[0]
              for name, value in shown.items()]
    cmap = plt.colormaps[palette.CMAP_NAME]

    _, _, autotexts = ax.pie(
        shown.values,
        labels=shown.index,
        colors=[cmap(shade) if shade else "#c9c9c9" for shade in shades],
        startangle=90, counterclock=False,
        # below 5% the number no longer fits its wedge and collides with the neighbour's
        autopct=lambda pct: f"{pct:.0f}%\n({int(round(pct / 100 * total))})" if pct >= 5 else "",
        pctdistance=0.72, labeldistance=1.05,
        wedgeprops=dict(edgecolor="white", linewidth=1.2),
        textprops=dict(fontsize=palette.PANEL_TICK_SIZE, fontweight="bold"),
    )
    for autotext, shade in zip(autotexts, shades):
        autotext.set(fontsize=palette.PANEL_VALUE_SIZE, color="white" if shade > 0.55 else "#222222")

    ax.set_title(f"Rincian Provinsi:\n{issue}\n(Total: {total:,} unggahan)",
                 fontsize=palette.PANEL_TITLE_SIZE, fontweight="bold", pad=12)


def _period(start_date, end_date):
    return f"{start_date} - {end_date}"


# =========================================================
# REPORTS
# =========================================================
def _without_noise(data, issue_col):
    """Rows classified 'Noise/Tidak Relevan' are not environmental issues -- no report counts them."""
    return data[data[issue_col] != _NOISE]


def env_weekly(data, start_date, end_date, *, province_col="Provinsi", issue_col="Isu_Inti",
               dominance_ratio=2.0, badge_size=18, show=True):
    """Weekly report: map | issue bars | a province pie when one issue dominates.

    If the top issue is at least `dominance_ratio` times the second (see `dominant_issue()`),
    it leaves the bar chart -- where it would squash every other bar into a sliver -- and
    gets a pie of the provinces it comes from instead. Otherwise there is no pie.

    Parameters
    ----------
    data : frame with `province_col` and `issue_col`; see the module docstring for deriving them.
        Rows classified 'Noise/Tidak Relevan' are dropped first.
    start_date, end_date : pre-formatted period labels, e.g. from `great.viz.prep.prepare_data`.
    dominance_ratio : how many times the second issue the top one must be to become a pie.
    badge_size : font size of the count inside each province's badge; the white circle is
        drawn in units of font size, so it grows with it.
    show : call `plt.show()` before returning.

    Returns the Figure.
    """
    data = _without_noise(data, issue_col)
    counts = data[issue_col].value_counts()
    top = dominant_issue(counts, dominance_ratio)

    # a pie is as wide as the row is tall (9), so it gets a narrow column of its own
    n_panels = 2 if top is None else 3
    fig, axes = plt.subplots(
        1, n_panels, figsize=(38 + 9 * (n_panels - 2), 9),
        gridspec_kw={"width_ratios": [1.3, 1, 0.55][:n_panels]},
    )

    map_gdf, prov_col = _map_with_counts(data, province_col)
    _panel_choropleth(
        axes[0], map_gdf, prov_col,
        f"Persebaran Isu Lingkungan di Indonesia\n{_period(start_date, end_date)}",
        badge_size=badge_size, title_size=26,
    )

    bars = counts[counts.index != top].sort_values(ascending=True)
    _panel_bars(axes[1], bars, "Distribusi Nasional Isu Lingkungan di Indonesia",
                colors=_ramp_bar_colors(bars))

    if top is not None:
        _panel_issue_pie(axes[2], data.loc[data[issue_col] == top, province_col], top)

    plt.tight_layout()
    if show:
        plt.show()
    return fig


def env_daily(data, start_date, end_date, *, province_col="Provinsi", issue_col="Isu_Inti",
              badge_size=18, show=True):
    """Daily report: map | issue bars stacked over posts-per-island bars.

    Same arguments as `env_weekly`, minus `dominance_ratio`. Returns the Figure.
    """
    data = _without_noise(data, issue_col)

    fig = plt.figure(figsize=(30, 14))
    gs = fig.add_gridspec(2, 2, width_ratios=[3.2, 1], height_ratios=[1, 1],
                          hspace=0.35, wspace=0.1)

    map_gdf, prov_col = _map_with_counts(data, province_col)
    _panel_choropleth(
        fig.add_subplot(gs[:, 0]), map_gdf, prov_col,
        f"Persebaran Isu Lingkungan di Indonesia\n{_period(start_date, end_date)}",
        badge_size=badge_size, title_size=20,
    )

    issues = data[issue_col].value_counts().sort_values(ascending=True)
    _panel_bars(fig.add_subplot(gs[0, 1]), issues, "Distribusi Nasional Isu Lingkungan di Indonesia",
                colors=_ramp_bar_colors(issues))

    islands = island_counts(data, province_col)
    _panel_bars(fig.add_subplot(gs[1, 1]), islands, "Distribusi Unggahan Isu Lingkungan per Pulau",
                colors=_ramp_bar_colors(islands))

    plt.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.05)
    if show:
        plt.show()
    return fig


def env_monthly(data, start_date, end_date, *, province_col="Provinsi", issue_col="Isu_Inti",
                dominance_ratio=2.0, badge_size=18, show=True):
    """Monthly report: map across the top; below it posts-per-island bars | issue bars | pie.

    The pie follows `env_weekly`'s rule: only when the top issue is at least
    `dominance_ratio` times the second, and that issue then leaves the bar chart. Without a
    pie the bottom row is just the two bar charts.

    Same arguments as `env_weekly`. Returns the Figure.
    """
    data = _without_noise(data, issue_col)
    counts = data[issue_col].value_counts()
    top = dominant_issue(counts, dominance_ratio)

    n_cols = 2 if top is None else 3
    fig = plt.figure(figsize=(30, 20))
    gs = fig.add_gridspec(2, n_cols, height_ratios=[1.1, 1], hspace=0.15, wspace=0.35)

    map_gdf, prov_col = _map_with_counts(data, province_col)
    _panel_choropleth(
        fig.add_subplot(gs[0, :]), map_gdf, prov_col,
        f"Persebaran Isu Lingkungan di Indonesia\n{_period(start_date, end_date)}",
        badge_size=badge_size, title_size=26,
    )

    islands = island_counts(data, province_col)
    _panel_bars(fig.add_subplot(gs[1, 0]), islands, "Distribusi Unggahan Isu Lingkungan per Pulau",
                colors=_ramp_bar_colors(islands))

    bars = counts[counts.index != top].sort_values(ascending=True)
    _panel_bars(fig.add_subplot(gs[1, 1]), bars, "Distribusi Nasional Isu Lingkungan di Indonesia",
                colors=_ramp_bar_colors(bars))

    if top is not None:
        _panel_issue_pie(fig.add_subplot(gs[1, 2]), data.loc[data[issue_col] == top, province_col], top)

    # not tight_layout(): the pie's outside labels make it push the bottom row apart
    plt.subplots_adjust(left=0.1, right=0.97, top=0.95, bottom=0.04)
    if show:
        plt.show()
    return fig
