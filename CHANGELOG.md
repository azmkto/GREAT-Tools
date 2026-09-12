# Changelog

Notable changes to `great`. Versions are tagged in git, so a notebook can pin a known-good
one — see [TUTORIAL.md §4](TUTORIAL.md) for the pinned-install syntax.

## 0.2.1

### Added

- **`resolve_province()` and `resolve_province_frame()` in `great.geo`.** Combines the two
  resolvers the way every caller actually wants: prefer the structured `Location` column when
  it names a real province, fall back to scanning the headline and mention text otherwise.
  `resolve_province_frame(df)` applies it across a frame and returns `[Provinsi, Pulau]`.
  Both example notebooks carried a copy of this logic inline; now they call the library.
- **`is_known_province()` and `KNOWN_PROVINCES`.** `resolve_from_structured_column()` returns
  its input unchanged when it does not recognise it, so callers could not tell a match from a
  miss. The inline notebook version inferred it by comparing input against output, which
  silently discarded any `Location` that was *already* a correctly spelled province name —
  the most reliable input there is. `is_known_province()` answers the question directly,
  testing against the 41 canonical names in `PULAU_MAP`.

### Changed

- `weekly_environment_report()` → **`env_one_bar()`**, `daily_environment_report()` →
  **`env_two_bar()`**. Anything importing the old names needs updating; they are gone, not
  aliased.

## 0.2.0

### Added

- **`great.geo` free-text location resolution.** A 572-entry Indonesian gazetteer
  (`LOCATION_TO_PROVINCE`) plus two resolvers: `resolve_from_free_text()` scans headline or
  mention text for the most specific place name and returns `(provinsi, pulau)`;
  `resolve_from_structured_column()` normalises an existing province column. Both are
  re-exported from `great`. Falls back to `ISLAND_FALLBACK` when only an island is named, and
  returns `"Tidak Terdeteksi"` when nothing matches. *(Naufaldo Indra Pratama)*
- **`great.viz.environment`** — Indonesia choropleth reports for environmental-issue
  monitoring. `env_one_bar()` draws a map plus one issue bar chart;
  `env_two_bar()` draws a map plus issue and per-island bar charts. Also
  `province_counts()`, `island_counts()` and `load_indonesia_geojson()`. Extracted from
  `Visual_Report_LH_Ver2.ipynb`, where the two figures duplicated eight helper functions
  verbatim between them.
  Both reports take `badge_size` to set the count-label font on the map; the daily one also
  takes `badge_growth`, since its badges scale with the count.
- **`[geo]` extra** — `geopandas`, `shapely`, `requests`, needed by `great.viz.environment`.
  Kept out of `[viz]` because geopandas pulls GDAL/PROJ; `[all]` includes it.
- **130 new `SLANG` entries** (96 → 226) and a precompiled `SLANG_PATTERN` for single-pass
  replacement. Type hints and precompiled regexes throughout `great.text`.
  *(Naufaldo Indra Pratama)*
- Two example notebooks under `Environment Visualization/`, one per report.

### Changed

- **Text cleaning output has changed.** The expanded `SLANG` dictionary means the cleaners no
  longer produce what 0.1.0 produced. Measured over 400 real mentions: `normalize_slang`
  differs on 294, `clean_for_bert` on 66, `clean_for_topics` and `clean_for_wordcloud` on 39
  each. This is an improvement — more slang is now normalised — but **topic models and word
  clouds built on 0.1.0 will not reproduce exactly.** Pin `v0.1.0` if you need the old
  behaviour.
- `great.text` is now re-exported from `great`, so `from great import clean_for_topics` works.
  Safe only because its `ftfy`/`nltk`/`Sastrawi` imports stay lazy — keep them that way.
- `pyproject.toml` uses setuptools package auto-discovery instead of an explicit list.
- The example notebooks now read from `Data/Prabowo 2026/prabowo26_agustus1.xlsx`, following
  the reorganisation of the data folders.

### Fixed

- **`import great` was completely broken.** `great/geo.py` imported `flashtext` at module
  level and built its keyword processor at import time, but `flashtext` was not declared in
  `pyproject.toml`. Since `great/__init__.py` imports `great.geo`, anyone without flashtext
  already installed got `ModuleNotFoundError` on `import great` — the palette and label
  vocabularies included. It is now a declared dependency *and* imported lazily on first use,
  so the core package imports even where it is absent.
- **`LOCATION_TO_PROVINCE` returned the wrong dictionary.** It had been aliased to
  `PROVINCE_FIX` under a "backward compatibility" comment, but those are different maps
  sharing no keys: the gazetteer is 572 entries (`'medan' → 'Sumatera Utara'`), the spelling
  normaliser 62 (`'NTT' → 'Nusa Tenggara Timur'`). Every gazetteer lookup through the
  top-level name silently missed. It now resolves to the real gazetteer.
- `resolve_from_free_text()` and `resolve_from_structured_column()` were unreachable from the
  top level; both are exported now, along with `ISLAND_FALLBACK`.
- `SLANG` mapped `beneran → benaran`, which is not the standard form, while `bener → benar`.
  Both now normalise to `benar`.
- `great.viz.environment` caches the province GeoJSON in a per-user directory rather than
  downloading it into whatever folder the notebook was launched from.

## 0.1.0

Initial package. Label vocabularies, colour palette, export schema and `validate_export()`,
text cleaners, environmental-issue rules, province geography, and `great.viz` — the weekly and
monthly sentiment/platform overview figures and the sentiment word clouds, extracted from
`pol_weekly_viz.ipynb` and `pol_monthly_viz.ipynb`.
