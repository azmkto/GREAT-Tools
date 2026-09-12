"""Unified province/location resolver.

Combines two stages that used to run separately:
1. Free-text location extraction via `LOCATION_TO_PROVINCE` (flashtext scan) —
   for headline/mentions text where a place name is buried mid-sentence.
2. `PROVINCE_FIX` spelling normalisation — a safety net applied to WHATEVER
   province name comes out of stage 1, or to an already-structured "Provinsi"
   column, so every downstream value ends up in the same canonical spelling
   regardless of which path produced it.

`PROVINCE_FIX` / `PULAU_MAP` / `GEO_FIX` moved from
`Weekly Monthly Visualization Program/app/config.py`.
`LOCATION_TO_PROVINCE` / `ISLAND_FALLBACK` extended after a manual review of
documents that fell through to "Tidak Terdeteksi" (see EVALUATION.md).
"""
import re
import numpy as np

# `flashtext` is imported lazily inside `_get_location_kp()`, not here. It is a hard
# dependency of this module's free-text scan, but `great/__init__.py` imports this module,
# so a module-level import would make a missing flashtext break `import great` entirely --
# including for people who only want the palette or the label vocabularies.
#
# Note flashtext 2.7 is from February 2018 and declares support only for Python 2.7/3.5/3.6.
# It is pure Python so it still runs, but it is unmaintained. If it ever breaks, the scan can
# be rebuilt as one alternation regex, the way `great/issues.py` and `great/text.py`'s
# `SLANG_PATTERN` already work.

# =========================================================
# STAGE 1 DATA: free-text location gazetteer
# =========================================================
LOCATION_TO_PROVINCE = {
    # ---------------- SUMATERA ----------------
    "aceh": "Aceh", "banda aceh": "Aceh", "sabang": "Aceh", "lhokseumawe": "Aceh",
    "langsa": "Aceh", "subulussalam": "Aceh", "pidie": "Aceh", "bireuen": "Aceh",
    "aceh besar": "Aceh", "aceh utara": "Aceh", "aceh timur": "Aceh", "aceh selatan": "Aceh",
    "leuser": "Aceh", "gunung leuser": "Aceh", "taman nasional gunung leuser": "Aceh",
    "krakatau": "Lampung", "gunung krakatau": "Lampung",
    "anak krakatau": "Lampung", "gunung anak krakatau": "Lampung",
    "selat sunda": "Lampung",

    "sumatera utara": "Sumatera Utara", "sumut": "Sumatera Utara", "medan": "Sumatera Utara",
    "binjai": "Sumatera Utara", "tebing tinggi": "Sumatera Utara", "pematangsiantar": "Sumatera Utara",
    "tanjungbalai": "Sumatera Utara", "sibolga": "Sumatera Utara", "padangsidempuan": "Sumatera Utara",
    "gunungsitoli": "Sumatera Utara", "deli serdang": "Sumatera Utara", "karo": "Sumatera Utara",
    "simalungun": "Sumatera Utara", "tapanuli": "Sumatera Utara", "toba": "Sumatera Utara", "nias": "Sumatera Utara",
    "danau toba": "Sumatera Utara", "sinabung": "Sumatera Utara", "gunung sinabung": "Sumatera Utara",
    "sibayak": "Sumatera Utara", "gunung sibayak": "Sumatera Utara", "nias selatan": "Sumatera Utara",

    "sumatera barat": "Sumatera Barat", "sumbar": "Sumatera Barat", "padang": "Sumatera Barat",
    "bukittinggi": "Sumatera Barat", "pariaman": "Sumatera Barat", "padang panjang": "Sumatera Barat",
    "payakumbuh": "Sumatera Barat", "sawahlunto": "Sumatera Barat", "solok": "Sumatera Barat",
    "agam": "Sumatera Barat", "tanah datar": "Sumatera Barat", "mentawai": "Sumatera Barat", "pesisir selatan": "Sumatera Barat",
    "danau singkarak": "Sumatera Barat", "danau maninjau": "Sumatera Barat", "marapi": "Sumatera Barat", "gunung marapi": "Sumatera Barat",

    "riau": "Riau", "pekanbaru": "Riau", "dumai": "Riau", "bengkalis": "Riau",
    "rokan hilir": "Riau", "rokan hulu": "Riau", "kampar": "Riau", "siak": "Riau",
    "pelalawan": "Riau", "kuantan singingi": "Riau", "indragiri hilir": "Riau", "indragiri hulu": "Riau",
    "sungai siak": "Riau", "sungai rokan": "Riau", "tesso nilo": "Riau", "rantau kopar": "Riau",

    "kepulauan riau": "Kepulauan Riau", "kepri": "Kepulauan Riau", "batam": "Kepulauan Riau",
    "tanjungpinang": "Kepulauan Riau", "bintan": "Kepulauan Riau", "karimun": "Kepulauan Riau",
    "lingga": "Kepulauan Riau", "natuna": "Kepulauan Riau", "anambas": "Kepulauan Riau",

    "jambi": "Jambi", "sungai penuh": "Jambi", "muaro jambi": "Jambi", "bungo": "Jambi",
    "merangin": "Jambi", "kerinci": "Jambi", "batanghari": "Jambi", "sarolangun": "Jambi", "tanjung jabung": "Jambi",
    "gunung kerinci": "Jambi", "taman nasional kerinci seblat": "Jambi", "danau kerinci": "Jambi",

    "sumatera selatan": "Sumatera Selatan", "sumsel": "Sumatera Selatan", "palembang": "Sumatera Selatan",
    "prabumulih": "Sumatera Selatan", "lubuklinggau": "Sumatera Selatan", "pagar alam": "Sumatera Selatan",
    "banyuasin": "Sumatera Selatan", "musi banyuasin": "Sumatera Selatan", "muara enim": "Sumatera Selatan",
    "lahat": "Sumatera Selatan", "ogan ilir": "Sumatera Selatan", "ogan komering ilir": "Sumatera Selatan",
    "oki": "Sumatera Selatan", "ogan komering ulu": "Sumatera Selatan", "oku": "Sumatera Selatan", "empat lawang": "Sumatera Selatan",
    "sungai musi": "Sumatera Selatan", "gunung dempo": "Sumatera Selatan", "sembilang": "Sumatera Selatan",

    "bangka belitung": "Kepulauan Bangka Belitung", "babel": "Kepulauan Bangka Belitung",
    "pangkalpinang": "Kepulauan Bangka Belitung", "bangka": "Kepulauan Bangka Belitung", "belitung": "Kepulauan Bangka Belitung",
    "bangka barat": "Kepulauan Bangka Belitung", "bangka selatan": "Kepulauan Bangka Belitung", "bangka tengah": "Kepulauan Bangka Belitung",

    "bengkulu": "Bengkulu", "rejanglebong": "Bengkulu", "rejang lebong": "Bengkulu",
    "seluma": "Bengkulu", "kaur": "Bengkulu", "mukomuko": "Bengkulu", "kepahiang": "Bengkulu", "lebong": "Bengkulu",

    "lampung": "Lampung", "bandar lampung": "Lampung", "metro": "Lampung", "pesawaran": "Lampung",
    "pringsewu": "Lampung", "tanggamus": "Lampung", "tulang bawang": "Lampung", "way kanan": "Lampung",
    "lampung selatan": "Lampung", "lampung tengah": "Lampung", "lampung utara": "Lampung", "lampung timur": "Lampung", "mesuji": "Lampung",
    "way kambas": "Lampung", "taman nasional way kambas": "Lampung", "bukit barisan selatan": "Lampung",

    # ---------------- JAWA ----------------
    "banten": "Banten", "tangerang": "Banten", "tangerang selatan": "Banten", "tangsel": "Banten",
    "cilegon": "Banten", "serang": "Banten", "lebak": "Banten", "pandeglang": "Banten",
    "ujung kulon": "Banten", "taman nasional ujung kulon": "Banten", "sawarna": "Banten",
    "serpong": "Banten", "bsd": "Banten", "ciputat": "Banten", "cikande": "Banten",
    "balaraja": "Banten", "curug": "Banten", "cikupa": "Banten",

    "jakarta": "DKI Jakarta", "dki": "DKI Jakarta", "dki jakarta": "DKI Jakarta",
    "jakarta selatan": "DKI Jakarta", "jaksel": "DKI Jakarta", "jakarta barat": "DKI Jakarta", "jakbar": "DKI Jakarta",
    "jakarta timur": "DKI Jakarta", "jaktim": "DKI Jakarta", "jakarta utara": "DKI Jakarta", "jakut": "DKI Jakarta",
    "jakarta pusat": "DKI Jakarta", "jakpus": "DKI Jakarta", "kepulauan seribu": "DKI Jakarta", "monas": "DKI Jakarta",

    "jawa barat": "Jawa Barat", "jabar": "Jawa Barat", "bandung": "Jawa Barat", "bandung barat": "Jawa Barat",
    "bogor": "Jawa Barat", "kabupaten bogor": "Jawa Barat", "kota bogor": "Jawa Barat",
    "depok": "Jawa Barat", "bekasi": "Jawa Barat", "kabupaten bekasi": "Jawa Barat", "cikarang": "Jawa Barat",
    "karawang": "Jawa Barat", "purwakarta": "Jawa Barat", "subang": "Jawa Barat", "indramayu": "Jawa Barat",
    "cirebon": "Jawa Barat", "majalengka": "Jawa Barat", "kuningan": "Jawa Barat", "sumedang": "Jawa Barat",
    "garut": "Jawa Barat", "tasikmalaya": "Jawa Barat", "ciamis": "Jawa Barat", "banjar": "Jawa Barat",
    "pangandaran": "Jawa Barat", "sukabumi": "Jawa Barat", "cianjur": "Jawa Barat", "cimahi": "Jawa Barat",
    "sungai citarum": "Jawa Barat", "citarum": "Jawa Barat", "ciliwung": "Jawa Barat", "jatiluhur": "Jawa Barat",
    "waduk jatiluhur": "Jawa Barat", "cirata": "Jawa Barat", "mount gede": "Jawa Barat", "gunung gede": "Jawa Barat",
    "gunung pangrango": "Jawa Barat", "tangkuban perahu": "Jawa Barat", "gunung ciremai": "Jawa Barat", "papandayan": "Jawa Barat",
    "tpa galuga": "Jawa Barat", "galuga": "Jawa Barat", "cibungbulang": "Jawa Barat",
    "cibinong": "Jawa Barat", "cileungsi": "Jawa Barat", "gunung putri": "Jawa Barat", "sentul": "Jawa Barat",
    "puncak bogor": "Jawa Barat", "jonggol": "Jawa Barat", "parung": "Jawa Barat", "sukmajaya": "Jawa Barat",
    "juanda raya": "Jawa Barat",

    "jawa tengah": "Jawa Tengah", "jateng": "Jawa Tengah", "semarang": "Jawa Tengah", "solo": "Jawa Tengah",
    "surakarta": "Jawa Tengah", "magelang": "Jawa Tengah", "pekalongan": "Jawa Tengah", "tegal": "Jawa Tengah",
    "salatiga": "Jawa Tengah", "brebes": "Jawa Tengah", "pemalang": "Jawa Tengah", "batang": "Jawa Tengah",
    "kendal": "Jawa Tengah", "demak": "Jawa Tengah", "jepara": "Jawa Tengah", "kudus": "Jawa Tengah",
    "pati": "Jawa Tengah", "rembang": "Jawa Tengah", "blora": "Jawa Tengah", "grobogan": "Jawa Tengah",
    "sragen": "Jawa Tengah", "karanganyar": "Jawa Tengah", "wonogiri": "Jawa Tengah", "sukoharjo": "Jawa Tengah",
    "klaten": "Jawa Tengah", "boyolali": "Jawa Tengah", "purworejo": "Jawa Tengah", "wonosobo": "Jawa Tengah",
    "temanggung": "Jawa Tengah", "banjarnegara": "Jawa Tengah", "purbalingga": "Jawa Tengah",
    "banyumas": "Jawa Tengah", "purwokerto": "Jawa Tengah", "cilacap": "Jawa Tengah", "kebumen": "Jawa Tengah",
    "dieng": "Jawa Tengah", "dataran tinggi dieng": "Jawa Tengah", "gunung merapi": "Jawa Tengah", "merapi": "Jawa Tengah",
    "gunung slamet": "Jawa Tengah", "gunung sindoro": "Jawa Tengah", "gunung sumbing": "Jawa Tengah", "rawa pening": "Jawa Tengah",

    "yogyakarta": "DI Yogyakarta", "jogja": "DI Yogyakarta", "diy": "DI Yogyakarta", "di yogyakarta": "DI Yogyakarta",
    "sleman": "DI Yogyakarta", "bantul": "DI Yogyakarta", "gunungkidul": "DI Yogyakarta", "gunung kidul": "DI Yogyakarta", "kulon progo": "DI Yogyakarta",
    "kaliurang": "DI Yogyakarta", "parangtritis": "DI Yogyakarta",
    "imogiri": "DI Yogyakarta", "wukirsari": "DI Yogyakarta",

    "jawa timur": "Jawa Timur", "jatim": "Jawa Timur", "surabaya": "Jawa Timur", "malang": "Jawa Timur",
    "batu": "Jawa Timur", "kediri": "Jawa Timur", "blitar": "Jawa Timur", "madiun": "Jawa Timur",
    "mojokerto": "Jawa Timur", "pasuruan": "Jawa Timur", "probolinggo": "Jawa Timur", "sidoarjo": "Jawa Timur",
    "gresik": "Jawa Timur", "bangkalan": "Jawa Timur", "sampang": "Jawa Timur", "pamekasan": "Jawa Timur",
    "sumenep": "Jawa Timur", "madura": "Jawa Timur", "tuban": "Jawa Timur", "bojonegoro": "Jawa Timur",
    "ngawi": "Jawa Timur", "magetan": "Jawa Timur", "ponorogo": "Jawa Timur", "pacitan": "Jawa Timur",
    "trenggalek": "Jawa Timur", "tulungagung": "Jawa Timur", "jombang": "Jawa Timur", "nganjuk": "Jawa Timur",
    "lumajang": "Jawa Timur", "jember": "Jawa Timur", "bondowoso": "Jawa Timur", "situbondo": "Jawa Timur",
    "banyuwangi": "Jawa Timur", "ijen": "Jawa Timur", "gunung bromo": "Jawa Timur", "bromo": "Jawa Timur",
    "gunung semeru": "Jawa Timur", "semeru": "Jawa Timur", "gunung kelud": "Jawa Timur", "gunung arjuno": "Jawa Timur",
    "bengawan solo": "Jawa Timur", "sungai brantas": "Jawa Timur", "brantas": "Jawa Timur",

    # ---------------- KALIMANTAN ----------------
    "kalimantan barat": "Kalimantan Barat", "kalbar": "Kalimantan Barat", "pontianak": "Kalimantan Barat",
    "singkawang": "Kalimantan Barat", "sambas": "Kalimantan Barat", "bengkayang": "Kalimantan Barat",
    "ketapang": "Kalimantan Barat", "sintang": "Kalimantan Barat", "kapuas hulu": "Kalimantan Barat",
    "mempawah": "Kalimantan Barat", "sanggau": "Kalimantan Barat", "sekadau": "Kalimantan Barat", "melawi": "Kalimantan Barat",
    "sungai kapuas": "Kalimantan Barat", "kapuas": "Kalimantan Barat",
    "kubu raya": "Kalimantan Barat", "sungai ambawang": "Kalimantan Barat",

    "kalimantan tengah": "Kalimantan Tengah", "kalteng": "Kalimantan Tengah", "palangkaraya": "Kalimantan Tengah",
    "palangka raya": "Kalimantan Tengah",
    "kotawaringin": "Kalimantan Tengah", "kotawaringin timur": "Kalimantan Tengah", "kotawaringin barat": "Kalimantan Tengah",
    "barito": "Kalimantan Tengah", "katingan": "Kalimantan Tengah", "seruyan": "Kalimantan Tengah", "sampit": "Kalimantan Tengah",
    "murung raya": "Kalimantan Tengah",
    "tanjung puting": "Kalimantan Tengah", "taman nasional tanjung puting": "Kalimantan Tengah", "sungai barito": "Kalimantan Tengah",

    "kalimantan selatan": "Kalimantan Selatan", "kalsel": "Kalimantan Selatan", "banjarmasin": "Kalimantan Selatan",
    "banjarbaru": "Kalimantan Selatan", "martapura": "Kalimantan Selatan", "tabalong": "Kalimantan Selatan",
    "kotabaru": "Kalimantan Selatan", "tanah bumbu": "Kalimantan Selatan", "tanah laut": "Kalimantan Selatan", "tapin": "Kalimantan Selatan",
    "hulu sungai": "Kalimantan Selatan",

    "kalimantan timur": "Kalimantan Timur", "kaltim": "Kalimantan Timur", "samarinda": "Kalimantan Timur",
    "balikpapan": "Kalimantan Timur", "bontang": "Kalimantan Timur", "ikn": "Kalimantan Timur",
    "nusantara": "Kalimantan Timur", "kutai": "Kalimantan Timur", "kutai kartanegara": "Kalimantan Timur",
    "kutai timur": "Kalimantan Timur", "berau": "Kalimantan Timur", "penajam": "Kalimantan Timur", "paser": "Kalimantan Timur",
    "tenggarong": "Kalimantan Timur", "tenggarong seberang": "Kalimantan Timur",
    "sungai mahakam": "Kalimantan Timur", "mahakam": "Kalimantan Timur", "penajam paser utara": "Kalimantan Timur",

    "kalimantan utara": "Kalimantan Utara", "kaltara": "Kalimantan Utara", "tarakan": "Kalimantan Utara",
    "bulungan": "Kalimantan Utara", "nunukan": "Kalimantan Utara", "malinau": "Kalimantan Utara", "tana tidung": "Kalimantan Utara",

    # ---------------- SULAWESI ----------------
    "sulawesi utara": "Sulawesi Utara", "sulut": "Sulawesi Utara", "manado": "Sulawesi Utara",
    "bitung": "Sulawesi Utara", "tomohon": "Sulawesi Utara", "kotamobagu": "Sulawesi Utara",
    "minahasa": "Sulawesi Utara", "sangihe": "Sulawesi Utara", "talaud": "Sulawesi Utara", "bolaang mongondow": "Sulawesi Utara",
    "bunaken": "Sulawesi Utara", "taman nasional bunaken": "Sulawesi Utara",

    "gorontalo": "Gorontalo", "bone bolango": "Gorontalo", "pohuwato": "Gorontalo", "boalemo": "Gorontalo",

    "sulawesi tengah": "Sulawesi Tengah", "sulteng": "Sulawesi Tengah", "palu": "Sulawesi Tengah",
    "donggala": "Sulawesi Tengah", "poso": "Sulawesi Tengah", "tolitoli": "Sulawesi Tengah",
    "luwuk": "Sulawesi Tengah", "banggai": "Sulawesi Tengah", "morowali": "Sulawesi Tengah", "sigi": "Sulawesi Tengah", "parigi moutong": "Sulawesi Tengah",
    "danau poso": "Sulawesi Tengah", "lore lindu": "Sulawesi Tengah",

    "sulawesi barat": "Sulawesi Barat", "sulbar": "Sulawesi Barat", "mamuju": "Sulawesi Barat",
    "majene": "Sulawesi Barat", "polewali mandar": "Sulawesi Barat", "polman": "Sulawesi Barat",

    "sulawesi selatan": "Sulawesi Selatan", "sulsel": "Sulawesi Selatan", "makassar": "Sulawesi Selatan",
    "parepare": "Sulawesi Selatan", "palopo": "Sulawesi Selatan", "gowa": "Sulawesi Selatan",
    "bone": "Sulawesi Selatan", "wajo": "Sulawesi Selatan", "soppeng": "Sulawesi Selatan",
    "pinrang": "Sulawesi Selatan", "enrekang": "Sulawesi Selatan", "toraja": "Sulawesi Selatan",
    "tana toraja": "Sulawesi Selatan", "bulukumba": "Sulawesi Selatan", "bantaeng": "Sulawesi Selatan",
    "jeneponto": "Sulawesi Selatan", "takalar": "Sulawesi Selatan", "maros": "Sulawesi Selatan", "pangkep": "Sulawesi Selatan",
    "toraja utara": "Sulawesi Selatan", "danau matano": "Sulawesi Selatan",

    "sulawesi tenggara": "Sulawesi Tenggara", "sultra": "Sulawesi Tenggara", "kendari": "Sulawesi Tenggara",
    "bau-bau": "Sulawesi Tenggara", "baubau": "Sulawesi Tenggara", "muna": "Sulawesi Tenggara",
    "wakatobi": "Sulawesi Tenggara", "konawe": "Sulawesi Tenggara", "kolaka": "Sulawesi Tenggara", "bombana": "Sulawesi Tenggara",

    # ---------------- BALI & NUSA TENGGARA ----------------
    "bali": "Bali", "denpasar": "Bali", "badung": "Bali", "gianyar": "Bali",
    "tabanan": "Bali", "buleleng": "Bali", "singaraja": "Bali", "karangasem": "Bali",
    "klungkung": "Bali", "bangli": "Bali", "jembrana": "Bali",
    "gunung agung": "Bali", "danau batur": "Bali", "kuta": "Bali", "ubud": "Bali",

    "nusa tenggara barat": "Nusa Tenggara Barat", "ntb": "Nusa Tenggara Barat", "mataram": "Nusa Tenggara Barat",
    "bima": "Nusa Tenggara Barat", "sumbawa": "Nusa Tenggara Barat", "dompu": "Nusa Tenggara Barat",
    "lombok": "Nusa Tenggara Barat", "lombok barat": "Nusa Tenggara Barat", "lombok tengah": "Nusa Tenggara Barat", "lombok timur": "Nusa Tenggara Barat",
    "gunung rinjani": "Nusa Tenggara Barat", "rinjani": "Nusa Tenggara Barat", "gunung tambora": "Nusa Tenggara Barat", "lombok utara": "Nusa Tenggara Barat",

    "nusa tenggara timur": "Nusa Tenggara Timur", "ntt": "Nusa Tenggara Timur", "kupang": "Nusa Tenggara Timur",
    "ende": "Nusa Tenggara Timur", "maumere": "Nusa Tenggara Timur", "sikka": "Nusa Tenggara Timur",
    "manggarai": "Nusa Tenggara Timur", "labuan bajo": "Nusa Tenggara Timur", "rote": "Nusa Tenggara Timur",
    "sumba": "Nusa Tenggara Timur", "sumba timur": "Nusa Tenggara Timur", "alor": "Nusa Tenggara Timur",
    "belu": "Nusa Tenggara Timur", "atambua": "Nusa Tenggara Timur", "timor tengah": "Nusa Tenggara Timur",
    "pulau komodo": "Nusa Tenggara Timur", "taman nasional komodo": "Nusa Tenggara Timur", "flores": "Nusa Tenggara Timur", "manggarai barat": "Nusa Tenggara Timur",

    # ---------------- MALUKU & PAPUA ----------------
    "maluku": "Maluku", "ambon": "Maluku", "tual": "Maluku", "buru": "Maluku",
    "seram": "Maluku", "aru": "Maluku", "kepulauan aru": "Maluku", "maluku tengah": "Maluku", "maluku tenggara": "Maluku",

    "maluku utara": "Maluku Utara", "ternate": "Maluku Utara", "tidore": "Maluku Utara",
    "halmahera": "Maluku Utara", "morotai": "Maluku Utara", "sula": "Maluku Utara",

    "papua": "Papua", "jayapura": "Papua", "biak": "Papua", "biak numfor": "Papua",
    "yapen": "Papua", "keerom": "Papua", "sarmi": "Papua", "mamberamo": "Papua",
    "danau sentani": "Papua", "puncak jaya": "Papua", "cartenz": "Papua",

    "papua barat": "Papua Barat", "manokwari": "Papua Barat", "fakfak": "Papua Barat",
    "kaimana": "Papua Barat", "teluk bintuni": "Papua Barat", "teluk wondama": "Papua Barat", "raja ampat": "Papua Barat",

    "papua selatan": "Papua Selatan", "merauke": "Papua Selatan", "boven digoel": "Papua Selatan",
    "mappi": "Papua Selatan", "asmat": "Papua Selatan", "sungai digul": "Papua Selatan",

    "papua tengah": "Papua Tengah", "nabire": "Papua Tengah", "timika": "Papua Tengah",
    "mimika": "Papua Tengah", "paniai": "Papua Tengah", "dogiyai": "Papua Tengah", "deiyai": "Papua Tengah",

    "papua pegunungan": "Papua Pegunungan", "wamena": "Papua Pegunungan", "jayawijaya": "Papua Pegunungan",
    "lanny jaya": "Papua Pegunungan", "tolikara": "Papua Pegunungan", "yahukimo": "Papua Pegunungan",
    "nduga": "Papua Pegunungan", "mamberamo tengah": "Papua Pegunungan", "yalimo": "Papua Pegunungan",

    "papua barat daya": "Papua Barat Daya", "sorong": "Papua Barat Daya",
    "tambrauw": "Papua Barat Daya", "maybrat": "Papua Barat Daya", "sorong selatan": "Papua Barat Daya",
}

ISLAND_FALLBACK = {
    "kalimantan": "Kalimantan", "borneo": "Kalimantan",
    "sumatera": "Sumatera", "sumatra": "Sumatera",
    "jawa": "Jawa",
    "sulawesi": "Sulawesi", "celebes": "Sulawesi",
    "papua": "Maluku-Papua", "maluku": "Maluku-Papua",
    "bali": "Bali-Nusa Tenggara", "nusa tenggara": "Bali-Nusa Tenggara",
}

# =========================================================
# STAGE 2 DATA: spelling normalisation for already-structured province values
# =========================================================
PROVINCE_FIX = {
    # Singkatan
    'NTT': 'Nusa Tenggara Timur',
    'Ntb': 'Nusa Tenggara Barat',
    'NTB': 'Nusa Tenggara Barat',
    'DKI': 'DKI Jakarta',
    'Jakarta': 'DKI Jakarta',
    'Sumut': 'Sumatera Utara',
    'Sumbar': 'Sumatera Barat',
    'Sumsel': 'Sumatera Selatan',
    'Kaltim': 'Kalimantan Timur',
    'Kalbar': 'Kalimantan Barat',
    'Kalsel': 'Kalimantan Selatan',
    'Kalteng': 'Kalimantan Tengah',
    'Kaltara': 'Kalimantan Utara',
    'Sulsel': 'Sulawesi Selatan',
    'Sultra': 'Sulawesi Tenggara',
    'Sulut': 'Sulawesi Utara',
    'Sulteng': 'Sulawesi Tengah',
    'Sulbar': 'Sulawesi Barat',
    'Babel': 'Kepulauan Bangka Belitung',
    'Kepri': 'Kepulauan Riau',
    'Jabar': 'Jawa Barat',
    'Jateng': 'Jawa Tengah',
    'Jatim': 'Jawa Timur',
    'Malut': 'Maluku Utara',
    'Kaltengah': 'Kalimantan Tengah',

    # Variasi penulisan
    'Sulawesi tengah': 'Sulawesi Tengah',
    'Kepulauan bangka Belitung': 'Kepulauan Bangka Belitung',
    'Kepulauan Bangka belitung': 'Kepulauan Bangka Belitung',
    'Bangka Belitung': 'Kepulauan Bangka Belitung',
    'Kelimantan Selatan': 'Kalimantan Selatan',
    'kalimantan Tengah': 'Kalimantan Tengah',
    'sumatera utara': 'Sumatera Utara',
    'jawa barat': 'Jawa Barat',
    'jawa tengah': 'Jawa Tengah',
    'jawa timur': 'Jawa Timur',
    'Kepulauan Riau ': 'Kepulauan Riau',
    'Jawa Barat ': 'Jawa Barat',

    # Kabupaten/kota yang masuk ke kolom Provinsi
    'Cirebon': 'Jawa Barat',
    'Subang': 'Jawa Barat',
    'Bekasi': 'Jawa Barat',
    'Bogor': 'Jawa Barat',
    'Depok': 'Jawa Barat',
    'Aceh Tengah': 'Aceh',
    'Sumba Timur': 'Nusa Tenggara Timur',
    'Trenggalek': 'Jawa Timur',
    'Malang': 'Jawa Timur',
    'Sidoarjo': 'Jawa Timur',
    'Kubu Raya': 'Kalimantan Barat',
    'Pangkalpinang': 'Kepulauan Bangka Belitung',
    'Bangka Barat': 'Kepulauan Bangka Belitung',

    # Nama terlalu umum / ambiguous
    'Riau, Sumatera Barat': 'Riau',
    'Kepulauan Maluku': 'Maluku',
    'Yogyakarta': 'DI Yogyakarta',
    'DIY': 'DI Yogyakarta',
    'Sulawesi': 'Sulawesi Tengah',
    'Jawa': 'Jawa Tengah',
    'Kalimantan': 'Kalimantan Tengah',
    'Sumatera': 'Sumatera Selatan',

    # Missing-like value
    'nan': np.nan,
    'NaN': np.nan,
    'None': np.nan,
    '': np.nan,
}

# Province -> island grouping (canonical names as produced by PROVINCE_FIX)
PULAU_MAP = {
    # Sumatera
    'Aceh': 'Sumatera',
    'Sumatera Utara': 'Sumatera',
    'Sumatera Barat': 'Sumatera',
    'Riau': 'Sumatera',
    'Kepulauan Riau': 'Sumatera',
    'Jambi': 'Sumatera',
    'Bengkulu': 'Sumatera',
    'Sumatera Selatan': 'Sumatera',
    'Kepulauan Bangka Belitung': 'Sumatera',
    'Lampung': 'Sumatera',

    # Jawa
    'Banten': 'Jawa',
    'DKI Jakarta': 'Jawa',
    'Jawa Barat': 'Jawa',
    'Jawa Tengah': 'Jawa',
    'DI Yogyakarta': 'Jawa',
    'Jawa Timur': 'Jawa',

    # Kalimantan
    'Kalimantan Barat': 'Kalimantan',
    'Kalimantan Tengah': 'Kalimantan',
    'Kalimantan Selatan': 'Kalimantan',
    'Kalimantan Timur': 'Kalimantan',
    'Kalimantan Utara': 'Kalimantan',

    # Sulawesi
    'Sulawesi Utara': 'Sulawesi',
    'Gorontalo': 'Sulawesi',
    'Sulawesi Tengah': 'Sulawesi',
    'Sulawesi Barat': 'Sulawesi',
    'Sulawesi Selatan': 'Sulawesi',
    'Sulawesi Tenggara': 'Sulawesi',

    # Bali & Nusa Tenggara
    'Bali': 'Bali-Nusa Tenggara',
    'Nusa Tenggara Barat': 'Bali-Nusa Tenggara',
    'Nusa Tenggara Timur': 'Bali-Nusa Tenggara',

    # Maluku
    'Maluku': 'Maluku',
    'Maluku Utara': 'Maluku',

    # Papua
    'Papua': 'Papua',
    'Papua Barat': 'Papua',
    'Papua Barat Daya': 'Papua',
    'Papua Tengah': 'Papua',
    'Papua Pegunungan': 'Papua',
    'Papua Selatan': 'Papua',
}

ISLAND_ORDER = [
    'Sumatera',
    'Jawa',
    'Kalimantan',
    'Sulawesi',
    'Bali-Nusa Tenggara',
    'Maluku',
    'Papua',
]

# GeoJSON province-name normalisation (the upstream file spells things differently
# again from both the raw export and PROVINCE_FIX above)
GEO_FIX = {
    'Di. Aceh': 'Aceh',
    'Nanggroe Aceh Darussalam': 'Aceh',
    'Nangroe Aceh Darussalam': 'Aceh',
    'Aceh': 'Aceh',

    'Probanten': 'Banten',
    'Banten': 'Banten',

    'Dki Jakarta': 'DKI Jakarta',
    'Dki Jakarta Raya': 'DKI Jakarta',
    'Daerah Khusus Ibukota Jakarta': 'DKI Jakarta',

    'Daerah Istimewa Yogyakarta': 'DI Yogyakarta',
    'Di Yogyakarta': 'DI Yogyakarta',
    'Yogyakarta': 'DI Yogyakarta',

    'Bangka Belitung': 'Kepulauan Bangka Belitung',
    'Kepulauan Bangka Belitung': 'Kepulauan Bangka Belitung',

    'Nusatenggara Barat': 'Nusa Tenggara Barat',
    'Nusa Tenggara Barat': 'Nusa Tenggara Barat',
    'Nusatenggara Timur': 'Nusa Tenggara Timur',
    'Nusa Tenggara Timur': 'Nusa Tenggara Timur',

    'Irian Jaya Barat': 'Papua Barat',
    'Irian Jaya Tengah': 'Papua Tengah',
    'Irian Jaya Timur': 'Papua',

    'Papua Barat': 'Papua Barat',
    'Papua Tengah': 'Papua Tengah',
    'Papua': 'Papua',

    'Kepulauan Riau': 'Kepulauan Riau',
    'Riau': 'Riau',
    'Sumatera Utara': 'Sumatera Utara',
    'Kalimantan Utara': 'Kalimantan Utara',
    'Sulawesi Barat': 'Sulawesi Barat',
    'Gorontalo': 'Gorontalo',
}

# =========================================================
# NORMALISATION
# =========================================================
# Rank prefixes, and the trailing country/filler suffixes the exports actually contain.
_RANK_PREFIX = re.compile(r'^(?:kab\.?|kabupaten|kota(?:\s+adm\.?)?|prov\.?|provinsi)\s+')
_DROP_SUFFIX = re.compile(r',?\s*(?:indonesia|republik indonesia|id)\s*$')
_PUNCT_EDGES = re.compile(
    r'^[\s\-–—.,;:/\\|()\[\]"\']+|[\s\-–—.,;:/\\|()\[\]"\']+$'
)


def _normalize_simple(value):
    """Casefold and collapse whitespace. The cheap half of normalisation."""
    return ' '.join(str(value).split()).casefold()


def _normalize(value):
    """The lookup key for any location string.

    Handles what real exports contain, which an exact-match lookup did not: mixed case,
    repeated whitespace, the escaped `\\,` separators the monitoring tool emits, rank
    prefixes ("KAB. ACEH SINGKIL"), and trailing ", Indonesia".
    """
    text = str(value).replace('\\,', ',').replace('\\', ' ')
    text = _normalize_simple(text)
    text = _PUNCT_EDGES.sub('', text)
    text = _DROP_SUFFIX.sub('', text)
    text = _RANK_PREFIX.sub('', text)
    return _PUNCT_EDGES.sub('', text)


def _candidates(value):
    """Normalised lookup keys for `value`, most specific first.

    A value like "Kota Bandung\\, Jawa Barat" names a city inside a province; the city is the
    more useful answer, so it is tried first. Splitting also rescues the concatenated values
    the monitoring tool emits, such as "Trenggalek\\, Indonesia".
    """
    raw = str(value).replace('\\,', ',')
    parts = [p for p in re.split(r'[,;/|]', raw) if p.strip()]
    seen, out = set(), []
    for part in parts + [raw]:
        key = _normalize(part)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


# =========================================================
# LOOKUP TABLES
# =========================================================
# Normalised views of the hand-maintained maps. Building these once is what makes matching
# case-insensitive: PROVINCE_FIX grew mixed-case keys over time, so an exact lookup
# recognised 'Sumut' but not 'sumut' or 'SUMUT' -- only 7 of 41 provinces had a lowercase
# entry, purely by accident of who added what.
_PROVINCE_FIX_CI = {}
for _key, _value in PROVINCE_FIX.items():
    if isinstance(_value, str):
        _PROVINCE_FIX_CI[_normalize_simple(_key)] = _value

# Canonical province name keyed by its own normalised form, so 'aceh' and 'ACEH' both reach
# 'Aceh' even though PROVINCE_FIX has no entry for either.
_CANONICAL_BY_KEY = {_normalize_simple(_p): _p for _p in PULAU_MAP}

# Official region data, generated from the BPS code list by `tools/build_regions.py`. It
# supplies the authoritative kabupaten/kota -> province parentage that used to be maintained
# by hand. The gazetteer above still matters: it carries ~213 entries the official list has no
# concept of -- landmarks ("gunung leuser", "krakatau", "danau toba"), abbreviations
# ("sumut", "kepri", "oki") and spelling variants -- which for environmental monitoring are
# often the only location a mention names. So the two are merged, not swapped.
from ._regions import PROVINCES as _OFFICIAL_PROVINCES  # noqa: E402
from ._regions import REGION_TO_PROVINCE as _OFFICIAL_REGIONS  # noqa: E402

_GAZETTEER = {_normalize_simple(_k): _v for _k, _v in LOCATION_TO_PROVINCE.items()}
# Official parentage wins where the two disagree: the gazetteer predates the 2022 Papua split
# ("puncak jaya" -> Papua Tengah, "raja ampat" -> Papua Barat Daya) and misfiled Kab. Kapuas.
# Gazetteer-only keys survive untouched.
_GAZETTEER.update(_OFFICIAL_REGIONS)

# Province names are searchable too, so "Aceh" in free text resolves directly.
for _name in _OFFICIAL_PROVINCES.values():
    _GAZETTEER.setdefault(_normalize_simple(_name), _name)

# Kabupaten that were wrongly listed as provinces in PULAU_MAP belong here instead.
_GAZETTEER.setdefault('maluku tengah', 'Maluku')
_GAZETTEER.setdefault('maluku selatan', 'Maluku')

# Region names that are also ordinary Indonesian words, so matching them bare produces
# confident nonsense. They stay reachable through their qualified forms ("kab. puncak"),
# which the generated data already carries.
#
# `puncak` means "peak" -- "puncak el nino", "puncak musim kemarau" -- and also names the
# Bogor highland everyone knows, on top of Kab. Puncak in Papua Tengah. Measured on 8,000
# documents it matched 195 of them (2.4%), seven times the next new single-word key, and
# mislocated Jakarta articles about the El Nino peak to Papua Tengah. Every other name the
# official list adds is a genuine place at low frequency, so this set has one member.
COMMON_WORD_REGIONS = frozenset({'puncak'})

for _word in COMMON_WORD_REGIONS:
    _GAZETTEER.pop(_word, None)

KNOWN_PROVINCES = frozenset(PULAU_MAP)


# =========================================================
# AMBIGUOUS NAMES
# =========================================================
# Names that mean different places depending on the words around them. A table, so a future
# case is one line rather than a code change.
#
# Every other landmark in the gazetteer whose bare name is also a kabupaten -- "danau toba",
# "sungai siak", "gunung kerinci", "danau kerinci", "danau poso" -- agrees with the official
# list, so these two are genuinely the only ones today.
AMBIGUOUS_REGIONS = {
    # Sungai Kapuas is West Kalimantan's river; Kab. Kapuas (62.03) is in Central Kalimantan.
    'kapuas': ([('sungai', 'Kalimantan Barat')], 'Kalimantan Tengah'),
    # Kota Banjar (32.79) is in West Java; the larger Kab. Banjar (63.03) is in South
    # Kalimantan and is the likelier referent when nothing qualifies it.
    'banjar': ([('kota', 'Jawa Barat')], 'Kalimantan Selatan'),
}


def _disambiguate(name, province, context):
    """Apply `AMBIGUOUS_REGIONS` to a matched name, given the text it was found in."""
    rule = AMBIGUOUS_REGIONS.get(name)
    if rule is None:
        return province
    triggers, default = rule
    haystack = (context or '').casefold()
    for trigger, answer in triggers:
        if trigger in haystack:
            return answer
    return default


# =========================================================
# BUILT ONCE, ON FIRST USE
# =========================================================
# 11 stdlib patterns, so these are cheap enough to build eagerly.
_ISLAND_PATTERNS = {k: re.compile(rf'\b{re.escape(k)}\b') for k in ISLAND_FALLBACK}

_location_kp_cache = None  # lazily built, cached


def _get_location_kp():
    """The gazetteer keyword scanner, built once on first use.

    Lazy for two reasons: it keeps the `flashtext` import off the `import great` path
    (see the note at the top of this module), and it avoids loading ~1,500 keywords into a
    trie for anyone who never resolves a location.

    Raises ImportError with an actionable message if flashtext is missing.
    """
    global _location_kp_cache
    if _location_kp_cache is None:
        try:
            from flashtext import KeywordProcessor
        except ImportError as exc:
            raise ImportError(
                'resolving locations from free text needs flashtext. '
                'Install it with: pip install flashtext'
            ) from exc
        kp = KeywordProcessor(case_sensitive=False)
        for loc in _GAZETTEER:
            kp.add_keyword(loc)
        _location_kp_cache = kp
    return _location_kp_cache


# =========================================================
# RESOLVERS
# =========================================================
UNDETECTED = 'Tidak Terdeteksi'
ISLAND_ONLY = 'Provinsi Tidak Spesifik'


def _canonicalize(province):
    """Normalise a province name to its canonical spelling, case-insensitively.

    Returns the input unchanged when it is not a province name at all, which is what the
    gazetteer path relies on.
    """
    if province is None:
        return province
    key = _normalize_simple(province)
    fixed = _PROVINCE_FIX_CI.get(key)
    if fixed is not None:
        return fixed
    return _CANONICAL_BY_KEY.get(key, province)


def is_known_province(value) -> bool:
    """True if `value` names a real province, after normalisation.

    Works for every spelling the library accepts -- canonical, abbreviation, any case, and
    with or without a rank prefix.
    """
    if value is None:
        return False
    return any(_canonicalize(key) in KNOWN_PROVINCES for key in _candidates(value) if key)


def _lookup(value):
    """(provinsi, pulau) for a structured location string, or None if unrecognised."""
    for key in _candidates(value):
        if not key:
            continue
        province = _PROVINCE_FIX_CI.get(key) or _CANONICAL_BY_KEY.get(key)
        if province is None:
            province = _GAZETTEER.get(key)
            if province is not None:
                province = _disambiguate(key, province, value)
        if province is not None:
            province = _canonicalize(province)
            if province in KNOWN_PROVINCES:
                return province, PULAU_MAP.get(province, UNDETECTED)
    return None


def _scan(text):
    """(provinsi, pulau) from free text, using the gazetteer scan."""
    lowered = str(text).casefold()
    found = _get_location_kp().extract_keywords(lowered)

    if found:
        counts = {}
        for name in found:
            counts[name] = counts.get(name, 0) + 1
        # most mentions wins; ties go to the longer, more specific name
        best, _ = max(counts.items(), key=lambda kv: (kv[1], len(kv[0])))
        province = _canonicalize(_disambiguate(best, _GAZETTEER[best], lowered))
        if province in KNOWN_PROVINCES:
            return province, PULAU_MAP.get(province, UNDETECTED)

    for name, island in ISLAND_FALLBACK.items():
        if _ISLAND_PATTERNS[name].search(lowered):
            return ISLAND_ONLY, island

    return UNDETECTED, UNDETECTED


def resolve(location=None, text=None) -> tuple:
    """Resolve a location to `(provinsi, pulau)`.

    Scans `text` first and falls back to the structured `location` only when the text names
    no place. Either argument may be omitted.

        resolve(None, 'banjir melanda kota medan')  -> ('Sumatera Utara', 'Sumatera')
        resolve('Kota Bandung\\, Jawa Barat')        -> ('Jawa Barat', 'Jawa')

    **Why text wins.** In media-monitoring exports `Location` is the author's or outlet's
    location, not the event's. Measured on 25k rows of the environment data, the two
    disagree 74% of the time, and the disagreements look like `Location='Jakarta'` on an
    article about fires in Kalimantan. For a map of where issues are *happening*, the article
    text is the right signal; `Location` is a fallback for rows whose text names nowhere.

    Returns `('Tidak Terdeteksi', 'Tidak Terdeteksi')` when nothing resolves, or
    `('Provinsi Tidak Spesifik', <pulau>)` when only an island is named.
    """
    if text is not None and str(text).strip():
        hit = _scan(text)
        if hit[0] not in (UNDETECTED, ISLAND_ONLY):
            return hit
    else:
        hit = None

    if location is not None and str(location).strip():
        structured = _lookup(location)
        if structured is not None:
            return structured

    return hit if hit is not None else (UNDETECTED, UNDETECTED)


def resolve_frame(data, location_col='Location', text_cols=('Headline', 'Mentions')):
    """Run `resolve()` across a DataFrame; returns a frame of `[Provinsi, Pulau]`.

        df[['Provinsi', 'Pulau']] = resolve_frame(df)

    `text_cols` are joined before scanning, so a place named in the headline still counts when
    the body does not repeat it. Missing columns are skipped rather than raising, since exports
    vary in which ones they carry.

    Follows `resolve()`'s precedence: the text scan runs first and `location_col` is consulted
    only for rows the text could not place. See `resolve()` for why.

    The structured fallback resolves each distinct value once rather than once per row -- a
    25k-row export typically holds only a few hundred distinct locations.
    """
    import pandas as pd  # core dependency; imported here to keep this module's top light

    index = data.index
    present = [c for c in text_cols if c in data.columns]

    provinces = pd.Series([None] * len(data), index=index, dtype=object)
    islands = pd.Series([None] * len(data), index=index, dtype=object)

    # --- free-text pass -----------------------------------------------------
    if present:
        # fillna before concatenating: on pandas 3 a NA in any column propagates through the
        # whole expression, so one missing Headline would silently wipe out the Mentions text
        # that actually carries the location.
        blob = data[present[0]].fillna('').astype(str)
        for col in present[1:]:
            blob = blob + ' ' + data[col].fillna('').astype(str)
        # Scan each distinct text once. Retweets and syndicated copy mean roughly half the
        # rows in a real export repeat text verbatim, so this is close to a 2x saving and
        # costs nothing when they happen to be unique.
        seen = {text: _scan(text) for text in blob.unique()}
        scanned = [seen[text] for text in blob]
        found = pd.Series([t[0] not in (UNDETECTED, ISLAND_ONLY) for t in scanned], index=index)
        provinces[found] = [t[0] for t, ok in zip(scanned, found) if ok]
        islands[found] = [t[1] for t, ok in zip(scanned, found) if ok]
    else:
        scanned = None

    # --- structured fallback for rows the text could not place, deduplicated
    todo = provinces.isna()
    if todo.any() and location_col in data.columns:
        # fillna before astype: on pandas 3 the string accessor propagates NA rather than
        # producing the literal 'nan', so unique() would otherwise hand back floats.
        keys = data.loc[todo, location_col].fillna('').astype(str).str.strip()
        table = {}
        for value in keys.unique():
            if not value or value.lower() == 'nan':
                continue
            hit = _lookup(value)
            if hit is not None:
                table[value] = hit
        if table:
            mapped = keys.map(table)
            hit = mapped.notna()
            idx = mapped.index[hit]
            provinces[idx] = [t[0] for t in mapped[hit]]
            islands[idx] = [t[1] for t in mapped[hit]]

    # --- island-only results from the scan, for rows still unplaced ---------
    if scanned is not None:
        still = provinces.isna()
        if still.any():
            provinces[still] = [t[0] for t, ok in zip(scanned, still) if ok]
            islands[still] = [t[1] for t, ok in zip(scanned, still) if ok]

    return pd.DataFrame({'Provinsi': provinces.fillna(UNDETECTED),
                         'Pulau': islands.fillna(UNDETECTED)}, index=index)
