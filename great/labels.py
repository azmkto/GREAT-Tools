"""Canonical label vocabularies used across projects.

Several projects spelled the same category differently — lowercase vs capitalised
sentiment, `News` vs `Media Mainstream`, `Threads` vs `Thread` (see EVALUATION.md
section 5.2). The values here are the canonical spelling; `MEDIA_MAP` normalises the
raw export's platform column into it.
"""
import re

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


# ---------------- news-outlet accounts ----------------
# `Media` in the export is the platform; outlet accounts also post on social platforms
# (detikcom on Twitter), and "who drives the conversation" analyses want people, not
# newsrooms. Every topic notebook carried its own copy of this list.

MEDIA_ACCOUNTS = {
    'detikcom', 'kompascom', 'cnnindonesia', 'tempodotco', 'antaranews',
    'cnbcindonesia', 'liputan6dotcom', 'liputan6', 'sctv', 'tvonenews', 'kumparan',
    'beritasatu', 'metrotvnews', 'tribunnews', 'republikaonline', 'suaradotcom',
    'jawapos', 'bbcindonesia', 'voaindonesia', 'narasitv', 'sindonews',
    'vivacoid', 'bisniscom', 'hariankompas', 'tirtoid', 'alineadotid',
    'inilahcom', 'merdekadotcom', 'okezone', 'idntimes', 'medcomid',
    'rri', 'tvri', 'jpnndotcom', 'grid', 'inewsdotid', 'fajar',
    'pikiranrakyat', 'gatra', 'nuonline', 'radioelshinta', 'mediaindonesia', 'setkabgoid',
    'awani', 'bharianmy', 'bernamadotcom', 'utusandotcom', 'sinarharian',
    'malaysiakini', 'thestar', 'nst', 'theedgemarkets',
    'rt', 'actualidadrt', 'rtcom', 'sputnik', 'sputniknews', 'sputnikindonesia',
    'tass', 'tassagency', 'rianovosti', 'ria', 'telesur', 'telesurtv',
}

MEDIA_ACCOUNT_KEYWORDS = ['news', 'media', 'redaksi', 'newsroom', 'official',
                          'humas', 'koran', 'gazette', 'radio']
# Short words only count at the end of a handle: as substrings, 'pers' caught
# 'persib_fans' and 'tv' caught 'tvstreamer'.
MEDIA_ACCOUNT_SUFFIXES = ('tv', 'pers', 'fm', 'dotcom', 'dotid', 'dotco', 'dotnet', 'dotorg')
MEDIA_DOMAIN_SUFFIXES = ('.com', '.id', '.co', '.net', '.org')


def is_media_account(author, platform=None, extra_accounts=()):
    """True for a news-outlet account. `extra_accounts` adds topic-specific handles
    without editing the shared list (an outlet in one topic can be an actor in another)."""
    if str(platform).strip() in ('News', 'Article', 'Media Mainstream'):
        return True
    raw = str(author).strip().lower().lstrip('@')
    norm = re.sub(r'[^a-z0-9]', '', raw)
    accounts = MEDIA_ACCOUNTS | {re.sub(r'[^a-z0-9]', '', str(a).lower()) for a in extra_accounts}
    return (norm in accounts
            or any(kw in raw for kw in MEDIA_ACCOUNT_KEYWORDS)
            or norm.endswith(MEDIA_ACCOUNT_SUFFIXES)
            or raw.endswith(MEDIA_DOMAIN_SUFFIXES))
