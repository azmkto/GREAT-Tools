"""GREAT — shared utilities for the social-media research notebooks.

One place for the label vocabulary, color palette, text cleaning, environmental-issue
rules, province geography, and the weekly/monthly visualization helpers that used to be
copy-pasted between notebooks.

The common symbols are re-exported here, so the everyday import is flat:

    from great import sent_colors, sent_class, MEDIA_MAP, validate_export

Two things are deliberately *not* re-exported:

* `great.text` — it lazily imports `ftfy`/`nltk`/`Sastrawi` inside its functions so the
  core package stays usable without them. Importing it here would defeat that.
  Use `from great.text import clean_for_topics`.
* `great.viz` — it needs `matplotlib`/`scienceplots` (the `[viz]` extra). Keeping it out
  means `import great` still works in a text-only or headless environment.
  Use `from great.viz.overview import weekly_overview`.
"""

__version__ = "0.1.0"

from .labels import (
    sent_class,
    plat_class,
    emo_class,
    MEDIA_MAP,
    MAJAS_LABEL_FIX,
    MAJAS_LABEL_MAP,
    normalize_majas,
)
from .palette import (
    sent_colors,
    plat_colors,
    emo_colors,
    CMAP_NAME,
    BASE_MAP_COLOR,
    EDGE_COLOR,
    ACTIVE_EDGE_COLOR,
    TITLE_SIZE,
    SUBTITLE_SIZE,
    LABEL_SIZE,
    TICK_SIZE,
    ANNOT_SIZE,
    MAP_NUMBER_SIZE,
)
from .schema import EXPORT_COLUMNS, validate_export
from .issues import ISSUE_RULES, classify_issue
from .geo import PROVINCE_FIX, PULAU_MAP, ISLAND_ORDER, GEO_FIX

# --- ALIAS/BACKWARD COMPATIBILITY (DITAMBAHKAN) ---
# Menghubungkan nama variabel lama di notebook legacy ke variabel baru di package:
LOCATION_TO_PROVINCE = PROVINCE_FIX
PROVINCE_TO_PULAU = PULAU_MAP

__all__ = [
    "__version__",
    # labels
    "sent_class", "plat_class", "emo_class", "MEDIA_MAP",
    "MAJAS_LABEL_FIX", "MAJAS_LABEL_MAP", "normalize_majas",
    # palette
    "sent_colors", "plat_colors", "emo_colors",
    "CMAP_NAME", "BASE_MAP_COLOR", "EDGE_COLOR", "ACTIVE_EDGE_COLOR",
    "TITLE_SIZE", "SUBTITLE_SIZE", "LABEL_SIZE", "TICK_SIZE",
    "ANNOT_SIZE", "MAP_NUMBER_SIZE",
    # schema
    "EXPORT_COLUMNS", "validate_export",
    # issues
    "ISSUE_RULES", "classify_issue",
    # geo
    "PROVINCE_FIX", "PULAU_MAP", "ISLAND_ORDER", "GEO_FIX",
    # geo legacy aliases
    "LOCATION_TO_PROVINCE", "PROVINCE_TO_PULAU",
]
