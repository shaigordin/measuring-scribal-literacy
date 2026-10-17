"""Labels from the Konkordanz der hethitischen Keilschrifttafeln (S. Košak, hethport.net).

For one CTH number the Konkordanz lists every fragment with its find number, publication,
CTH designation including the edition's sub-numbering (e.g. 701.a₁.3 = Salvini-Wegner group a₁,
manuscript 3) and its date (ah./mh./jh. ...). This module downloads that page once, keeps the
HTML in a cache folder (so later runs read exactly the same table), and turns it into a CSV.

The experiments read `labels(...)`: one row per fragment keyed like a TLHdig txtid, with
`sub-category` (the edition group, or the bare CTH number when the Konkordanz gives none or an
uncertain one such as "?") and `Zeit` (the Konkordanz date).

Usage: python -m qtm.konkordanz 701 data/konkordanz labels/cth701_labels.csv
"""
import datetime
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd
from lxml import html

URL = "https://hethport.net/hetkonk/hetkonk_abfrage.php?c={cth}"


def fetch(cth: str, cache: Path) -> str:
    cache.mkdir(parents=True, exist_ok=True)
    f = cache / f"hetkonk_c{cth}.html"
    if not f.exists():
        req = urllib.request.Request(URL.format(cth=cth), headers={"User-Agent": "measuring-scribal-literacy"})
        f.write_bytes(urllib.request.urlopen(req, timeout=120).read())
        (cache / f"hetkonk_c{cth}.accessed").write_text(datetime.date.today().isoformat() + "\n")
    return f.read_text(encoding="utf-8", errors="replace")


def parse(page: str, cth: str) -> pd.DataFrame:
    rows = []
    for tr in html.fromstring(page).iter("tr"):
        tds = tr.findall("td")
        ids = [td.get("id") for td in tds]
        if len(tds) < 7 or ids[0] != "y1":
            continue
        y3 = [td for td in tds if td.get("id") == "y3"]
        y4 = [td for td in tds if td.get("id") == "y4"]
        if len(y3) < 2 or not y4:
            continue
        cth_full = " ".join(y3[1].text_content().split())
        if not cth_full.startswith(cth):
            continue
        parts = cth_full[len(cth):].lstrip(".").split(".")
        rows.append({"fundnr": " ".join(tds[0].text_content().split()),
                     "publication": " ".join(y3[0].text_content().split()),
                     "cth_full": cth_full,
                     "subgroup": parts[0] if parts and parts[0] else None,
                     "manuscript": ".".join(parts[1:]) or None,
                     "date": " ".join(y4[0].text_content().split()) or None})
    return pd.DataFrame(rows)


def labels(df: pd.DataFrame, cth: str, groups=None) -> pd.DataFrame:
    """Experiment labels. `groups` lists the valid edition groups; anything else is unclassified."""
    key = df.publication.where(df.publication.str.len() > 1, df.fundnr)  # unpublished: "." -> find number
    ok = df.subgroup.isin(groups) if groups else df.subgroup.notna() & (df.subgroup != "?")
    out = pd.DataFrame({"txtid": key.str.rstrip("+").str.strip(), "cth_full": df.cth_full,
                        "sub-category": df.subgroup.where(ok, cth), "Zeit": df.date})
    return out.drop_duplicates("txtid")


# Salvini-Wegner, ChS I/2 groups as written in the Konkordanz
CTH701_GROUPS = ["a", "a₁", "b", "b₁", "b₂", "c", "d", "e", "f"]

if __name__ == "__main__":
    cth, cache, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    df = parse(fetch(cth, cache), cth)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    lab = labels(df, cth, CTH701_GROUPS if cth == "701" else None)
    lab.to_csv(out, index=False)
    acc = (cache / f"hetkonk_c{cth}.accessed").read_text().strip()
    Path(out).with_suffix(".source.txt").write_text(f"{URL.format(cth=cth)}\naccessed {acc}\n")
    print(len(lab), "fragments;", lab["sub-category"].value_counts().to_dict(), lab.Zeit.value_counts().head(8).to_dict())
