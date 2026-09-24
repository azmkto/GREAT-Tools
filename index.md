---
title: GREAT Big Data Analysis Program
type: project
status: active
started: 2026-09-07
category: []
working_dir: "GREAT Big Data Analysis Program/"
tags: [project-node]
---

# GREAT Big Data Analysis Program

Project node. Linked from notes as `[[great-tools]]`.

## Scope

The `great` Python package — shared infrastructure for GREAT's social-media research
notebooks. It is not itself a research question; it is the label vocabulary, colour
palette, text-cleaning rules, environmental-issue classifier, province geography, and
weekly/monthly visualization helpers that used to be copy-pasted across
[[ihsg-narratives]], [[topic-modelling]], [[prabowos-2nd-years]],
[[weekly-monthly-visualization]] and others. Published as `azmkto/GREAT-Tools` on
GitHub and installed with `pip install -e ".[all]"` (or `git+https://...` on Colab).

## Where the work lives

Everything is under this folder — this is one of the few projects that *is* its own
repo rather than pointing elsewhere:

- `great/` — the package: `labels.py`, `palette.py`, `schema.py`, `text.py`,
  `issues.py`, `geo.py`, `viz/` (`prep`, `checks`, `overview`, `wordcloud`,
  `environment`, `style`)
- `Weekly Visualization/`, `Monthly Visualization/`, `Environment Visualization/` —
  worked end-to-end example notebooks
- `tools/build_regions.py` — builds the province gazetteer
- `README.md`, `TUTORIAL.md`, `CONTRIBUTING.md`, `CHANGELOG.md`

## Consumers

Every other monitoring/analysis project in `projects/` depends on this package for
sentiment/platform class vocab, colour palettes, the 13-column export schema, and the
weekly/monthly overview plots. A breaking change here (e.g. the 0.3.2 `viz.checks`
rename) ripples into all of them — check `CHANGELOG.md`'s Breaking sections before
bumping the pin in a downstream notebook.

## Open threads

- (add as they come up)
