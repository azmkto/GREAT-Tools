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
    'Daerah Istimewa Yogyakarta': 'Jawa',
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
    'Maluku Selatan': 'Maluku',
    'Maluku Tengah': 'Maluku',

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
# BUILT ONCE, ON FIRST USE
# =========================================================
# 11 stdlib patterns, so these are cheap enough to build eagerly.
_ISLAND_PATTERNS = {k: re.compile(rf'\b{re.escape(k)}\b') for k in ISLAND_FALLBACK}

_location_kp_cache = None  # lazily built, cached


def _get_location_kp():
    """The gazetteer keyword scanner, built once on first use.

    Lazy for two reasons: it keeps the `flashtext` import off the `import great` path
    (see the note at the top of this module), and it avoids loading ~570 keywords into a
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
        for loc in LOCATION_TO_PROVINCE:
            kp.add_keyword(loc)
        _location_kp_cache = kp
    return _location_kp_cache


# =========================================================
# RESOLVER FUNCTIONS
# =========================================================
def _canonicalize(province: str) -> str:
    """Final normalisation pass — run on EVERY province value, no matter
    which stage produced it, so ejaan/singkatan yang lolos tetap diseragamkan."""
    return PROVINCE_FIX.get(province, province)


def resolve_from_structured_column(raw_value: str) -> str:
    """Stage: kolom Provinsi yang sudah ada (data survei/export rapi).
    Lookup langsung, bukan scan — inputnya sudah berupa satu nama provinsi
    (walau ejaan/singkatannya mungkin salah)."""
    return _canonicalize(str(raw_value).strip())


def resolve_from_free_text(text: str) -> tuple:
    """Stage: teks bebas (headline/mentions). Scan dulu pakai gazetteer untuk
    menemukan kandidat lokasi paling spesifik, baru hasilnya dilewatkan
    `_canonicalize` sebagai jaring pengaman terakhir.

    Ties dipecahkan lewat panjang keyword (kandidat lebih panjang/spesifik
    menang atas kandidat pendek yang juga match). Kalau tidak ada lokasi
    spesifik ketemu, coba fallback nama pulau saja lewat `ISLAND_FALLBACK`.
    Return: (provinsi, pulau) — keduanya "Tidak Terdeteksi" kalau nihil,
    atau ("Provinsi Tidak Spesifik", <pulau>) kalau cuma pulau yang disebut.
    """
    text_lower = str(text).lower()
    found = _get_location_kp().extract_keywords(text_lower)

    if found:
        counts = {}
        for loc in found:
            counts[loc] = counts.get(loc, 0) + 1
        best_loc, _ = max(counts.items(), key=lambda c: (c[1], len(c[0])))
        prov = _canonicalize(LOCATION_TO_PROVINCE[best_loc])
        return prov, PULAU_MAP.get(prov, "Tidak Terdeteksi")

    for name, pulau_name in ISLAND_FALLBACK.items():
        if _ISLAND_PATTERNS[name].search(text_lower):
            return "Provinsi Tidak Spesifik", pulau_name

    return "Tidak Terdeteksi", "Tidak Terdeteksi"
