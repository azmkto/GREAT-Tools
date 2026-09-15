"""Environmental issue keyword rules and classifier.

`ISSUE_RULES` is moved from `Weekly Monthly Visualization Program/app/config.py`.
`classify_issue()` replaces the first-match-wins substring scan that used to live
inline in `reports.py` — that version misclassified text like "kebakaran lahan" as
"Konflik agraria" because `lahan` also appears in the agraria rule and rules were
tested in list order with no word boundaries (see EVALUATION.md, defect P0-4).

This version anchors every keyword to a word boundary and picks the rule with the
most matches instead of the first rule that matches at all.

Keywords for the existing categories were expanded, and three new categories
('Bencana vulkanik', 'Perubahan iklim/emisi', 'Konservasi/reboisasi') were added
after a manual review of documents that fell through to `_OTHER` (see
EVALUATION.md).
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
            'abu vulkanik', 'erupsi', 'gunung anak krakatau', 'aktivitas vulkanik',
            'letusan gunung', 'awan panas', 'status siaga gunung', 'guguran lava',
            'sinabung erupsi', 'merapi erupsi',
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
        'category': 'Krisis energi/BBM konvensional',
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
        ],
    },
]

_OTHER = 'Isu lingkungan lain'

_RULE_PATTERNS = [
    (rule['category'], re.compile(
        r'\b(?:' + '|'.join(re.escape(k) for k in rule['keywords']) + r')\b'
    ))
    for rule in ISSUE_RULES
]


def classify_issue(text) -> str:
    """Classify one piece of text into an environmental issue category.

    Scores every rule by how many of its keywords appear (word-boundary matched,
    not a bare substring test) and returns the category with the most hits, so a
    generic word belonging to a lower-priority rule can't shadow a more specific
    match. Returns `_OTHER` when no rule matches at all.
    """
    text = str(text).lower()
    scored = [(len(rx.findall(text)), category) for category, rx in _RULE_PATTERNS]
    n, category = max(scored)
    return category if n else _OTHER
