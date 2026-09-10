"""Reshape a raw media-monitoring export into the frames the plots consume.

The usual sequence:

    df1, start_date, end_date = prep.prepare_data(df)
    sent_data = prep.sentiment_data(df1)   # Date x Sentiment  (wide)
    plat_data = prep.platform_data(df1)    # (Date, Media)     -> Count
    ps_data   = prep.plat_sent_data(df1)   # Media, Sentiment, Count (long)
"""
import pandas as pd

from ..labels import MEDIA_MAP


def prepare_data(data):
    """Normalise dates, platform spelling and sentiment case; sort by date.

    Returns `(data, start_date, end_date)` where the two dates are pre-formatted
    `'%d %b %Y'` strings for use in plot titles.
    """
    data = data.copy()
    # The exports store Date as ISO strings ('2026-07-03 16:58:03'), so the format is
    # fixed and unambiguous -- parse it as such rather than letting pandas guess.
    #
    # Deliberately NOT `dayfirst=True` (which the original notebooks used): on pandas 3
    # dayfirst is applied to ISO input too, silently swapping day and month whenever the
    # day is <= 12 -- '2026-07-01' became 07 Jan 2026. Because dates past the 12th are
    # left alone, a single file ends up with a mix of correct and swapped dates.
    # `format='ISO8601'` also fails loudly if an export ever arrives in another layout,
    # instead of quietly mis-parsing it.
    data['Date'] = pd.to_datetime(data['Date'], format='ISO8601').dt.normalize()
    data['Media'] = data['Media'].replace(MEDIA_MAP)
    data['Sentiment'] = data['Sentiment'].str.strip().str.lower()
    data = data.sort_values('Date', ascending=True)
    start_date = data['Date'].iloc[0].strftime('%d %b %Y')
    end_date = data['Date'].iloc[-1].strftime('%d %b %Y')
    return data, start_date, end_date


def sentiment_data(data):
    """Daily sentiment counts, wide: one row per Date, one column per sentiment."""
    return data.groupby('Date')['Sentiment'].value_counts().unstack(fill_value=0)


def platform_data(data):
    """Daily platform counts as a long Series named 'Count', indexed (Date, Media)."""
    return (data.groupby('Date')['Media']
                .value_counts().unstack(fill_value=0).stack().rename('Count'))


def plat_sent_data(data):
    """Platform x sentiment counts as a long frame with [Media, Sentiment, Count]."""
    return (data.groupby('Media')['Sentiment']
                .value_counts().unstack(fill_value=0).stack()
                .rename('Count').reset_index())
