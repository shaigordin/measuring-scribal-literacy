"""The physical pieces of TLHdig texts.

A TLHdig text whose id ends in "+" is a join of several fragments. Its header names them,
  <AO:TxtPubl>IBoT 4.7 {€1} + KUB 31.1 {€2} + KBo 3.16 {€3}</AO:TxtPubl>
  <AO:InvNr>Bo 1309 {€1} + Bo 785 {€2} + Bo 433 {€3}</AO:InvNr>
and every line says which pieces it is preserved on: lnr " {€1+2} Obv. II 2′". A line on one piece
only belongs to that piece; a line running across the join ({€1+2}) is left out of both, so that
each piece keeps only the words written on it.

`headers(xml_dir)` reads publication and find (inventory) number of every piece of every text;
`split(tokens)` gives one row per word with its piece number (None for lines across a join).
"""
import re
from pathlib import Path

import pandas as pd

PIECE = re.compile(r"\{€([\d+]+)\}")
TAG = {"publ": re.compile(r"<AO:TxtPubl>(.*?)</AO:TxtPubl>", re.S), "inv": re.compile(r"<AO:InvNr>(.*?)</AO:InvNr>", re.S)}
DOC = re.compile(r"<docID>(.*?)</docID>")


def _items(s):
    """'IBoT 4.7 {€1} + KUB 31.1 {€2}' -> {1: 'IBoT 4.7', 2: 'KUB 31.1'} (unnumbered: {1: s})."""
    s = re.sub(r"<[^>]+>", "", s).strip()
    found = re.findall(r"(.*?)\{€(\d+)\}\s*\+?\s*", s)
    if not found:
        return {1: s} if s else {}
    return {int(n): x.strip().strip("+").strip() for x, n in found}


def headers(xml_dir) -> pd.DataFrame:
    rows = []
    for f in sorted(Path(xml_dir).glob("*/*.xml")):
        t = f.read_text(encoding="utf-8", errors="replace")[:20000]
        doc = DOC.search(t)
        if not doc:
            continue
        publ = _items(TAG["publ"].search(t).group(1)) if TAG["publ"].search(t) else {}
        inv = _items(TAG["inv"].search(t).group(1)) if TAG["inv"].search(t) else {}
        for n in sorted(set(publ) | set(inv)):
            rows.append({"txtid": doc.group(1).strip(), "piece": n, "publication": publ.get(n, ""),
                         "inventory": inv.get(n, "")})
    return pd.DataFrame(rows).drop_duplicates(["txtid", "piece"])


def piece_of(lnr) -> int | None:
    """Piece number of a line, or None when the line runs across pieces or has no marker."""
    m = PIECE.search(str(lnr))
    if not m or "+" in m.group(1):
        return None
    return int(m.group(1))
