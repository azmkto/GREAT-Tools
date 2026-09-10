"""Load-time sanity checks — the print-blocks both notebooks ran before plotting.

These report; they don't raise. For the strict, fail-fast version of the label
check use `great.validate_export()` directly.
"""
import pandas as pd

from ..schema import validate_export


def frame_info(obj, label):
    """Print shape, columns and dtypes for a DataFrame, or index levels for a Series."""
    print(f'\n{label} Info:\n')
    print(f'Number of Rows: {len(obj):,}')
    if isinstance(obj, pd.DataFrame):
        print(f'Columns: {list(obj.columns)}\n')
        print('Data Types:')
        print(obj.dtypes.to_string(), '\n')
    else:
        print(f'Value Name: {obj.name}\n'
              f'Index Levels: {list(obj.index.names)}\n'
              f'Data Type: {obj.dtype}')
        for level in obj.index.names:
            values = obj.index.get_level_values(level).unique()
            if pd.api.types.is_datetime64_any_dtype(values):
                print(f'{level}: {len(values)} unique '
                      f'({values.min():%d %b %Y} - {values.max():%d %b %Y})')
            else:
                print(f'{level}: {len(values)} unique {values.tolist()}')
        print()


def check_completeness(data):
    """Print per-column missing-value counts, plus duplicate row/mention counts."""
    missing = data.isna().sum()
    print('Completeness:')
    print(missing[missing > 0].to_string() if missing.any() else 'No missing values')
    print(f'\nDuplicate Rows     : {data.duplicated().sum():,}\n'
          f'Duplicate Mentions : {data["Mentions"].duplicated().sum():,}\n')


def check_coverage(data):
    """Print days covered, empty days, peak/quietest day and the daily average."""
    days = data['Date'].dt.normalize()
    daily = days.value_counts().sort_index()
    span = pd.date_range(days.min(), days.max(), freq='D')
    gaps = span.difference(daily.index)

    print('Time Coverage:')
    print(f'Days Covered  : {daily.size} of {span.size}\n'
          f'Empty Days    : {gaps.size}\n'
          f'Peak Day      : {daily.idxmax():%d %b %Y} ({daily.max():,} mentions)\n'
          f'Quietest Day  : {daily.idxmin():%d %b %Y} ({daily.min():,} mentions)\n'
          f'Daily Average : {daily.mean():,.0f} mentions\n')


def share(series, top=None):
    """Value counts for `series` with a 'Share (%)' column, optionally top-N only.

    The share is always against the full length of `series`, so a `top=10` view
    still reads as a percentage of everything, not of the ten shown.
    """
    counts = series.value_counts()
    denominator = len(series)
    if top:
        counts = counts.head(top)
    return pd.DataFrame({'Count': counts,
                         'Share (%)': (counts / denominator * 100).round(1)})


def check_composition(data, top_authors=10):
    """Print the sentiment, platform and top-author breakdowns."""
    print('Sentiment Breakdown:')
    print(share(data['Sentiment']).to_string(), '\n')

    print('Platform Breakdown:')
    print(share(data['Media']).to_string(), '\n')

    print(f'Unique Authors: {data["Author"].nunique():,}\n')
    print(f'Top {top_authors} Authors:')
    print(share(data['Author'], top=top_authors).to_string(), '\n')


def check_labels(data):
    """Report whether every Sentiment / Media value is one the library recognises.

    Delegates the actual vocabulary comparison to `great.validate_export()` so
    there is only one definition of "recognised", then downgrades its exception
    to a printed line — these checks are informational, not fatal.
    """
    print('Label Check:')
    try:
        validate_export(data)
    except ValueError as exc:
        print(f'Problem: {exc}')
    else:
        print('All Sentiment and Media values recognised')
