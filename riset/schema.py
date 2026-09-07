"""The canonical media-monitoring export schema, and a loader-time validator.

Every project in this portfolio consumes the same kind of export (Twitter/X,
Facebook, Instagram, TikTok, YouTube, News), but nothing ever wrote the schema down
in one place — so each notebook re-derives it slightly differently, and category
spelling drifts between projects (see EVALUATION.md section 5.2). Call
`validate_export()` right after loading a raw file so a mismatch fails at load time
with a clear message, instead of turning into a silent `NaN` forty cells later.
"""
import pandas as pd

from .labels import sent_class, plat_class, MEDIA_MAP

EXPORT_COLUMNS = [
    'No', 'Type', 'Headline', 'Mentions', 'Date', 'Link', 'Media',
    'Sentiment', 'Author', 'Followers', 'Retweeted', 'Favourited', 'Location',
]


def validate_export(df: pd.DataFrame) -> pd.DataFrame:
    """Raise a clear error if `df` doesn't match the expected export shape.

    Checks: required columns are present, `Sentiment` values are all in
    `riset.labels.sent_class` (case-insensitive), and `Media` values are all
    either in `riset.labels.plat_class` or mappable to it via `MEDIA_MAP`.
    Returns `df` unchanged so this can be chained: `df = validate_export(df)`.
    """
    missing = [c for c in EXPORT_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"export is missing columns: {missing}")

    if 'Sentiment' in df.columns:
        bad_sentiment = set(df['Sentiment'].dropna().astype(str).str.strip().str.lower()) - set(sent_class)
        if bad_sentiment:
            raise ValueError(f"unknown sentiment values: {sorted(bad_sentiment)}")

    if 'Media' in df.columns:
        known = set(plat_class) | set(MEDIA_MAP)
        bad_media = set(df['Media'].dropna().astype(str)) - known
        if bad_media:
            raise ValueError(f"unknown platform values: {sorted(bad_media)}")

    return df
