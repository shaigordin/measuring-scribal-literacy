"""Per-word writing layers of a worked-example text, for the figure's typography.

Reads the text's TLHdig XML with orphans/qtm/tlhdig.py and writes figures/data/marks_<id>.csv:
one row per word, in the order of the case file's tokens (line, position, editors' transliteration,
layer). The layer has one letter per sign: H phonetic (Hittite and other languages, set in
italics), A Akkadogram (italic capitals), S Sumerogram (upright capitals), d determinative.

Usage: python3 make_case_marks.py "<TLHdig>/CTH 470_XML_TLH/KBo 44.52.xml" 470
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "orphans"))
from qtm import tlhdig  # noqa: E402


def main():
    xml, cth = sys.argv[1], sys.argv[2]
    rows = tlhdig.parse_file(xml, cth, "TLH")
    txtid = rows[0][0]
    out = os.path.join(HERE, "figures", "data", f"marks_{txtid.replace(' ', '_').replace('.', '_')}.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    k = len(tlhdig.MARK_COLS)
    layer_at = len(rows[0]) - k + tlhdig.MARK_COLS.index("layer")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lnr", "pos", "translit_ed", "layer"])
        pos, cur = 0, None
        for r in rows:
            pos = pos + 1 if r[3] == cur else 0
            cur = r[3]
            w.writerow([r[3], pos, r[6], r[layer_at]])
    print("wrote", out)


if __name__ == "__main__":
    main()
