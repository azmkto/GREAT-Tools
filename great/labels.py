"""Canonical label vocabularies used across projects.

Several projects spelled the same category differently — lowercase vs capitalised
sentiment, `News` vs `Media Mainstream`, `Threads` vs `Thread` (see EVALUATION.md
section 5.2). The values here are the canonical spelling; `MEDIA_MAP` normalises the
raw export's platform column into it.
"""
import numpy as np
import pandas as pd

sent_class = ['positive', 'negative', 'neutral']

plat_class = ['News', 'Facebook', 'Twitter', 'Youtube', 'Instagram', 'Tiktok', 'Threads']

emo_class = ['joy', 'trust', 'fear', 'surprise',
             'sadness', 'disgust', 'anger', 'anticipation']

# Raw export platform spelling -> canonical plat_class spelling
MEDIA_MAP = {
    'Article': 'News',
    'Media Mainstream': 'News',
    'Thread': 'Threads',
}

# ---------------- majas (figurative-language) label normalisation ----------------
# From the Evolution Project majas classifier: collapses the raw annotation
# vocabulary down to the 4-class taxonomy the model is trained on. `literal` ->
# `penegasan` is an intentional taxonomy decision, not a bug — see that project's
# CLAUDE.md.

MAJAS_LABEL_FIX = {
    'sarkas': 'sarkasme',
}

MAJAS_LABEL_MAP = {
    'sarkasme':  'sindiran',
    'ironi':     'sindiran',
    'satire':    'sindiran',
    'sinisme':   'sindiran',
    'hiperbola': 'perbandingan',
    'simile':    'perbandingan',
    'metafora':  'perbandingan',
    'repetisi':  'penegasan',
    'retoris':   'penegasan',
    'skeptis':   'penegasan',
    'kritik':    'penegasan',
    'literal':   'penegasan',
}


def normalize_majas(text):
    """Collapse a raw majas annotation to the 4-class taxonomy, or NaN for NaN in."""
    if pd.isna(text):
        return np.nan
    word = str(text).strip().lower()
    word = MAJAS_LABEL_FIX.get(word, word)
    word = MAJAS_LABEL_MAP.get(word, word)
    return word
