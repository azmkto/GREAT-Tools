"""Generate `great/_regions.py` from the official BPS region-code CSV.

The CSV encodes the hierarchy in `kode_wilayah`: a code with no dot is a province ("96" =
Papua Barat Daya), a code with one dot is a kabupaten/kota inside it ("96.01"). That parent
relationship is the whole point -- it gives an authoritative city -> province mapping that
does not have to be maintained by hand.

Run it whenever BPS publishes an update:

    py -3.11 tools/build_regions.py "<path to kota_kabupaten_provinsi.csv>"

Defaults to the copy under Data/Iklim dan Lingkungan. Writes great/_regions.py; review the
diff before committing, since a bad CSV would silently rewrite the whole vocabulary.
"""
import argparse
import os
import re
import sys

import pandas as pd

DEFAULT_CSV = os.path.join(
    r"C:\Users\ASUS\Documents\Research Project\Data", "Iklim dan Lingkungan",
    "kota_kabupaten_provinsi.csv",
)
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "great", "_regions.py")

# KAB. / KABUPATEN / KAB / KOTA, with or without the trailing dot. Two rows in the current
# CSV use "KAB " with no dot, hence the optional dot rather than a literal "KAB.".
PREFIX = re.compile(r"^(?:KAB\.?|KABUPATEN|KOTA(?:\s+ADM\.?)?)\s+", re.I)

# Words that are part of a name rather than a rank, so Title Case does not mangle them.
KEEP_UPPER = {"DKI", "DI"}

# Where the library's canonical spelling differs from the CSV's. `great.geo` has always used
# "DI Yogyakarta" -- PROVINCE_FIX, GEO_FIX, the gazetteer and the GeoJSON join all point at it
# -- so the generated data uses that rather than forcing a rename across the whole package.
# The CSV's longer form survives as an alias in GEO_FIX, which is what the GeoJSON needs.
CANONICAL_OVERRIDE = {
    "Daerah Istimewa Yogyakarta": "DI Yogyakarta",
}


def collapse(text):
    """Collapse runs of whitespace. Fixes the CSV's own 'P A P U A' -> 'P A P U A' -> 'PAPUA'."""
    return " ".join(str(text).split())


def title_case(name):
    """Title Case for display, preserving DKI / DI and not lowercasing inside words."""
    parts = []
    for word in collapse(name).split():
        parts.append(word.upper() if word.upper() in KEEP_UPPER else word.capitalize())
    return " ".join(parts)


def fix_province(raw):
    """'P A P U A' -> 'Papua'. Single letters separated by spaces are a CSV formatting quirk."""
    text = collapse(raw)
    if len(text) > 1 and all(len(tok) == 1 for tok in text.split()):
        text = "".join(text.split())
    name = title_case(text)
    return CANONICAL_OVERRIDE.get(name, name)


def normalize_key(name):
    """The lookup key: casefolded, whitespace-collapsed, rank prefix removed."""
    text = collapse(name)
    text = PREFIX.sub("", text)
    return text.casefold()


def build(csv_path):
    df = pd.read_csv(csv_path, dtype=str).fillna("")
    df["kode_wilayah"] = df["kode_wilayah"].str.strip()
    df["provinsi_kabupaten_kota"] = df["provinsi_kabupaten_kota"].str.strip()

    is_province = ~df["kode_wilayah"].str.contains(r"\.", regex=True)
    prov_rows = df[is_province]
    kab_rows = df[df["kode_wilayah"].str.count(r"\.") == 1]

    provinces = {r["kode_wilayah"]: fix_province(r["provinsi_kabupaten_kota"])
                 for _, r in prov_rows.iterrows()}

    regencies = {}
    region_to_province = {}
    for _, row in kab_rows.iterrows():
        code = row["kode_wilayah"]
        parent = code.split(".")[0]
        province = provinces.get(parent)
        if province is None:
            print(f"  WARNING: {code} {row['provinsi_kabupaten_kota']!r} has no province {parent}",
                  file=sys.stderr)
            continue
        full = collapse(row["provinsi_kabupaten_kota"])
        regencies[code] = title_case(full)
        # bare name ("bandung") and the prefixed form ("kota bandung") both resolve
        region_to_province[normalize_key(full)] = province
        region_to_province[collapse(full).casefold()] = province

    return provinces, regencies, region_to_province


def emit(provinces, regencies, region_to_province, csv_path):
    def dict_lines(d, sort_key=None):
        items = sorted(d.items(), key=sort_key) if sort_key else sorted(d.items())
        return "\n".join(f"    {k!r}: {v!r}," for k, v in items)

    by_code = lambda kv: (int(kv[0].split(".")[0]), kv[0])

    return f'''"""Official Indonesian region codes -- GENERATED, DO NOT EDIT BY HAND.

Regenerate with `py -3.11 tools/build_regions.py` after updating the source CSV.
Source: {os.path.basename(csv_path)} ({len(provinces)} provinces, {len(regencies)} kabupaten/kota).

`kode_wilayah` encodes the hierarchy: "96" is a province, "96.01" a kabupaten/kota inside it.
`REGION_TO_PROVINCE` keys are normalised (casefolded, whitespace collapsed, KAB./KOTA prefix
stripped) and carry both the bare and prefixed forms, so "bandung" and "kota bandung" both hit.
"""

# code -> province name, Title Case for display
PROVINCES = {{
{dict_lines(provinces, by_code)}
}}

# code -> kabupaten/kota name, rank prefix kept
REGENCIES = {{
{dict_lines(regencies, by_code)}
}}

# normalised kabupaten/kota name -> province name
REGION_TO_PROVINCE = {{
{dict_lines(region_to_province)}
}}
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv", nargs="?", default=DEFAULT_CSV)
    ap.add_argument("-o", "--out", default=OUT)
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        sys.exit(f"CSV not found: {args.csv}")

    provinces, regencies, region_to_province = build(args.csv)

    if len(provinces) != 38:
        print(f"  WARNING: {len(provinces)} provinces, expected 38", file=sys.stderr)

    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(emit(provinces, regencies, region_to_province, args.csv))

    print(f"  {len(provinces)} provinces, {len(regencies)} kabupaten/kota, "
          f"{len(region_to_province)} lookup keys")
    print(f"  wrote {args.out}")


if __name__ == "__main__":
    main()
