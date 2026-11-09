"""Snapshot the CTH titles of the TLHdig index (hethport.net/TLHdig/tlh_idx1.php) to a CSV.

The page is downloaded once and kept in sources/, so later builds read the same titles.

Usage: python build/cth_titles.py [--out sources]
"""
import argparse
import csv
import datetime
import html
import os
import re
import urllib.request

URL = "https://hethport.net/TLHdig/tlh_idx1.php"
ITEM = re.compile(r"<a href='tlh_idx2\.php\?t=CTH ([^']+)'><b>CTH [^<]+</b>:\s*(.*?)</a>", re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sources"))
    a = ap.parse_args()
    raw = os.path.join(a.out, "tlh_idx1.html")
    if not os.path.exists(raw):
        req = urllib.request.Request(URL, headers={"User-Agent": "measuring-scribal-literacy"})
        with open(raw, "wb") as f:
            f.write(urllib.request.urlopen(req, timeout=120).read())
        with open(raw.replace(".html", ".accessed"), "w") as f:
            f.write(f"{URL}\n{datetime.date.today().isoformat()}\n")
    page = open(raw, encoding="utf-8", errors="replace").read()
    rows = [(cth.strip(), " ".join(html.unescape(re.sub("<[^>]+>", "", t)).split())) for cth, t in ITEM.findall(page)]
    with open(os.path.join(a.out, "cth_titles.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["cth", "title"])
        w.writerows(rows)
    print(f"{len(rows)} CTH titles")


if __name__ == "__main__":
    main()
