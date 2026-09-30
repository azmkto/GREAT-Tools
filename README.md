# **GREAT Big Data Analysis Program**

## **Introduction**
The Python package inside the **GREAT-Tools** repository. Shared utilities made by Big Data and Information Desk of GREAT Institute for the label vocabulary, color palette, text cleaning, environmental-issue rules, province geography, and the weekly/monthly visualization helpers that used to be copy-pasted across all the projects
## **Current Status**
The library is still under development and there are many things ahead to come since the disruption of AI hits really hard and need to adapt. Current change consists:
1. Finalize `topic_modelling.ipynb` using BERTopic and embedded with local LLM (Stable per 30 September 2026).
2. 

## Install

Clone, then install from the clone (editable — picks up edits without reinstalling):

```bash
git clone https://github.com/azmkto/GREAT-Tools.git
cd GREAT-Tools
py -3.11 -m pip install -e ".[all]"
```

Once installed, `import great` works from **any** notebook in any folder on your machine —
no `sys.path` code needed, and `git pull` is the whole update procedure.

`[all]` pulls every extra. To be selective: `text` (ftfy, nltk, PySastrawi), `ml`
(scikit-learn), `viz` (matplotlib, scienceplots, wordcloud, seaborn, plotly — and `ml`),
`geo` (geopandas, shapely, requests — for the Indonesia choropleth reports).
`great.viz` imports its dependencies at module level, so `[viz]` is required for any plotting;
plain `import great` needs none of them.

On a Colab runtime — including VS Code attached to one — install from GitHub instead:

```python
%pip install -q "great[all] @ git+https://github.com/azmkto/GREAT-Tools.git"
```

See [TUTORIAL.md §1](TUTORIAL.md) for all three environments.

## Docs

| | |
|---|---|
| [TUTORIAL.md](TUTORIAL.md) | Installing and using the library — local, VS Code + Colab extension, and Colab |
| [CONTRIBUTING.md](CONTRIBUTING.md) | For collaborators: getting the latest, and getting your changes in |
| [CHANGELOG.md](CHANGELOG.md) | What changed in each version, and what it breaks |

## Use

The common symbols are re-exported at the top level:

```python
from great import sent_class, plat_class, MEDIA_MAP, normalize_majas
from great import sent_colors, plat_colors, emo_colors
from great import validate_export, classify_issue
from great import PROVINCE_FIX, PULAU_MAP, GEO_FIX
```

`text` and `viz` are imported from their own modules, so the core package stays usable
without their dependencies installed:

```python
from great.text import clean_for_bert, clean_for_topics
from great.viz import prep, checks, wordcloud
from great.viz.style import apply_style
from great.viz.overview import weekly_overview, monthly_overview
from great.viz.wordcloud import sentiment_wordclouds
```

Worked end-to-end examples live in
[`Weekly Visualization/example_weekly_with_great.ipynb`](Weekly%20Visualization/example_weekly_with_great.ipynb)
and
[`Monthly Visualization/example_monthly_with_great.ipynb`](Monthly%20Visualization/example_monthly_with_great.ipynb).

## Modules

| Module | Contents |
|---|---|
| `labels.py` | Sentiment/platform/emotion class lists, `MEDIA_MAP`, majas label normalisation |
| `palette.py` | `sent_colors`, `plat_colors`, `emo_colors` and shared plot-size constants |
| `schema.py` | The canonical 13-column export schema and `validate_export()` |
| `text.py` | `SLANG`, stopword sets, `clean_for_bert()`, `clean_for_topics()` — needs `[text]` |
| `issues.py` | Environmental issue keyword rules and `classify_issue()` |
| `geo.py` | 1,243-entry gazetteer on official BPS codes, `resolve()`, `resolve_frame()`, province fixes, province→island mapping |
| `viz/prep.py` | `prepare_data()`, `sentiment_data()`, `platform_data()`, `plat_sent_data()` |
| `viz/checks.py` | `frame_info()`, `share()`, and the `completeness()`, `coverage()`, `composition()`, `author()`, `labels()` load-time reports |
| `viz/overview.py` | `daily_overview()`, `weekly_overview()`, `monthly_overview()`, plus the daily data steps `keyword_tiles()`, `representative_posts()`, `author_sentiment()` — needs `[viz]` |
| `viz/wordcloud.py` | `sentiment_wordclouds()`, `distinctive_terms()`, `tfidf_matrix()`, `ramp()` — needs `[viz]` |
| `viz/environment.py` | `env_daily()`, `env_weekly()`, `env_monthly()`, `dominant_issue()`, `province_counts()`, `island_counts()` — needs `[geo]` |
| `viz/style.py` | `apply_style()` — SciencePlots defaults |

See [TUTORIAL.md](TUTORIAL.md) for the full guide.
