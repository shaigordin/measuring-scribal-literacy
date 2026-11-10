"""Studies the Konkordanz cites for each reference tradition: earliest, most recent, most cited.

Reads the cached Konkordanz pages (data/konkordanz/hetkonk_c<CTH>.html, see qtm/konkordanz.py),
takes the notes column of every manuscript row, and extracts citations of the form
"J. Klinger, StBoT 37, 1996, 302-352". Counts each work once per manuscript row. Personal
communications ("Hinweis ...") have no series and are not counted.

Usage: python konkordanz_literature.py --groups literature --out results/konkordanz_literature.csv
"""
import argparse
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd
from lxml import html

from qtm.groups import GROUPSETS

CIT = re.compile(r"((?:[A-ZÄÖÜŠ][a-zäöü]{0,3}\.(?:-[A-Z]\.)?\s?){1,3}(?:(?:de|van|von|del|di)\s)?"
                 r"[A-ZÄÖÜŠÇ][\w’'\-]+(?:[-–][A-ZÄÖÜ][\w’'\-]+)?"
                 r"(?:\s?[–/-]\s?(?:[A-Z][a-z]?\.\s?){1,3}[A-ZÄÖÜ][\w’'\-]+)?)"
                 r",\s([A-Za-zÄÖÜäöü][^,;()]{1,40}?),\s((?:18|19|20)\d\d)\b")


def notes(page):
    for tr in html.fromstring(page).iter("tr"):
        tds = tr.findall("td")
        if len(tds) >= 7 and tds[0].get("id") == "y1":
            yr = [td for td in tds if td.get("id") == "yr"]
            pub = [td for td in tds if td.get("id") == "y3"]
            if yr and pub:
                yield " ".join(pub[0].text_content().split()), " ".join(yr[0].text_content().split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--groups", default="literature")
    ap.add_argument("--cache", default="data/konkordanz")
    ap.add_argument("--out", default="results/konkordanz_literature.csv")
    a = ap.parse_args()
    rows = []
    for tradition, cths in GROUPSETS[a.groups].items():
        count, cths_of, example = defaultdict(int), defaultdict(set), {}
        for cth in cths:
            f = Path(a.cache) / f"hetkonk_c{cth}.html"
            if not f.exists():
                continue
            for pub, note in notes(f.read_text(encoding="utf-8", errors="replace")):
                seen = set()
                for author, venue, year in CIT.findall(note):
                    key = (" ".join(author.split()), " ".join(venue.split()), int(year))
                    if key not in seen:
                        seen.add(key)
                        count[key] += 1
                        cths_of[key].add(str(cth))
                        example.setdefault(key, pub)
        for (author, venue, year), n in count.items():
            rows.append({"tradition": tradition, "author": author, "venue": venue, "year": year,
                         "manuscripts_citing": n, "cths": " ".join(sorted(cths_of[(author, venue, year)])),
                         "example_manuscript": example[(author, venue, year)]})
    df = pd.DataFrame(rows).sort_values(["tradition", "manuscripts_citing"], ascending=[True, False])
    df.to_csv(a.out, index=False)
    for t, g in df.groupby("tradition"):
        print(f"== {t}")
        print("  most cited:", "; ".join(f"{r.author}, {r.venue}, {r.year} ({r.manuscripts_citing})" for r in g.head(4).itertuples()))
        e = g.sort_values("year").head(2); l = g.sort_values("year").tail(2)
        print("  earliest:", "; ".join(f"{r.author}, {r.venue}, {r.year}" for r in e.itertuples()))
        print("  latest:", "; ".join(f"{r.author}, {r.venue}, {r.year}" for r in l.itertuples()))


if __name__ == "__main__":
    main()
