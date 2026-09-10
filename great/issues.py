"""Environmental issue keyword rules and classifier.

`ISSUE_RULES` is moved from `Weekly Monthly Visualization Program/app/config.py`.
`classify_issue()` replaces the first-match-wins substring scan that used to live
inline in `reports.py` — that version misclassified text like "kebakaran lahan" as
"Konflik agraria" because `lahan` also appears in the agraria rule and rules were
tested in list order with no word boundaries (see EVALUATION.md, defect P0-4).

This version anchors every keyword to a word boundary and picks the rule with the
most matches instead of the first rule that matches at all.
"""
import re

ISSUE_RULES = [
    {
        'category': 'Tambang ilegal/ekstraktif',
        'keywords': [
            'tambang', 'pertambangan', 'peti', 'tambang emas',
            'batubara', 'batu bara', 'nikel', 'mining',
            'galian', 'tambang ilegal',
        ],
    },
    {
        'category': 'Konflik agraria',
        'keywords': [
            'agraria', 'konflik lahan', 'sengketa tanah',
            'konflik', 'sengketa', 'gusur', 'penggusuran',
        ],
    },
    {
        'category': 'Deforestasi',
        'keywords': [
            'hutan', 'deforestasi', 'pembabatan',
            'penggundulan', 'pembalakan', 'illegal logging',
        ],
    },
    {
        'category': 'Banjir/longsor',
        'keywords': [
            'banjir', 'longsor', 'banjir bandang',
        ],
    },
    {
        'category': 'Pencemaran air/limbah',
        'keywords': [
            'sungai', 'pencemaran air', 'sumur', 'limbah',
            'tercemar', 'pencemaran', 'tumpahan minyak',
            'tumpahan solar', 'tumpahan', 'polusi air',
        ],
    },
    {
        'category': 'Sampah',
        'keywords': [
            'sampah', 'plastik', 'tpa', 'limbah plastik',
        ],
    },
    {
        'category': 'Kekeringan/Krisis Air',
        'keywords': [
            'kemarau panjang', 'krisis air', 'kekeringan',
        ],
    },
    {
        'category': 'Kebakaran lingkungan',
        'keywords': [
            'kebakaran', 'karhutla', 'lahan terbakar', 'kebakaran hutan',
        ],
    },
    {
        'category': 'Abrasi/erosi',
        'keywords': [
            'abrasi', 'abrasi pantai', 'erosi', 'pesisir',
        ],
    },
    {
        'category': 'Satwa/ekosistem',
        'keywords': [
            'satwa', 'habitat', 'ekosistem', 'mangrove',
            'terumbu', 'biodiversitas', 'konservasi',
        ],
    },
    {
        'category': 'Polusi udara',
        'keywords': [
            'udara', 'asap', 'emisi', 'polusi udara',
            'pencemaran udara',
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
