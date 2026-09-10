"""The sentiment / platform overview figure, weekly and monthly.

Both notebooks carried a copy of this under the name
`plot_sentiment_platform_overview`. The three stacked-bar panels were identical;
monthly only added a sentiment-trend line plot across the top and grew the
gridspec to fit it. So the panels live in the private `_panel_*` helpers below
and the two public wrappers just lay them out:

    weekly_overview   2x2 grid, 3 panels          figsize (30, 7)
    monthly_overview  3x2 grid, 3 panels + trend  figsize (30, 14)

Both return `(sent_pct_df, platform_totals_df)`.
"""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .. import labels, palette


def _panel_sentiment_trend(ax, sentiment_data, sent_class, sent_colors,
                           robj, start_date, end_date, interval):
    """Top panel (monthly only): daily mention count per sentiment, as lines."""
    for s in sent_class:
        ax.plot(sentiment_data.index, sentiment_data[s], label=s.capitalize(),
                color=sent_colors[s], linewidth=3, marker='o', ms=3.01, alpha=0.8)
    ax.set_title(f'Sentiment Trend of {robj}\n'
                 f'{start_date} - {end_date}', fontsize=20, fontweight='bold', pad=20)
    ax.set_xlabel('Time', fontsize=18, fontweight='semibold')
    ax.set_ylabel('Mentions', fontsize=18, fontweight='semibold')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    ax.tick_params(axis='x', rotation=0, labelsize=12)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.5, 1.05),
              frameon=False, ncol=3)


def _panel_media_sentiment(ax, ps_data, plat_class, sent_class, sent_colors,
                           robj, start_date, end_date):
    """Left panel: sentiment share within each platform, stacked horizontal bars."""
    media_totals = (ps_data.groupby(['Media', 'Sentiment'])['Count'].sum()
                           .unstack().reindex(plat_class, axis=0))
    media_pct = media_totals.div(media_totals.sum(axis=1), axis=0) * 100

    y = np.arange(len(plat_class))
    bar_height = 0.5
    left = np.zeros(len(plat_class))

    for s in sent_class:
        values = np.array([media_pct.loc[p, s]
                           if (p in media_pct.index and s in media_pct.columns) else 0
                           for p in plat_class])
        ax.barh(y, values, left=left, height=bar_height, label=s, color=sent_colors[s])
        for i, v in enumerate(values):
            if v > 5:
                ax.text(left[i] + v / 2, y[i], f'{v:.1f}%',
                        ha='center', va='center',
                        color='black' if s == 'positive' else 'white',
                        fontsize=16, fontweight='semibold')
        left += values

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.set_yticks(y, labels=plat_class, fontsize=18, fontweight='semibold')
    ax.set_xlabel('Mentions (%)', fontsize=18, fontweight='semibold')
    ax.set_title(f'Sentiment share per Media of {robj}\n'
                 f'{start_date} - {end_date}', fontsize=20, fontweight='bold')
    ax.set_xlim(0, 100)
    ax.legend(fontsize=12, loc='upper center', bbox_to_anchor=(0.15, 1.05),
              frameon=False, ncol=3)


def _panel_overall_sentiment(ax, sentiment_data, sent_class, sent_colors,
                             robj, start_date, end_date):
    """Upper-right panel: overall sentiment share as one stacked bar.

    Returns `sent_pct_df` (Count / Percentage per sentiment).
    """
    sent_total = sentiment_data[sent_class].sum()
    sent_grand_total = sent_total.sum()
    sent_pct = sent_total / sent_grand_total * 100

    left_tr = 0
    bar_height_tr = 0.6
    for s in sent_class:
        value = sent_pct[s]
        ax.barh(0, value, left=left_tr, height=bar_height_tr,
                color=sent_colors[s], edgecolor='white', linewidth=0.5,
                label=f'{s.capitalize()}:{int(sent_total[s]): ,}')
        if value > 5:
            ax.text(left_tr + value / 2, 0, f'{value:.1f}%',
                    ha='center', va='center',
                    color='black' if s == 'positive' else 'white',
                    fontsize=18, fontweight='semibold')
        left_tr += value

    ax.set_xlim(0, 100)
    ax.set_yticks([])
    ax.set_xlabel('Share of Mentions (%)', fontsize=12)
    ax.set_title(f'Sentiment Shares of {robj}\n{start_date} - {end_date}',
                 fontsize=20, pad=12, fontweight='semibold')
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis='x', labelsize=10)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
              ncol=3, frameon=False, fontsize=18)

    return pd.DataFrame({
        'Count': sent_total,
        'Percentage': sent_total / sent_grand_total,
    })


def _panel_platform_share(ax, platform_data, plat_colors,
                          robj, start_date, end_date):
    """Lower-right panel: each platform's share of total mentions, one stacked bar.

    Returns `platform_totals_df` (Count / Percentage per platform).
    """
    plat_totals = platform_data.groupby('Media').sum().sort_values(ascending=False)
    # The notebook read a module-global `plat_data` for this total. Every call
    # site passed that same object in as `platform_data`, so summing the
    # per-platform totals is the identical number, without the free variable.
    plat_grand_total = plat_totals.sum()
    plat_pct_total = (plat_totals / plat_grand_total) * 100

    legend_handles = [plt.Rectangle((0, 0), 1, 1, color=plat_colors[p])
                      for p in plat_pct_total.index]
    legend_labels = [f'{p}:{int(plat_totals[p]):,} ({plat_pct_total[p]:.1f}%)'
                     for p in plat_totals.index]

    left_br = 0
    bar_height_br = 0.6
    for plat in plat_totals.index:
        value = plat_pct_total[plat]
        ax.barh(0, value, left=left_br, height=bar_height_br,
                color=plat_colors[plat], edgecolor='white', linewidth=0.5)
        if value >= 5:
            ax.text(left_br + value / 2, 0, f'{value:.1f}%',
                    ha='center', va='center', color='white',
                    fontsize=20, fontweight='bold')
        left_br += value

    ax.set_xlim(0, 100)
    ax.set_title(f'Platform Contribution Share of {robj}\n {start_date} - {end_date}',
                 fontsize=20, fontweight='semibold')
    ax.set_yticks([])
    ax.set_xlabel('Share of Mentions (%)', fontsize=12)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.legend(legend_handles, legend_labels,
              loc='upper center', bbox_to_anchor=(0.5, -0.15),
              ncol=4, frameon=False, fontsize=18)

    return pd.DataFrame({
        'Count': plat_totals,
        'Percentage': plat_pct_total,
    })


def weekly_overview(ps_data, platform_data, sentiment_data,
                    robj, start_date, end_date,
                    plat_class=None, sent_class=None,
                    plat_colors=None, sent_colors=None,
                    show=True):
    """Three-panel weekly overview.

    Left (full height) sentiment share per media, top right overall sentiment
    share, bottom right platform contribution share.

    Parameters
    ----------
    ps_data : long frame with [Media, Sentiment, Count] -- from `prep.plat_sent_data`.
        The notebook version read this from a global; it is an explicit argument now.
    platform_data : Series named 'Count' indexed (Date, Media) -- from `prep.platform_data`.
    sentiment_data : wide frame, one column per sentiment -- from `prep.sentiment_data`.
    robj : research-object name, used in every panel title.
    start_date, end_date : pre-formatted period labels, from `prep.prepare_data`.
    plat_class, sent_class, plat_colors, sent_colors : default to the library
        vocabularies in `great.labels` / `great.palette`.
    show : call `plt.show()` before returning.

    Returns
    -------
    (sent_pct_df, platform_totals_df)
    """
    plat_class = labels.plat_class if plat_class is None else plat_class
    sent_class = labels.sent_class if sent_class is None else sent_class
    plat_colors = palette.plat_colors if plat_colors is None else plat_colors
    sent_colors = palette.sent_colors if sent_colors is None else sent_colors

    fig = plt.figure(figsize=(30, 7))
    gs = fig.add_gridspec(2, 2, width_ratios=[0.9, 1], height_ratios=[1.2, 1])

    ax_left = fig.add_subplot(gs[:, 0])
    ax_tr = fig.add_subplot(gs[0, 1])
    ax_br = fig.add_subplot(gs[1, 1])

    _panel_media_sentiment(ax_left, ps_data, plat_class, sent_class, sent_colors,
                           robj, start_date, end_date)
    sent_pct_df = _panel_overall_sentiment(ax_tr, sentiment_data, sent_class,
                                           sent_colors, robj, start_date, end_date)
    platform_totals_df = _panel_platform_share(ax_br, platform_data, plat_colors,
                                               robj, start_date, end_date)

    plt.tight_layout()
    if show:
        plt.show()

    return sent_pct_df, platform_totals_df


def monthly_overview(ps_data, platform_data, sentiment_data,
                     robj, start_date, end_date, interval,
                     plat_class=None, sent_class=None,
                     plat_colors=None, sent_colors=None,
                     show=True):
    """Four-panel monthly overview: `weekly_overview` plus a sentiment trend on top.

    Same arguments as `weekly_overview`, plus:

    interval : day spacing for the trend panel's x-axis ticks (`mdates.DayLocator`).

    Returns
    -------
    (sent_pct_df, platform_totals_df)
    """
    plat_class = labels.plat_class if plat_class is None else plat_class
    sent_class = labels.sent_class if sent_class is None else sent_class
    plat_colors = palette.plat_colors if plat_colors is None else plat_colors
    sent_colors = palette.sent_colors if sent_colors is None else sent_colors

    fig = plt.figure(figsize=(30, 14))
    gs = fig.add_gridspec(3, 2, width_ratios=[0.9, 1], height_ratios=[0.8, 0.3, 0.3])

    ax_top = fig.add_subplot(gs[0, :])
    ax_left = fig.add_subplot(gs[1:, 0])
    ax_tr = fig.add_subplot(gs[1, 1])
    ax_br = fig.add_subplot(gs[2, 1])

    _panel_sentiment_trend(ax_top, sentiment_data, sent_class, sent_colors,
                           robj, start_date, end_date, interval)
    _panel_media_sentiment(ax_left, ps_data, plat_class, sent_class, sent_colors,
                           robj, start_date, end_date)
    sent_pct_df = _panel_overall_sentiment(ax_tr, sentiment_data, sent_class,
                                           sent_colors, robj, start_date, end_date)
    platform_totals_df = _panel_platform_share(ax_br, platform_data, plat_colors,
                                               robj, start_date, end_date)

    plt.tight_layout()
    if show:
        plt.show()

    return sent_pct_df, platform_totals_df
