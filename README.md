# riset

Shared utilities for azmkto's social-media research notebooks — one place for the
label vocabulary, color palette, text cleaning, environmental-issue rules, and province
geography that used to be copy-pasted across `Evolution Project`, `Topic Modelling Trial`,
`IHSG Narratives`, `Weekly Monthly Visualization Program`, and friends.

## Install

Local (editable, picks up edits without reinstalling):

```bash
pip install -e "C:\path\to\Research Project\Library"
```

Colab / anywhere else, once this is pushed to GitHub:

```python
%pip install git+https://github.com/azmkto/riset.git -q
```

## Use

```python
from riset.labels import sent_class, plat_class, MEDIA_MAP, normalize_majas
from riset.palette import sent_colors, plat_colors, emo_colors
from riset.text import clean_for_bert, clean_for_topics
from riset.issues import classify_issue
from riset.geo import PROVINCE_FIX, PULAU_MAP, GEO_FIX
from riset.schema import validate_export
```

## Modules

| Module | Contents |
|---|---|
| `labels.py` | Sentiment/platform/emotion class lists, `MEDIA_MAP`, majas label normalisation |
| `palette.py` | `sent_colors`, `plat_colors`, `emo_colors` and shared plot-size constants |
| `schema.py` | The canonical 13-column export schema and `validate_export()` |
| `text.py` | `SLANG`, stopword sets, `clean_for_bert()`, `clean_for_topics()` |
| `issues.py` | Environmental issue keyword rules and `classify_issue()` |
| `geo.py` | Province name fixes and province→island mapping |
