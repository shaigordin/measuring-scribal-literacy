"""Full titles for the Konkordanz's short citations (series and journal abbreviations).

Downloads the Konkordanz's list of abbreviations (hethport.net/hetkonk/hetkonkabkrz.html), parses its
two-column table and keeps the entries the release cites (the studies in release/traditions.csv),
so that release_docs.py can expand "Kümmel 1967 (StBoT 3)" into a full reference.

Usage: python3 konkordanz_abbreviations.py [--release release] [--out labels/konkordanz_abbreviations.csv]
"""
import argparse
import html
import re
import urllib.request
from datetime import date

import pandas as pd

URL = "https://hethport.net/hetkonk/hetkonkabkrz.html"
ALIAS = {"ArAn": "ArchAn"}               # the Konkordanz cites ArAn, its list spells it ArchAn


def table(page):
    out = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)[:2]]
        if len(cells) == 2 and cells[0]:
            out[cells[0]] = cells[1]
    return out


def keys(venue):
    """'JCS 18' -> ['JCS 18', 'JCS']; 'StBoT 72,1' -> ['StBoT 72,1', 'StBoT 72', 'StBoT']."""
    v = ALIAS.get(venue.split(" ")[0], venue.split(" ")[0]) + venue[len(venue.split(" ")[0]):]
    out = [v, re.sub(r",\s?\d+$", "", v)]
    if not v.startswith("Fs"):                       # a Festschrift is listed under its own name only
        out.append(v.split(" ")[0])
    return list(dict.fromkeys(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", default="release")
    ap.add_argument("--out", default="labels/konkordanz_abbreviations.csv")
    a = ap.parse_args()
    page = urllib.request.urlopen(URL, timeout=60).read().decode("utf-8")
    D = table(page)
    T = pd.read_csv(f"{a.release}/traditions.csv")
    venues = set()
    for col in ["most_cited_study", "first_study", "latest_study"]:
        venues |= {re.search(r"\((.*)\)$", s).group(1) for s in T[col]}
    venues |= {"HbOr I/15", "StBoT 57", "DBH 19"}
    rows = []
    for v in sorted(venues):
        hit = next((k for k in keys(v) if k in D), None)
        rows.append({"venue": v, "abbreviation": hit or "", "full": D.get(hit, "") if hit else "",
                     "source": URL, "accessed": date.today().isoformat()})
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print(pd.DataFrame(rows)[["venue", "abbreviation", "full"]].to_string())


if __name__ == "__main__":
    main()
