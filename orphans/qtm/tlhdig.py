"""Parse the TLHdig XML release (Zenodo 10.5281/zenodo.20328284) into a token table.

One row per <w> word: txtid, cth_number, source (HFR/TLH/...), lnr, lang, word, translit.
`word` is the normalised form from the `trans` attribute; `translit` is the sign
sequence with determinatives as {DET}. Words that are wholly or partly illegible
(`%` in trans, or only `x` signs) keep their translit but get an empty `word`.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

FOLDER = re.compile(r"CTH (\d+)[^_]*_XML_(\w+)")
SKIP = {"space", "del_in", "del_fin", "laes_in", "laes_fin", "corr", "note", "gap"}


def _text(node):
    """Sign text of an element; determinatives become {DET}, sign groups are space-separated."""
    tag = etree.QName(node).localname if isinstance(node.tag, str) else ""
    if tag in SKIP:
        return ""
    inner = (node.text or "") + "".join(_text(c) + (c.tail or "") for c in node)
    if tag == "d":
        return "{" + inner + "}"
    if tag in ("aGr", "sGr"):
        return " " + inner + " "
    return inner


def _translit(w):
    t = (w.text or "") + "".join(_text(c) + (c.tail or "") for c in w)
    t = re.sub(r"\s*-\s*", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_file(path, cth, source):
    tree = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True))
    rows, lnr, lang, txtid = [], None, None, None
    doc = tree.find(".//docID")
    txtid = doc.text.strip() if doc is not None and doc.text else Path(path).stem
    for el in tree.iter("lb", "w"):
        if el.tag == "lb":
            lnr, lang = el.get("lnr"), el.get("lg")
            continue
        tl = _translit(el)
        if not tl:
            continue
        trans = el.get("trans") or ""
        word = "" if ("%" in trans or not re.search(r"[^x\s\-.]", tl.replace("x", ""))) else trans
        rows.append((txtid, cth, source, lnr, lang, word, tl))
    return rows


def parse_release(root, cths=None):
    out = []
    for d in sorted(Path(root).iterdir()):
        m = FOLDER.match(d.name)
        if not m or (cths and m.group(1) not in cths):
            continue
        for f in d.rglob("*.xml"):
            try:
                out += parse_file(f, m.group(1), m.group(2))
            except Exception as e:  # malformed files are logged, not fatal
                print(f"skip {f}: {e}", file=sys.stderr)
    df = pd.DataFrame(out, columns=["txtid", "cth_number", "source", "lnr", "lang", "word", "translit"])
    # the same manuscript can appear in an HFR and a TLH folder: keep the HFR copy
    rank = df.source.map({"HFR": 0}).fillna(1)
    keep = df.assign(r=rank).groupby("txtid").r.transform("min") == rank
    return df[keep].reset_index(drop=True)


if __name__ == "__main__":
    root, out = sys.argv[1], sys.argv[2]
    cths = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    df = parse_release(root, cths)
    df.to_csv(out, index=False)
    print(df.groupby("cth_number").txtid.nunique().to_string())
