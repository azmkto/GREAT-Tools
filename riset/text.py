"""Indonesian social-media text cleaning.

`SLANG` is the same dictionary that used to be copy-pasted verbatim into five
notebooks across four projects (`TM_LLM_CPU.ipynb`, `sn_needs.ipynb`,
`TM_LLM_Trial.ipynb`, `RUUPA_Notebook.ipynb`, `Demo_27_Agustus_Notebook.ipynb`, plus
separately in the three Evolution Project notebooks).

`TOPIC_STOPWORDS_BASE` deliberately excludes subject-specific noise that was mixed
into the original list (a politician's name and its compounds, one campaign
hashtag, two usernames) — pass those per project via `clean_for_topics(...,
extra_stopwords={...})` instead of baking one project's subject into every project.

Two cleaners are exposed on purpose, matching two different real requirements in
the source notebooks — this was previously invisible because both were called
`clean()` in different files:

- `clean_for_bert()` — for transformer input (IndoBERT etc). Keeps case,
  punctuation, and stopwords, because the transformer's own tokenizer needs them.
  Only fixes encoding, strips URLs/@mentions, unwraps hashtags, and normalises slang.
- `clean_for_topics()` — for BERTopic / clustering input. Also lowercases, strips
  everything that isn't a letter, and removes stopwords (Sastrawi + NLTK Indonesian
  + NLTK English + a hand-tuned social-media noise list), because topic clustering
  wants content words only.

`clean_for_topics()` needs `nltk` and `PySastrawi`; `clean_for_bert()` needs `ftfy`.
Neither is a hard dependency of `riset` itself — install with `pip install
"riset[text]"` to get both, or install them yourself if you only need one cleaner.
"""
import html
import re

SLANG = {
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "tdk": "tidak",
    "bgt": "banget", "yg": "yang", "krn": "karena", "krna": "karena", "karna": "karena",
    "sm": "sama", "utk": "untuk", "dr": "dari", "skrg": "sekarang",
    "dgn": "dengan", "dg": "dengan", "org": "orang",
    "tp": "tapi", "spt": "seperti", "kayak": "seperti", "kaya": "seperti", "kyk": "seperti",
    "blm": "belum", "jgn": "jangan", "emg": "memang", "emang": "memang",
    "jd": "jadi", "jg": "juga", "aja": "saja", "aj": "saja",
    "udah": "sudah", "udh": "sudah", "dah": "sudah",
    "gmn": "bagaimana", "knp": "kenapa", "kalo": "kalau", "klo": "kalau",
    "trs": "terus", "trus": "terus", "gini": "begini", "gitu": "begitu",
    "sy": "saya", "km": "kamu", "gw": "saya", "gue": "saya", "lo": "kamu", "lu": "kamu",
    "hrs": "harus", "bs": "bisa", "msh": "masih", "dlm": "dalam",
    "sblm": "sebelum", "stlh": "setelah", "pd": "pada", "pgn": "ingin", "pengen": "ingin",
    "liat": "lihat", "abis": "habis",

    "bkn": "bukan", "gpp": "tidak apa-apa", "gapapa": "tidak apa-apa", "gaada": "tidak ada",
    "cmn": "cuma", "cuman": "cuma",
    "mksh": "terima kasih", "makasih": "terima kasih",
    "moga": "semoga", "smoga": "semoga",
    "wkt": "waktu", "cpt": "cepat", "lg": "lagi", "lgi": "lagi",
    "sll": "selalu", "sllu": "selalu", "prnh": "pernah",
    "sndiri": "sendiri", "stiap": "setiap", "byk": "banyak", "dikit": "sedikit",
    "dtg": "datang", "krg": "kurang", "ato": "atau",
    "pke": "pakai", "pake": "pakai", "kudu": "harus", "musti": "harus",
    "denger": "dengar", "kasih": "beri", "bikin": "buat",
    "brp": "berapa", "gmna": "bagaimana", "knpa": "kenapa",
    "walopun": "walaupun",

    # figurative-relevant — worth flagging separately, see note below
    "kayanya": "sepertinya", "kykny": "sepertinya", "emgnya": "memangnya",
    # extend this from your own corpus's most frequent non-dictionary tokens
}

# Social-media / broadcast noise for topic modelling — subject-specific terms
# (politician names etc.) live in TOPIC_STOPWORDS_EXTRA so callers can opt in or
# swap them per project instead of inheriting one project's subject into another's.
TOPIC_STOPWORDS_BASE = {
    'subscribe', 'shorts', 'channel', 'fyp', 'follow', 'com', 'www',
    'beritaterkini', 'selengkapnya', 'sumber', 'informasi', 'terkini',
    'resmi', 'news', 'video', 'viral', 'berita', 'media', 'sosial', 'rt', 'langsung',
    'ujarnya', 'tulis', 'termuat', 'menyatakan', 'menyebut', 'dinilai',
    'dilihat', 'disampaikan', 'mengatakan', 'sindonews', 'detik',
    'kompas', 'tribun', 'cnnindonesia', 'kumparan', 'tempo', 'nya', 'sih', 'nih', 'tuh',
    'deh', 'dong', 'kok', 'yah', 'lah', 'kan',
    'aja', 'udah', 'sdh', 'sampe', 'tau', 'gitu', 'gini', 'orang', 'bilang',
    'ngomong', 'lihat', 'pakai', 'banget', 'bgt', 'emang', 'kayak', 'kaya',
    'shortvideo', 'youtubeshorts', 'beritaviral', 'trending', 'foryou',
    'short', 'like', 'live', 'chat', 'streaming', 'audio', 'komen', 'komentar', 'yuk', 'cek',
    'baca', 'bantu', 'update', 'store', 'quot', 'klik', 'tonton', 'simak',

    # platform / format residue
    'youtube', 'facebook', 'tiktok', 'instagram', 'viralshorts', 'part',

    # calendar noise
    'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli',
    'agustus', 'september', 'oktober', 'november', 'desember',

    # colloquial residue / discourse particles
    'kena', 'kau', 'coba', 'doang', 'gara', 'mah', 'sok', 'pas', 'hati', 'mic',
    'takut', 'geger',
}

_stopwords_tm = None  # lazily built, cached


def normalize_slang(text: str) -> str:
    """Replace known Indonesian slang/abbreviations token-for-token via `SLANG`."""
    return " ".join(SLANG.get(w, w) for w in text.split())


def clean_for_bert(text) -> str:
    """Clean text for transformer input. Keeps case, punctuation, stopwords.

    Requires `ftfy` (`pip install ftfy` or `pip install "riset[text]"`).
    """
    if not isinstance(text, str):
        return ''
    try:
        import ftfy
    except ImportError as e:
        raise ImportError(
            "clean_for_bert() requires ftfy: pip install ftfy"
        ) from e

    text = ftfy.fix_text(text)                       # repair encoding artefacts
    text = re.sub(r"http\S+|www\.\S+", " ", text)     # URLs
    text = re.sub(r"@\w+", " ", text)                 # mentions
    text = re.sub(r"#(\w+)", r"\1", text)              # keep hashtag word, drop '#'
    text = re.sub(r"\s+", " ", text).strip()
    return normalize_slang(text)


def _load_topic_stopwords():
    global _stopwords_tm
    if _stopwords_tm is not None:
        return _stopwords_tm
    try:
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        import nltk
        from nltk.corpus import stopwords as nltk_stopwords
    except ImportError as e:
        raise ImportError(
            "clean_for_topics() requires nltk and PySastrawi: "
            'pip install nltk PySastrawi (or pip install "riset[text]")'
        ) from e

    try:
        nltk_stopwords.words('indonesian')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    words = set(StopWordRemoverFactory().get_stop_words())
    words |= set(nltk_stopwords.words('indonesian'))
    words |= set(nltk_stopwords.words('english'))
    words |= TOPIC_STOPWORDS_BASE
    _stopwords_tm = {w.lower() for w in words}
    return _stopwords_tm


def clean_for_topics(text, extra_stopwords=None) -> str:
    """Clean text for BERTopic / clustering input.

    Lowercases, strips everything but letters, normalises slang, and removes
    stopwords (Sastrawi + NLTK Indonesian + NLTK English + `TOPIC_STOPWORDS_BASE`,
    plus anything passed in `extra_stopwords`). Drops tokens of length <= 2.

    Requires `nltk` and `PySastrawi` (`pip install "riset[text]"`), downloaded once
    on first call.
    """
    if not isinstance(text, str):
        return ''
    stopwords_tm = _load_topic_stopwords()
    if extra_stopwords:
        stopwords_tm = stopwords_tm | {w.lower() for w in extra_stopwords}

    text = html.unescape(text)
    text = re.sub(r"http\S+|www\.\S+|@\w+", " ", text)                        # URLs + mentions
    text = re.sub(r"#(\w+)", lambda m: re.sub(r'(?<!^)(?=[A-Z])', ' ', m.group(1)), text)  # split CamelCase hashtags
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)                                     # punctuation, digits, emoji
    text = normalize_slang(text)
    return " ".join(w for w in text.split() if w not in stopwords_tm and len(w) > 2)
