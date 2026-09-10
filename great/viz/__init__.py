"""Weekly / monthly visualization helpers.

Extracted from `pol_weekly_viz.ipynb` and `pol_monthly_viz.ipynb`, which held
byte-identical copies of most of this.

Everything this subpackage needs is imported for you -- one import gets the whole
toolkit, no separate `from wordcloud import WordCloud` or `import scienceplots` in the
notebook:

    from great.viz import prep, checks, wordcloud
    from great.viz import apply_style, weekly_overview, monthly_overview, sentiment_wordclouds

Needs the `[viz]` extra (`matplotlib`, `scienceplots`, `wordcloud`, `scikit-learn`) and,
because the word cloud cleans through `great.text`, the `[text]` libraries too. Install
both at once with `pip install -e "<repo>[viz,text]"`.

This subpackage is deliberately not imported by `great/__init__.py`, so `import great`
still works in a text-only or headless environment without any of the above installed.
"""

from . import checks, prep, style, wordcloud
from .overview import monthly_overview, weekly_overview
from .style import apply_style
from .wordcloud import (
    distinctive_terms,
    prepare_corpus,
    ramp,
    sentiment_wordclouds,
    tfidf_matrix,
)

__all__ = [
    # submodules
    "checks", "prep", "style", "wordcloud",
    # style
    "apply_style",
    # overview figures
    "weekly_overview", "monthly_overview",
    # word cloud pipeline
    "sentiment_wordclouds", "prepare_corpus", "tfidf_matrix",
    "distinctive_terms", "ramp",
]
