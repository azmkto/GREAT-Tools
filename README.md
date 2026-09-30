# **GREAT Big Data Analysis Program**

## **Introduction**
The Python package inside the **GREAT-Tools** repository. Shared utilities made by Big Data and Information Desk of GREAT Institute for the label vocabulary, color palette, text cleaning, environmental-issue rules, province geography, and the weekly/monthly visualization helpers that used to be copy-pasted across all the projects
## **Current Status**
The library is still under development and there are many things ahead to come since the disruption of AI hits really hard and need to adapt. Current change consists:
1. Finalize `topic_modelling.ipynb` using BERTopic and embedded with local LLM (Stable per 30 September 2026).
2. Finalize `daily_report_notebook.ipynb` and `report_notebook.ipynb` as reusable notebook to visualize daily report needs and weekly-monthly needs (Stable per 30 September 2026).
3. Still refining the author network extractor and 

## Install

Since the repository is now public, all you need just to install it like this (either locally or just in the current session):

```bash
pip install -q "great[all] @ git+https://github.com/azmkto/GREAT-Tools.git"
```

Add (`%` or `!` before the `pip` if you use IDE and/or colab runtime). Once installed, `import great` works from **any** notebook in anywhere.

`[all]` pulls every extra. To be selective: `text` (ftfy, nltk, PySastrawi), `ml`
(scikit-learn), `viz` (matplotlib, scienceplots, wordcloud, seaborn, plotly — and `ml`),
`geo` (geopandas, shapely, requests — for the Indonesia choropleth reports).
`great.viz` imports its dependencies at module level, so `[viz]` is required for any plotting;
plain `import great` needs none of them.

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

For the working example could be seen in the `Notebook` folder.

## Modules

| Module               | Contents                                                                                                                                                                   |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `labels.py`          | Sentiment/platform/emotion class lists, `MEDIA_MAP`, majas label normalisation                                                                                             |
| `palette.py`         | `sent_colors`, `plat_colors`, `emo_colors` and shared plot-size constants                                                                                                  |
| `schema.py`          | The canonical 13-column export schema and `validate_export()`                                                                                                              |
| `text.py`            | `SLANG`, stopword sets, `clean_for_bert()`, `clean_for_topics()` — needs `[text]`                                                                                          |
| `issues.py`          | Environmental issue keyword rules and `classify_issue()`                                                                                                                   |
| `geo.py`             | 1,243-entry gazetteer on official BPS codes, `resolve()`, `resolve_frame()`, province fixes, province→island mapping                                                       |
| `viz/prep.py`        | `prepare_data()`, `sentiment_data()`, `platform_data()`, `plat_sent_data()`                                                                                                |
| `viz/checks.py`      | `frame_info()`, `share()`, and the `completeness()`, `coverage()`, `composition()`, `author()`, `labels()` load-time reports                                               |
| `viz/overview.py`    | `daily_overview()`, `weekly_overview()`, `monthly_overview()`, plus the daily data steps `keyword_tiles()`, `representative_posts()`, `author_sentiment()` — needs `[viz]` |
| `viz/wordcloud.py`   | `sentiment_wordclouds()`, `distinctive_terms()`, `tfidf_matrix()`, `ramp()` — needs `[viz]`                                                                                |
| `viz/environment.py` | `env_daily()`, `env_weekly()`, `env_monthly()`, `dominant_issue()`, `province_counts()`, `island_counts()` — needs `[geo]`                                                 |
| `viz/style.py`       | `apply_style()` — SciencePlots defaults                                                                                                                                    |

See [TUTORIAL.md](TUTORIAL.md) for the full guide.
