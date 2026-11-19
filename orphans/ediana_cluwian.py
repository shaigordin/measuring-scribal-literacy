"""Cuneiform Luwian word forms and their lemmata from eDiAna, for filling TLHdig's missing analyses.

eDiAna: Digital Philological-Etymological Dictionary of the Minor Ancient Anatolian Corpus Languages
(LMU München, https://www.ediana.gwi.uni-muenchen.de/, CC BY-SA 4.0). Its Cuneiform Luwian corpus
lemmatises the Luwian words of each line. This script downloads every Cuneiform Luwian text through
the site's own corpus interface (includes/api.php, as corpus.php calls it), caches the answers in
data/ediana/ and writes one row per lemmatised word: text, line, spelling, lemma, translation, part
of speech and grammar.

Usage: python3 ediana_cluwian.py [--cache data/ediana] [--out data/ediana_cluwian_forms.csv]
"""
import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = "https://www.ediana.gwi.uni-muenchen.de"
UA = {"User-Agent": "Mozilla/5.0 (research script; TLHdig/eDiAna lemma lookup)"}


def get(url, data=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers=UA)
    return urllib.request.urlopen(req, timeout=120).read().decode("utf-8")


def cells(table):
    rows = re.findall(r"<tr>(.*?)</tr>", table or "", re.S)
    return [[html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
            for r in rows]


def tokens(sentence):
    s = re.sub(r"<span class=sup>(.*?)</span>", r"{\1}", sentence or "")
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xa0", " ")
    return s.split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="data/ediana")
    ap.add_argument("--out", default="data/ediana_cluwian_forms.csv")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    page = cache / "corpus.html"
    if not page.exists():
        page.write_text(get(f"{BASE}/corpus.php"), encoding="utf-8")
    s = page.read_text(encoding="utf-8")
    j = s.find('id="c_luwian_table"')
    docs = re.findall(r"docid='(\d+)' langid='cuneiform' >([^<]+)<", s[j:s.find("</table>", j)])
    rows, skipped = [], 0
    for docid, name in docs:
        f = cache / f"cluw_{docid}.json"
        if not f.exists():
            f.write_text(get(f"{BASE}/includes/api.php", {"searchterms[lem]": "", "corpus_text": "true",
                                                          "language": "cuneiform", "docids": docid}), encoding="utf-8")
            time.sleep(0.5)
        got = json.loads(f.read_text(encoding="utf-8") or "{}")
        for text, lines in (got.items() if isinstance(got, dict) else []):
            for e in lines:
                c = cells(e.get("sentence_total"))
                toks = tokens(e.get("sentence"))
                if len(c) < 6 or not any(any(r) for r in c):
                    continue
                if any(len(r) != len(toks) for r in c):
                    skipped += 1
                    continue
                for i, t in enumerate(toks):
                    if c[2][i]:
                        rows.append({"text": text, "docid": docid, "line": e["word"].lstrip("· ").strip(),
                                     "spelling": t, "lemma": c[2][i], "translation": c[3][i], "pos": c[4][i],
                                     "grammar": c[5][i]})
    df = pd.DataFrame(rows)
    df.to_csv(a.out, index=False)
    print(f"{len(docs)} texts, {len(df)} lemmatised words, {df.lemma.nunique()} lemmata; {skipped} lines not aligned")


if __name__ == "__main__":
    main()
