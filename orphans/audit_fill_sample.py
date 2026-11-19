"""Random sample of filled analyses (fill_lemmas.py) for a manual check, reportable as a robustness audit.

Draws, with a fixed seed, a simple random sample of filled words from each source, so that the share
judged correct estimates the accuracy of each fill over all filled words (token-weighted):
  - 200 of the words filled from the same spelling elsewhere in TLHdig;
  - 100 of the words filled from eDiAna (Luwian).
With about 90% correct, 200 words give a 95% interval of roughly ±4 points and 100 words ±6 points.
Each row shows the word in its line, the filled lemma and word class, the source, and empty columns
for the check: correct (y / n / ?), correct lemma if not, note.

Usage: python3 audit_fill_sample.py data/tokens_marks_filled.csv --out results/fill_audit_sample.csv
"""
import argparse

import pandas as pd

N = {"filled_tlhdig": 200, "filled_ediana": 100}
LABEL = {"filled_tlhdig": "TLHdig same spelling", "filled_ediana": "eDiAna"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filled")
    ap.add_argument("--out", default="results/fill_audit_sample.csv")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    df = pd.read_csv(a.filled, dtype=str, keep_default_na=False)
    line = df.groupby(["txtid", "lnr"], sort=False).translit.agg(" ".join)
    parts = []
    for rule, n in N.items():
        pool = df[df.wc_rule == rule]
        s = pool.sample(min(n, len(pool)), random_state=a.seed)
        parts.append(s.assign(fill=LABEL[rule], pool_size=len(pool)))
    S = pd.concat(parts)
    S["line_text"] = [line[(t, l)] for t, l in zip(S.txtid, S.lnr)]
    S = S.reset_index(drop=True)
    S.insert(0, "item", range(1, len(S) + 1))
    out = S[["item", "fill", "pool_size", "txtid", "cth_number", "lnr", "line_text", "translit", "word", "wclass",
             "fill_source"]].rename(columns={"translit": "spelling", "word": "filled_lemma", "wclass": "filled_class"})
    out = out.assign(correct="", correct_lemma="", note="")
    out.to_csv(a.out, index=False)
    print(out.groupby("fill").size().to_dict(), "->", a.out)


if __name__ == "__main__":
    main()
