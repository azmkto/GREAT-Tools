# Changelog

Notable changes to `great`. Versions are tagged in git, so a notebook can pin a known-good
one — see [TUTORIAL.md §4](TUTORIAL.md) for the pinned-install syntax.

## 0.3.1

### Changed

- **`env_one_bar()` now takes `badge_growth` too.** Both reports draw the same map through the
  same panel helper, but only `env_two_bar()` exposed the control, so a styling choice
  inherited from the source notebook — weekly used flat badges, daily used scaled ones — had
  hardened into a capability difference in the API. The two functions should differ in what
  they *draw*, not in what you can *ask for*.

  Defaults are unchanged: `env_one_bar` defaults to `badge_growth=0` (flat 18pt badges, edge
  0.8) and `env_two_bar` to `badge_growth=5` (18.4→23pt, edge 0.6), so every existing call
  renders exactly as before.

  `island_order` stays on `env_two_bar` alone, which is the justified asymmetry — `env_one_bar`
  has no island chart for it to order.

- The private `_panel_choropleth()` lost its `proportional_badges` flag; it only ever meant
  "is `badge_growth` non-zero", so the flag and the number could disagree.

## 0.3.0

Region mapping rebuilt on the official BPS region-code list (38 provinces, 514 kabupaten/kota),
merged into the hand-built gazetteer rather than replacing it.

### Added

- **`tools/build_regions.py` and `great/_regions.py`.** The generator reads the BPS CSV and
  emits plain dict literals, so the data is greppable and diffable and costs no import-time
  file IO. Re-run it when BPS publishes an update.
- **`AMBIGUOUS_REGIONS`** — names that mean different places depending on context.
  `sungai kapuas` → Kalimantan Barat but bare `kapuas` → Kalimantan Tengah (Kab. Kapuas is
  62.03); `kota banjar` → Jawa Barat but bare `banjar` → Kalimantan Selatan. Every other
  landmark whose bare name is also a kabupaten (`danau toba`, `sungai siak`, `gunung kerinci`,
  `danau kerinci`, `danau poso`) agrees with the official list, so the table has two entries.
- **`COMMON_WORD_REGIONS`** — region names that are also ordinary Indonesian words and so must
  not match bare. One member: `puncak` ("peak") matched 2.4% of all documents and sent Jakarta
  articles about *puncak El Niño* to Papua Tengah. Still reachable as `kab. puncak`.

### Changed

- **`resolve()` now prefers article text over the structured `Location` column.** Measured on
  25k rows, the two disagree **74%** of the time, and `Location` is the author's or outlet's
  location — `Jakarta` on an article about fires in Kalimantan. For a map of where issues are
  *happening*, the text is the right signal; `Location` is now the fallback for rows the text
  cannot place. Total hit rate is unchanged by this; the cases simply land in the right province.
- **`PULAU_MAP` is 38 provinces, not 41.** `Maluku Tengah` (kabupaten 81.01) and
  `Maluku Selatan` were never provinces and are now gazetteer entries pointing at `Maluku`;
  `Daerah Istimewa Yogyakarta` was a duplicate of `DI Yogyakarta` and stays an alias in
  `PROVINCE_FIX`/`GEO_FIX`. `KNOWN_PROVINCES` finally means what its name says.
- **Matching is case-, whitespace- and punctuation-insensitive.** Previously lowercase worked
  for only 7 of 41 provinces, because `PROVINCE_FIX` had grown ad-hoc lowercase keys for some
  and not others. All 38 now resolve from any casing, and the values real exports contain —
  `Kota Bandung\, Jawa Barat`, `Trenggalek\, Indonesia`, `KAB. ACEH SINGKIL` — resolve too.
- **Three outdated mappings corrected** from the official list: `puncak jaya` → Papua Tengah
  and `raja ampat` → Papua Barat Daya (both predated the 2022 Papua split), `kapuas` →
  Kalimantan Tengah.
- **`resolve_frame()` is ~3.3x faster** (2,800 → 9,300 rows/sec). Roughly half the rows in a
  real export repeat text verbatim — retweets and syndicated copy — so each distinct text is
  scanned once.
- Hit rate improved with **zero rows lost**: 63.5% → 67.2% on `test_data.xlsx`, 67.8% → 70.3%
  on `test_data_2.xlsx`. Map coverage 33 → 34 of 38 provinces.

### Removed

Breaking. `resolve_from_free_text`, `resolve_from_structured_column`, `resolve_province` and
`resolve_province_frame` are gone, with no aliases. Replace all four with `resolve()` for a
single value or `resolve_frame()` for a DataFrame.

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
