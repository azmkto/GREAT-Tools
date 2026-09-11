"""Indonesian social-media text cleaning module for the 'great' library.

Three cleaners are exposed:
- `clean_for_bert()`: Keeps case, punctuation, and stopwords. Fixes encoding, strips URLs/@mentions,
  unwraps hashtags, and normalises slang.
- `clean_for_topics()`: Lowercases, strips non-letters, removes stopwords (Sastrawi + NLTK + TOPIC_STOPWORDS_BASE),
  and normalises slang.
- `clean_for_wordcloud()`: Extends `clean_for_topics()` with `WORDCLOUD_STOPWORDS_EXTRA`.
"""

import html
import re
from typing import Iterable, Optional, Set

# ==============================================================================
# 1. DICTIONARIES & STOPWORD SETS
# ==============================================================================

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
    "liat": "lihat", "abis": "habis", "ngutang": "utang",
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
    # Figurative & negation
    "kayanya": "sepertinya", "kykny": "sepertinya", "emgnya": "memangnya",
    "kaga": "tidak", "kagak": "tidak", "ngga": "tidak", "enggak": "tidak", "tak": "tidak",
    # Question words
    "napa": "kenapa", "ngapain": "sedang apa", "ngapa": "kenapa",
    "gmana": "bagaimana", "gimana": "bagaimana",
    # Pronouns
    "ente": "kamu", "situ": "kamu", "elu": "kamu", "elo": "kamu",
    "gua": "saya", "gwa": "saya", "ane": "saya", "aq": "saya",
    # Time
    "skrng": "sekarang", "skarang": "sekarang", "bsk": "besok",
    "kmrn": "kemarin", "kemaren": "kemarin", "td": "tadi",
    "entar": "nanti", "ntar": "nanti", "nti": "nanti", "detik2": "detik-detik",
    # Relationships
    "dpt": "dapat", "dapet": "dapat", "tggl": "tinggal", "tinggl": "tinggal",
    "tmn": "teman", "temen": "teman", "sm2": "sama-sama", "sama2": "sama-sama",
    # Truth & reality
    "trnyata": "ternyata", "ternyta": "ternyata",
    "sbnrnya": "sebenarnya", "sebenernya": "sebenarnya", "sbnernya": "sebenarnya",
    "bener": "benar", "beneran": "benar",
    # Connectives
    "sbg": "sebagai", "sbgai": "sebagai", "trhdp": "terhadap", "thd": "terhadap", "thdp": "terhadap",
    "diantaranya": "di antaranya", "diantara": "di antara", "meski": "meskipun", "jgnkan": "jangankan",
    # Colloquial verbs
    "ngerti": "mengerti", "ngerasa": "merasa", "berasa": "terasa",
    "keliatan": "terlihat", "keliatannya": "terlihatnya",
    "nyari": "mencari", "nyoba": "mencoba", "nunggu": "menunggu",
    "ngasih": "memberi", "ngajak": "mengajak", "ngobrol": "berbicara",
    "nyadar": "sadar", "ngerasain": "merasakan", "ngebayangin": "membayangkan",
    "mikir": "berpikir", "mikirin": "memikirkan", "ngomongin": "membicarakan",
    # Emotions
    "kesel": "kesal", "sebel": "sebal", "capek": "lelah", "cape": "lelah",
    "males": "malas", "mager": "malas gerak", "seneng": "senang",
    # Intensifiers
    "parah": "sangat", "gila": "sangat", "anjir": "sangat", "anjay": "sangat",
    "sangattt": "sangat", "bangettt": "banget", "banget2": "banget",
    "makin": "semakin", "kian": "semakin",
    # Quality & judgement
    "mantap": "bagus", "mantul": "bagus", "keren": "bagus",
    "jelek": "buruk", "ancur": "hancur", "ngeri": "mengerikan", "serem": "menyeramkan",
    "bego": "bodoh", "goblok": "bodoh", "tolol": "bodoh", "bodo": "bodoh",
    "songong": "sombong", "belagu": "sombong",
    # Communication
    "curhat": "curahan hati", "japri": "pesan pribadi", "japrii": "pesan pribadi",
    # Political & crime discourse
    "pemrintah": "pemerintah", "korup": "korupsi", "dikorupsi": "korupsi", "ngorupsi": "korupsi",
    "nyolong": "mencuri", "maling": "pencuri",
    "boong": "bohong", "bohong2": "bohong", "hoax": "hoaks", "hoak": "hoaks",
    "settingan": "rekayasa", "settingannya": "rekayasa", "php": "janji palsu",
    "ngamuk": "marah", "murka": "marah",
    # Misc typos
    "emank": "memang", "emangnya": "memangnya", "makannya": "makanya",
    "yng": "yang", "dngan": "dengan", "utuk": "untuk",
    "smpai": "sampai", "sampe": "sampai", "bwt": "buat", "buatt": "buat",
    "jgnlah": "janganlah", "tuhh": "tuh", "sihh": "sih", "dehh": "deh",
}

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
    'kompascom', 'viralvideo', 'shortvideo', 'youtubeshorts', 'beritaviral', 'trending',
    'foryou', 'short', 'like', 'jagaindonesia', 'anutin', 'live', 'chat', 'streaming',
    'audio', 'komen', 'komentar', 'yuk', 'cek', 'baca', 'bantu', 'update', 'store',
    'quot', 'klik', 'tonton', 'simak', 'tok', 'day', 'ipo', 'panggil', 'mulu', 'kek',
    'rang', 'suruh', 'loh', 'lho', 'youtube', 'facebook', 'tiktok', 'instagram',
    'viralshorts', 'part', 'shortvids', 'lambesahamjja', 'ardisatriawan', 'tempodotco',
    'detikcom', 'tribunnewscom', 'kumparancom', 'sindonewscom', 'beritasatucom',
    'liputan6dotcom', 'okezonecom', 'merdeka', 'vivaid', 'suara', 'jpnnpic',
    'killingmaster', 'nye', 'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'sabtu', 'minggu',
    'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus',
    'september', 'oktober', 'november', 'desember', 'indonesia', 'nasional', 'bangsa',
    'masyarakat', 'publik', 'dunia', 'isu', 'momen', 'terbaru', 'terbaik', 'langkah',
    'kinerja', 'memperkuat', 'menjaga', 'pertemuan', 'terkait', 'terbuka', 'eks',
    'kena', 'kau', 'coba', 'doang', 'gara', 'mah', 'sok', 'pas', 'hati', 'mic',
    'takut', 'allah', 'geger',
}

WORDCLOUD_STOPWORDS_EXTRA = {
    'prabowo', 'presiden', 'subianto', 'pemerintah', 'president',
    'indonesia', 'nasional', 'bangsa', 'masyarakat', 'publik', 'dunia', 'isu',
    'momen', 'terbaru', 'terbaik', 'langkah', 'kinerja', 'memperkuat', 'menjaga',
    'pertemuan', 'terkait', 'terbuka', 'eks',
}

# ==============================================================================
# 2. PRE-COMPILED REGEX PATTERNS (PERFORMANCE OPTIMIZATION)
# ==============================================================================

RE_URL = re.compile(r"http\S+|www\.\S+")
RE_MENTION = re.compile(r"@\w+")
RE_URL_MENTION = re.compile(r"http\S+|www\.\S+|@\w+")
RE_HASHTAG_KEEP = re.compile(r"#(\w+)")
RE_CAMELCASE = re.compile(r"(?<!^)(?=[A-Z])")
RE_NON_ALPHA = re.compile(r"[^a-z\s]")
RE_WHITESPACE = re.compile(r"\s+")

# Build regex pattern for exact slang replacement
SLANG_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(key) for key in sorted(SLANG.keys(), key=len, reverse=True)) + r")\b"
)

_stopwords_tm_cache: Optional[Set[str]] = None


# ==============================================================================
# 3. HELPER FUNCTIONS
# ==============================================================================

def normalize_slang(text: str) -> str:
    """Replace known Indonesian slang/abbreviations using `SLANG` mapping."""
    if not text:
        return ""
    return SLANG_PATTERN.sub(lambda m: SLANG[m.group(0)], text)


def _load_topic_stopwords() -> Set[str]:
    """Lazy loader for NLTK, PySastrawi, and base stopwords."""
    global _stopwords_tm_cache
    if _stopwords_tm_cache is not None:
        return _stopwords_tm_cache

    try:
        from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
        import nltk
        from nltk.corpus import stopwords as nltk_stopwords
    except ImportError as e:
        raise ImportError(
            "clean_for_topics() / clean_for_wordcloud() require 'nltk' and 'PySastrawi': "
            "install via `pip install \"great[text]\"` or `pip install nltk PySastrawi`."
        ) from e

    try:
        nltk_stopwords.words('indonesian')
    except LookupError:
        nltk.download('stopwords', quiet=True)

    words = set(StopWordRemoverFactory().get_stop_words())
    words |= set(nltk_stopwords.words('indonesian'))
    words |= set(nltk_stopwords.words('english'))
    words |= TOPIC_STOPWORDS_BASE

    _stopwords_tm_cache = {w.lower() for w in words if w}
    return _stopwords_tm_cache


def _split_camelcase_hashtag(match: re.Match) -> str:
    """Unwrap camelCase/PascalCase hashtags (#JagaIndonesia -> Jaga Indonesia)."""
    return RE_CAMELCASE.sub(' ', match.group(1))


def _clean_with_stopwords(text: str, stopwords: Set[str]) -> str:
    """Core cleaning pipeline shared by `clean_for_topics()` and `clean_for_wordcloud()`."""
    if not isinstance(text, str) or not text.strip():
        return ""

    text = html.unescape(text)
    text = RE_URL_MENTION.sub(" ", text)
    text = RE_HASHTAG_KEEP.sub(_split_camelcase_hashtag, text)
    text = text.lower()
    text = RE_NON_ALPHA.sub(" ", text)
    text = normalize_slang(text)

    # Token filtering: drop stopwords and short words <= 2 chars
    tokens = [w for w in text.split() if w not in stopwords and len(w) > 2]
    return " ".join(tokens)


# ==============================================================================
# 4. EXPOSED CLEANERS
# ==============================================================================

def clean_for_bert(text: str) -> str:
    """Clean text for transformer input (e.g., IndoBERT).

    Keeps case, punctuation, and stopwords. Fixes encoding, strips URLs/@mentions,
    unwraps hashtags, and normalises slang.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    try:
        import ftfy
    except ImportError as e:
        raise ImportError(
            "clean_for_bert() requires ftfy: install via `pip install ftfy` or `pip install \"great[text]\"`"
        ) from e

    text = ftfy.fix_text(text)
    text = html.unescape(text)
    text = RE_URL.sub(" ", text)
    text = RE_MENTION.sub(" ", text)
    text = RE_HASHTAG_KEEP.sub(r"\1", text)
    text = RE_WHITESPACE.sub(" ", text).strip()
    return normalize_slang(text)


def clean_for_topics(text: str, extra_stopwords: Optional[Iterable[str]] = None) -> str:
    """Clean text for BERTopic / clustering input.

    Lowercases, strips non-letters, normalises slang, and removes stopwords.
    """
    base_stopwords = _load_topic_stopwords()

    if extra_stopwords:
        # Create a shallow copy to prevent mutating the global cached set
        effective_stopwords = base_stopwords | {w.lower() for w in extra_stopwords}
    else:
        effective_stopwords = base_stopwords

    return _clean_with_stopwords(text, effective_stopwords)


def clean_for_wordcloud(text: str, extra_stopwords: Optional[Iterable[str]] = None) -> str:
    """Clean text for word clouds.

    Extends topic stopwords with `WORDCLOUD_STOPWORDS_EXTRA` (actor names & generic political filler).
    """
    base_stopwords = _load_topic_stopwords()
    effective_stopwords = base_stopwords | WORDCLOUD_STOPWORDS_EXTRA

    if extra_stopwords:
        effective_stopwords = effective_stopwords | {w.lower() for w in extra_stopwords}

    return _clean_with_stopwords(text, effective_stopwords)
