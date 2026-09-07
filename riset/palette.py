"""Shared color palette and plot-size constants.

Moved from `Weekly Monthly Visualization Program/app/config.py` — that content was
already correct, it was just trapped in one project.

`plat_colors` keys are kept in sync with the canonical spelling in
`riset.labels.plat_class` (`'News'`, `'Threads'`, not the original `'Media
Mainstream'` / `'Thread'`) — see EVALUATION.md section 5.2.
"""

sent_colors = {
    'positive': '#7AD1FF',   # bright blue
    'negative': '#EE4B2B',   # bright red
    'neutral':  '#818589',   # light gray
}

plat_colors = {
    'News':      '#2ecc71',
    'Facebook':  '#2980b9',
    'Twitter':   '#5b9bd5',
    'Youtube':   '#e74c3c',
    'Instagram': '#9b59b6',
    'Tiktok':    '#1abc9c',
    'Threads':   '#818589',
}

emo_colors = {
    'joy':          '#f4d03f',
    'trust':        '#82e0aa',
    'fear':         '#5d6d7e',
    'surprise':     '#00FF40',
    'sadness':      '#85c1e9',
    'disgust':      '#8e44ad',
    'anger':        '#e74c3c',
    'anticipation': '#a04000',
}

# ---------------- environmental issue report config ----------------

CMAP_NAME = "YlOrRd"
BASE_MAP_COLOR = "#eeeeee"
EDGE_COLOR = "#444444"
ACTIVE_EDGE_COLOR = "#333333"

TITLE_SIZE = 18
SUBTITLE_SIZE = 15
LABEL_SIZE = 13
TICK_SIZE = 12
ANNOT_SIZE = 12
MAP_NUMBER_SIZE = 13
