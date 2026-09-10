"""Indonesian province name normalisation and province -> island mapping.

Moved from `Weekly Monthly Visualization Program/app/config.py`.
"""
import numpy as np

# Province name cleaning: raw survey/export spelling -> canonical spelling
PROVINCE_FIX = {
    # Singkatan
    'NTT': 'Nusa Tenggara Timur',
    'Ntb': 'Nusa Tenggara Barat',
    'NTB': 'Nusa Tenggara Barat',
    'DKI': 'DKI Jakarta',
    'Jakarta': 'DKI Jakarta',
    'Sumut': 'Sumatera Utara',
    'Sumbar': 'Sumatera Barat',
    'Kaltim': 'Kalimantan Timur',
    'Kalbar': 'Kalimantan Barat',
    'Kalsel': 'Kalimantan Selatan',
    'Kalteng': 'Kalimantan Tengah',
    'Sulsel': 'Sulawesi Selatan',
    'Sultra': 'Sulawesi Tenggara',
    'Sulut': 'Sulawesi Utara',
    'Sulteng': 'Sulawesi Tengah',

    # Variasi penulisan
    'Sulawesi tengah': 'Sulawesi Tengah',
    'Kepulauan bangka Belitung': 'Kepulauan Bangka Belitung',
    'Kepulauan Bangka belitung': 'Kepulauan Bangka Belitung',
    'Bangka Belitung': 'Kepulauan Bangka Belitung',
    'Kelimantan Selatan': 'Kalimantan Selatan',
    'kalimantan Tengah': 'Kalimantan Tengah',

    # Kabupaten/kota yang masuk ke kolom Provinsi
    'Cirebon': 'Jawa Barat',
    'Subang': 'Jawa Barat',
    'Aceh Tengah': 'Aceh',
    'Sumba Timur': 'Nusa Tenggara Timur',

    # Nama terlalu umum / ambiguous
    'Riau, Sumatera Barat': 'Riau',
    'Kepulauan Maluku': 'Maluku',
    'Yogyakarta': 'DI Yogyakarta',
    'DIY': 'DI Yogyakarta',
    'Sulawesi': 'Sulawesi Tengah',
    'Jawa': 'Jawa Tengah',

    # Missing-like value
    'nan': np.nan,
    'NaN': np.nan,
    'None': np.nan,
    '': np.nan,
}

# Province -> island grouping
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
}
