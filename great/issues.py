"""Environmental issue keyword rules and classifier.

`ISSUE_RULES` is moved from `Weekly Monthly Visualization Program/app/config.py`.
`classify_issue()` replaces the first-match-wins substring scan that used to live
inline in `reports.py` — that version misclassified text like "kebakaran lahan" as
"Konflik agraria" because `lahan` also appears in the agraria rule and rules were
tested in list order with no word boundaries (see EVALUATION.md, defect P0-4).

This version anchors every keyword to a word boundary and picks the rule with the
most matches instead of the first rule that matches at all.

Keywords for the existing categories were expanded, and new categories
('Bencana vulkanik', 'Perubahan iklim/emisi', 'Konservasi/reboisasi',
'Angin puting beliung', 'Gempa bumi') were added after a manual review of
documents that fell through to `_OTHER` (see EVALUATION.md).

`NOISE_RULES` / `is_noise()` catch documents that matched environmental
keywords loosely (or not at all) but are actually unrelated content — personal
health complaints, spam/klik-bait ("pajak murah"), dsb — scraped in by generic
keyword overlap. These are flagged separately instead of being counted as
`_OTHER` ("Isu lingkungan lain"), since they're not an environmental issue at
all, just noise in the corpus.
"""
import re

ISSUE_RULES = [
    {
        'category': 'Tambang ilegal/ekstraktif',
        'keywords': [
            'tambang', 'pertambangan', 'peti', 'tambang emas',
            'batubara', 'batu bara', 'nikel', 'mining',
            'galian', 'tambang ilegal', 'penambangan liar',
            'izin usaha pertambangan', 'iup', 'reklamasi tambang',
            'tambang pasir', 'penambangan pasir ilegal', 'tambang timah',
            'lubang tambang', 'bekas tambang', 'galian c',
        ],
    },
    {
        'category': 'Konflik agraria',
        'keywords': [
            'agraria', 'konflik lahan', 'sengketa tanah',
            'konflik', 'sengketa', 'gusur', 'penggusuran',
            'konflik agraria', 'perebutan lahan', 'sengketa tanah adat',
            'penggusuran lahan warga', 'perampasan lahan', 'mafia tanah',
            'sengketa lahan', 'konflik tenurial', 'hak ulayat',
        ],
    },
    {
        'category': 'Deforestasi',
        'keywords': [
            'hutan', 'deforestasi', 'pembabatan',
            'penggundulan', 'pembalakan', 'illegal logging',
            'penebangan liar', 'alih fungsi hutan', 'bekas tebangan',
            'pembukaan lahan hutan', 'ditanami sawit', 'lahan sawit',
            'alih fungsi jadi sawit', 'perambahan hutan', 'hutan gundul',
            'konversi hutan', 'tutupan hutan hilang', 'kawasan hutan lindung rusak',
        ],
    },
    {
        'category': 'Banjir/longsor',
        'keywords': [
            'banjir', 'longsor', 'banjir bandang',
            'tanah longsor', 'banjir rob', 'banjir merendam',
            'banjir lahar', 'genangan', 'banjir luapan sungai',
            'debit air sungai meningkat', 'tanggul jebol',
        ],
    },
    {
        'category': 'Angin puting beliung',
        'keywords': [
            'puting beliung', 'angin puting beliung', 'angin kencang',
            'angin kencang merusak', 'angin ribut', 'angin topan',
            'atap rumah beterbangan', 'pohon tumbang angin',
            'angin puting beliung terjang', 'bmkg peringatan angin',
        ],
    },
    {
        'category': 'Gempa bumi',
        'keywords': [
            'gempa', 'gempa bumi', 'guncangan gempa', 'gempa susulan',
            'magnitudo', 'skala richter', 'sr', 'episentrum', 'pusat gempa',
            'gempa dangkal', 'gempa tektonik', 'korban gempa',
            'rumah roboh gempa', 'gempa merusak', 'zona megathrust', 'megathrust',
        ],
    },
    {
        'category': 'Pencemaran air/limbah',
        'keywords': [
            'sungai', 'pencemaran air', 'sumur', 'limbah',
            'tercemar', 'pencemaran', 'tumpahan minyak',
            'tumpahan solar', 'tumpahan', 'polusi air',
            'limbah pabrik', 'pencemaran sungai', 'air tercemar', 'limbah b3',
            'air menghitam', 'sungai menghitam', 'ipal', 'limbah elektronik',
            'e-waste', 'limbah pabrik sawit', 'pencemaran kali', 'kali tercemar',
            'sumber limbah', 'limbah cair', 'limbah medis', 'air baku tercemar',
            'pencemaran lingkungan',
        ],
    },
    {
        'category': 'Sampah',
        'keywords': [
            'sampah', 'plastik', 'tpa', 'limbah plastik',
            'sampah plastik', 'tpa penuh', 'darurat sampah', 'sampah menumpuk',
            'pengelolaan sampah', 'pengolahan sampah', 'bank sampah',
            'sampah organik', 'pemilahan sampah', 'sampah rumah tangga',
            'tempat pemrosesan akhir', 'tempat pengolahan sampah',
            'tempat pembuangan akhir', 'tpst', 'psel',
            'sampah menjadi energi', 'reduce reuse recycle',
            'pengelolaan limbah', 'fasilitas pengolahan sampah',
            'sekam padi', 'tpa galuga', 'tpa karang',
            'daur ulang', 'sampah laut', 'microplastic', 'mikroplastik',
            'sampah anorganik', 'pungut sampah',
        ],
    },
    {
        'category': 'Kekeringan/Krisis Air',
        'keywords': [
            'kemarau panjang', 'krisis air', 'kekeringan',
            'krisis air bersih', 'el nino', 'musim kemarau panjang',
            'sumber air mengering', 'sumur kering', 'debit air menurun',
            'kekurangan air bersih', 'krisis air baku',
        ],
    },
    {
        'category': 'Kebakaran lingkungan',
        'keywords': [
            'kebakaran', 'karhutla', 'lahan terbakar', 'kebakaran hutan',
            'kebakaran lahan', 'titik api', 'hotspot', 'kabut asap',
            'water bombing', 'lahan gambut terbakar', 'asap karhutla',
            'titik panas', 'kebakaran tpa', 'tpa terbakar',
            'pembakaran hutan', 'pembakaran lahan',
            'kebakaran lapak', 'lapak limbah', 'lokasi kebakaran',
            'hektare lahan terdampak', 'lahan terdampak kebakaran',
            'api berkobar', 'gambut terbakar', 'kebakaran gambut',
            'satgas karhutla', 'modifikasi cuaca',
        ],
    },
    {
        'category': 'Abrasi/erosi',
        'keywords': [
            'abrasi', 'abrasi pantai', 'erosi', 'pesisir',
            'terumbu karang', 'pencemaran laut', 'reklamasi pantai',
            'garis pantai mundur', 'erosi pantai', 'rob pesisir',
            'kerusakan pesisir',
        ],
    },
    {
        'category': 'Satwa/ekosistem',
        'keywords': [
            'satwa', 'habitat', 'ekosistem', 'mangrove',
            'terumbu', 'biodiversitas', 'konservasi',
            'satwa dilindungi', 'orang utan', 'habitat satwa', 'populasi satwa',
            'perburuan liar', 'perdagangan satwa liar', 'spesies langka',
            'satwa langka', 'hutan mangrove', 'kawasan konservasi',
        ],
    },
    {
        'category': 'Polusi udara',
        'keywords': [
            'udara', 'asap', 'emisi', 'polusi udara',
            'pencemaran udara', 'ispu', 'pm2,5', 'pm2.5', 'kualitas udara buruk',
            'kabut polusi', 'udara tidak sehat', 'indeks kualitas udara',
            'polusi kendaraan', 'emisi kendaraan', 'uji emisi',
        ],
    },
    {
        'category': 'Bencana vulkanik',
        'keywords': [
            'abu vulkanik', 'debu vulkanik', 'erupsi', 'gunung anak krakatau',
            'aktivitas vulkanik', 'letusan gunung', 'awan panas', 'status siaga gunung',
            'guguran lava', 'sinabung erupsi', 'merapi erupsi',
            'lewotobi', 'gunung lewotobi', 'ile lewotobi', 'gunung ibu', 'gunung ruang',
            'gunung marapi', 'gunung semeru', 'gunung kerinci', 'gunung dukono',
            'status awas gunung', 'level awas', 'radius bahaya', 'zona bahaya vulkanik',
            'muntahan lava', 'lontaran batu pijar', 'gempa vulkanik', 'tremor vulkanik',
            'material vulkanik', 'evakuasi warga gunung', 'ppgba', 'pvmbg',
            'kolom abu', 'semburan abu',
        ],
    },
    {
        'category': 'Perubahan iklim/emisi',
        'keywords': [
            'perubahan iklim', 'emisi karbon', 'gas rumah kaca', 'pemanasan global',
            'krisis iklim', 'cuaca ekstrem', 'anomali cuaca', 'gelombang panas',
            'kenaikan permukaan laut', 'jejak karbon', 'karbon dioksida',
        ],
    },
    {
        'category': 'Konservasi/reboisasi',
        'keywords': [
            'penanaman pohon', 'wakaf hijau', 'menjaga lingkungan',
            'kelestarian lingkungan', 'pelestarian lingkungan',
            'gerakan tanam pohon', 'reboisasi', 'penghijauan',
            'restorasi lahan', 'restorasi hutan', 'rehabilitasi lahan',
            'hutan wakaf', 'taman kota hijau',
        ],
    },
    {
        'category': 'Energi terbarukan (EBT)',
        'keywords': [
            'energi terbarukan', 'energi baru terbarukan', 'ebt',
            'panel surya', 'energi surya', 'pembangkit listrik tenaga surya', 'plts',
            'energi angin', 'pembangkit listrik tenaga bayu', 'pltb',
            'pembangkit listrik tenaga air', 'plta', 'mikrohidro',
            'panas bumi', 'geothermal', 'pembangkit listrik tenaga panas bumi', 'pltp',
            'biomassa', 'biofuel', 'biodiesel', 'bioenergi', 'bahan bakar nabati',
            'energi bersih', 'energi hijau', 'transisi energi',
            'net zero emission', 'dekarbonisasi', 'kendaraan listrik',
            'baterai listrik', 'hidrogen hijau',
        ],
    },
    {
        'category': 'Krisis Energi Nasional',
        'keywords': [
            'krisis energi', 'harga bbm', 'kenaikan harga bbm', 'bbm subsidi',
            'subsidi bbm', 'harga minyak', 'harga gas', 'kelangkaan bbm',
            'ketahanan energi', 'energi nasional', 'energi fosil',
            'bahan bakar fosil', 'krisis listrik', 'pemadaman listrik',
            'tarif listrik', 'kelangkaan energi', 'pasokan energi',
            'impor bbm', 'impor minyak', 'harga energi', 'kebijakan energi',
            'pertamina', 'elpiji', 'gas lpg', 'kelangkaan gas',
            'pertalite', 'pertamax', 'solar subsidi', 'antrean bbm',
            'opec', 'harga gas dunia', 'blackout',
            # efisiensi / hemat energi (respons kebijakan ke krisis energi)
            'hemat energi', 'penghematan energi', 'efisiensi energi',
            'gerakan hemat energi', 'hemat listrik', 'kebijakan hemat energi',
            'imbauan hemat energi', 'work from home', 'wfh',
            'pembatasan jam operasional', 'penghematan bbm',
        ],
    },
]

_OTHER = 'Isu lingkungan lain'
_NOISE = 'Noise/Tidak Relevan'

# Konten yang lolos keyword scraping tapi bukan isu lingkungan sama sekali —
# klik-bait kesehatan pribadi, spam, obrolan personal yang kebetulan
# nyenggol kata umum ("krisis", "energi" dipakai metaforis, dst).
# Daftar ini masih awal, tambahin terus tiap ketemu contoh baru.
NOISE_RULES = [
    {
        'category': 'Kesehatan pribadi',
        'keywords': [
            'diabetes', 'gejala', 'gula darah', 'kolesterol', 'obat herbal',
            'penyakit dalam', 'keluhan kesehatan', 'cara mengobati',
        ],
    },
    {
        'category': 'Spam/klik-bait',
        'keywords': [
            'sangat murah', 'klik disini', 'daftar sekarang', 'promo terbatas',
            'buruan daftar', 'gratis ongkir', 'cuan',
        ],
    },
    {
        'category': 'Obrolan personal/relationship',
        'keywords': [
            'patriarki', 'laki ga', 'suami', 'pacar', 'mantan',
        ],
    },
]

_RULE_PATTERNS = [
    (rule['category'], re.compile(
        r'\b(?:' + '|'.join(re.escape(k) for k in rule['keywords']) + r')\b'
    ))
    for rule in ISSUE_RULES
]

_NOISE_PATTERNS = [
    (rule['category'], re.compile(
        r'\b(?:' + '|'.join(re.escape(k) for k in rule['keywords']) + r')\b'
    ))
    for rule in NOISE_RULES
]


def is_noise(text) -> bool:
    """True kalau teks lebih cocok sebagai noise (bukan isu lingkungan)
    daripada sebagai isu lingkungan apapun. Dipanggil sebelum classify_issue()
    dianggap final — dok noise dikeluarkan dari `_OTHER` supaya ga nge-drag
    angka 'Isu lingkungan lain'."""
    text = str(text).lower()
    issue_score = max((len(rx.findall(text)) for _, rx in _RULE_PATTERNS), default=0)
    noise_score = sum(len(rx.findall(text)) for _, rx in _NOISE_PATTERNS)
    return noise_score > 0 and noise_score >= issue_score


def classify_issue(text) -> str:
    """Classify one piece of text into an environmental issue category.

    Scores every rule by how many of its keywords appear (word-boundary matched,
    not a bare substring test) and returns the category with the most hits, so a
    generic word belonging to a lower-priority rule can't shadow a more specific
    match. Returns `_NOISE` when the text looks like non-environmental noise
    (diabetes/spam/personal chat that scraped in by keyword overlap), otherwise
    returns `_OTHER` when no environmental rule matches at all.
    """
    if is_noise(text):
        return _NOISE

    text = str(text).lower()
    scored = [(len(rx.findall(text)), category) for category, rx in _RULE_PATTERNS]
    n, category = max(scored)
    return category if n else _OTHER
