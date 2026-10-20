"""Reshape a raw media-monitoring export into the frames the plots consume.

The usual sequence:

    df1, start_date, end_date = prep.prepare_data(df)
    sent_data = prep.sentiment_data(df1)   # Date x Sentiment  (wide)
    plat_data = prep.platform_data(df1)    # (Date, Media)     -> Count
    ps_data   = prep.plat_sent_data(df1)   # Media, Sentiment, Count (long)

`find_export(folder, names)` picks the export to read from a folder of them, and
`month_exports(folder, names, month)` every export that covers part of a month.
"""
import calendar
import datetime as dt
import re
from pathlib import Path

import pandas as pd

from ..labels import MEDIA_MAP


def _norm(name):
    return re.sub(r'[\s_.\-]+', ' ', name).lower()


def _matching(folder, names):
    """Excel exports in `folder` whose name contains any of `names`; raises when there are none."""
    names = [names] if isinstance(names, str) else names
    files = [p for p in Path(folder).iterdir()
             if p.suffix.lower() in ('.xlsx', '.xls') and not p.name.startswith('~$')]
    hits = [p for p in files if any(_norm(n) in _norm(p.stem) for n in names)]
    if not hits:
        raise FileNotFoundError(f'No export matching {list(names)} in {folder}. '
                                f'Excel files there: {sorted(p.name for p in files)}')
    return hits


def _name_dates(p):
    """(start, end) from the monitoring tool's `_YYYYMMDD_YYYYMMDD_` file name, or None."""
    m = re.search(r'_(\d{8})_(\d{8})_', p.name)
    return tuple(dt.datetime.strptime(d, '%Y%m%d').date() for d in m.groups()) if m else None


def month_exports(folder, names, month):
    """Every export in `folder` matching `names` that covers any day of `month` ('YYYY-MM').

    The dates come from the file names (the monitoring tool's `_YYYYMMDD_YYYYMMDD_`), so no file
    is opened to decide. A week that crosses the month boundary is included in both months; trim
    the rows to `first_day`..`last_day` after reading so each day is counted in one month only.
    Files without dates in the name are skipped and listed.

    Returns `(files, first_day, last_day)`, files sorted by start date.
    """
    year, mon = map(int, month.split('-'))
    first = dt.date(year, mon, 1)
    last = dt.date(year, mon, calendar.monthrange(year, mon)[1])

    hits = _matching(folder, names)
    undated = sorted(p.name for p in hits if _name_dates(p) is None)
    if undated:
        print(f'Skipped, no dates in the name: {undated}')
    files = sorted((p for p in hits if _name_dates(p) and _name_dates(p)[0] <= last
                    and _name_dates(p)[1] >= first), key=_name_dates)
    if not files:
        raise FileNotFoundError(f'No export matching {list(names)} in {folder} covers {month}')
    return files, first, last


def find_export(folder, names):
    """The newest Excel export in `folder` whose file name contains any of `names`.

    Names are compared case-insensitively with '_', '-' and '.' read as spaces, so
    `'badan komunikasi'` matches `report_17736_all_all_20261012_20261012_2924_Badan_Komunikasi_Presiden.xlsx`
    and `'prabowo'` matches both that naming scheme and a hand-named `Data Prabowo.xlsx`.
    Newest is the end date in the name (`_YYYYMMDD_YYYYMMDD_`, the monitoring tool's scheme)
    when there is one, otherwise the day the file was last modified. Excel lock files (`~$...`)
    are skipped.

    Raises FileNotFoundError listing the folder's Excel files when nothing matches.
    """
    def newest(p):
        mtime = p.stat().st_mtime
        dates = _name_dates(p)
        return (dates[1] if dates else dt.date.fromtimestamp(mtime)), mtime

    return max(_matching(folder, names), key=newest)


def prepare_data(data):
    """Parse dates, normalise platform spelling and sentiment case; sort by date.

    `Date` keeps its time of day, which the coordination and timing analyses need; the
    daily helpers below floor it to the day themselves.

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
    data['Date'] = pd.to_datetime(data['Date'], format='ISO8601')
    data['Media'] = data['Media'].replace(MEDIA_MAP)
    data['Sentiment'] = data['Sentiment'].str.strip().str.lower()
    data = data.sort_values('Date', ascending=True)
    start_date = data['Date'].iloc[0].strftime('%d %b %Y')
    end_date = data['Date'].iloc[-1].strftime('%d %b %Y')
    return data, start_date, end_date


def sentiment_data(data):
    """Daily sentiment counts, wide: one row per Date, one column per sentiment."""
    return data.groupby(data['Date'].dt.normalize())['Sentiment'].value_counts().unstack(fill_value=0)


def platform_data(data):
    """Daily platform counts as a long Series named 'Count', indexed (Date, Media)."""
    return (data.groupby(data['Date'].dt.normalize())['Media']
                .value_counts().unstack(fill_value=0).stack().rename('Count'))


def plat_sent_data(data):
    """Platform x sentiment counts as a long frame with [Media, Sentiment, Count]."""
    return (data.groupby('Media')['Sentiment']
                .value_counts().unstack(fill_value=0).stack()
                .rename('Count').reset_index())
