"""GREAT — shared utilities for the social-media research notebooks.

One place for the label vocabulary, color palette, text cleaning, environmental-issue
rules, province geography, and the weekly/monthly visualization helpers that used to be
copy-pasted between notebooks.

The common symbols are re-exported here, so the everyday import is flat:

    from great import sent_colors, sent_class, MEDIA_MAP, validate_export

`great.text` is re-exported too, which is safe *only* because its heavy dependencies
(`ftfy`, `nltk`, `Sastrawi`) are imported lazily inside its functions rather than at module
level. Keep it that way -- a module-level `import ftfy` in `great/text.py` would make
`import great` fail for anyone without the `[text]` extra.

`great.geo` follows the same rule: `flashtext` is imported on first use, not at import time.

`great.viz` is deliberately **not** re-exported here. It imports matplotlib, scikit-learn,
wordcloud and (for `great.viz.environment`) geopandas at module level, so pulling it in would
make `import great` require a full plotting and geospatial stack. Import it directly:

    from great.viz.overview import weekly_overview
    from great.viz.environment import env_two_bar
"""

__version__ = "0.3.2"

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
from .geo import (
    PROVINCE_FIX,
    PULAU_MAP,
    ISLAND_ORDER,
    ISLAND_FALLBACK,
    GEO_FIX,
    LOCATION_TO_PROVINCE,
    AMBIGUOUS_REGIONS,
    KNOWN_PROVINCES,
    UNDETECTED,
    is_known_province,
    resolve,
    resolve_frame,
)

# --- TEXT CLEANING & SLANG ---
from .text import (
    SLANG,
    TOPIC_STOPWORDS_BASE,
    WORDCLOUD_STOPWORDS_EXTRA,
    normalize_slang,
    clean_for_bert,
    clean_for_topics,
    clean_for_wordcloud,
)

# --- ALIAS/BACKWARD COMPATIBILITY ---
# `LOCATION_TO_PROVINCE` is imported from .geo above -- it is the free-text gazetteer
# (572 entries, 'medan' -> 'Sumatera Utara'). It must NOT be aliased to PROVINCE_FIX, which
# is the 40-entry spelling normaliser ('NTT' -> 'Nusa Tenggara Timur'). The two share no
# keys, so that alias silently returned a dict in which every gazetteer lookup missed.
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
    "PROVINCE_FIX", "PULAU_MAP", "ISLAND_ORDER", "ISLAND_FALLBACK", "GEO_FIX",
    "LOCATION_TO_PROVINCE",
    "resolve", "resolve_frame", "is_known_province",
    "KNOWN_PROVINCES", "AMBIGUOUS_REGIONS", "UNDETECTED",
    # geo legacy alias
    "PROVINCE_TO_PULAU",
    # text
    "SLANG",
    "TOPIC_STOPWORDS_BASE",
    "WORDCLOUD_STOPWORDS_EXTRA",
    "normalize_slang",
    "clean_for_bert",
    "clean_for_topics",
    "clean_for_wordcloud",
]
