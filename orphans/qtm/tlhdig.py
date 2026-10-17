"""Parse the TLHdig XML release (Zenodo 10.5281/zenodo.20328284) into a token table.

One row per word: txtid, cth_number, source (HFR/TLH/...), lnr, lang, word, translit, wclass,
wc_rule, wc_conf. A <w> that holds an Akkadographic preposition and its noun (A-NA {GIŠ}BANŠUR)
becomes two rows, the preposition and the noun (see qtm.wordclass).
`word` is the normalised form from the `trans` attribute; `translit` is the sign
sequence with determinatives as {DET}. `wclass` is the word class from qtm.wordclass, `wc_rule` the
rule that set it and `wc_conf` its confidence; manual corrections from a CSV (word, translit,
wclass, note, reviewer; translit empty = every occurrence of the word) override them. Words that are wholly or partly illegible
(`%` in trans, or only `x` signs) keep their translit but get an empty `word`.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

from .wordclass import RULES, is_preposition, word_class_rule

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
        if not word:
            rows.append((txtid, cth, source, lnr, lang, word, tl, "", ""))
            continue
        head, _, rest = word.partition(" ")
        if is_preposition(head):
            # the preposition, then (if any) the noun with its own analysis
            rows.append((txtid, cth, source, lnr, lang, head, head, "function", "preposition_split"))
            if rest:
                rtl = tl[len(head):].strip() if tl.startswith(head + " ") else tl
                wc, rule = word_class_rule({**el.attrib, "trans": rest}, rtl, lang)
                rows.append((txtid, cth, source, lnr, lang, rest, rtl, wc, rule))
            continue
        wc, rule = word_class_rule(el.attrib, tl, lang)
        rows.append((txtid, cth, source, lnr, lang, word, tl, wc, rule))
    return rows


def apply_corrections(df, path):
    """Manual word-class corrections; a row with a translit applies only to that spelling."""
    if not path or not Path(path).exists():
        return df
    cor = pd.read_csv(path, dtype=str).fillna("")
    for _, c in cor.iterrows():
        hit = df.word == c.word
        if c.translit:
            hit &= df.translit == c.translit
        df.loc[hit, ["wclass", "wc_rule"]] = [c.wclass, "manual"]
    return df


def parse_release(root, cths=None):
    out = []
    for d in sorted(Path(root).iterdir()):
        m = FOLDER.match(d.name)
        if not m or (cths and m.group(1) not in cths):
            continue
        for f in sorted(d.rglob("*.xml")):  # sorted: same row order on every filesystem
            try:
                out += parse_file(f, m.group(1), m.group(2))
            except Exception as e:  # malformed files are logged, not fatal
                print(f"skip {f}: {e}", file=sys.stderr)
    df = pd.DataFrame(out, columns=["txtid", "cth_number", "source", "lnr", "lang", "word", "translit", "wclass", "wc_rule"])
    # the same manuscript can appear in an HFR and a TLH folder: keep the HFR copy
    rank = df.source.map({"HFR": 0}).fillna(1)
    keep = df.assign(r=rank).groupby("txtid").r.transform("min") == rank
    return df[keep].reset_index(drop=True)


def finish(df, corrections=None):
    df = apply_corrections(df, corrections)
    df["wc_conf"] = df.wc_rule.map(RULES).fillna("")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("cths", nargs="?")
    ap.add_argument("--corrections", default=str(Path(__file__).parent.parent / "labels" / "wordclass_corrections.csv"))
    a = ap.parse_args()
    df = finish(parse_release(a.root, a.cths.split(",") if a.cths else None), a.corrections)
    df.to_csv(a.out, index=False)
    print(df.groupby("cth_number").txtid.nunique().to_string())
