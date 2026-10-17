"""Descriptive numbers quoted on the slides that are not experiment outputs.

- orphan corpus: CTH 470 and EBo texts, their size in legible words, and where TLHdig files EBo texts
- plene clusters: for the spelling contrasts of E7d, how many texts use the plene spelling and in which CTHs

Usage: python stats_corpus.py TOKENS.csv --out results/<run>   (writes corpus_stats.json)
"""
import argparse
import json

import numpy as np
import pandas as pd

from qtm.corpus import load
from qtm.groups import GROUPSETS, label_map, is_orphan
from qtm.layers import has_plene
from run_experiments import MIN_WORDS
from run_profiles import CONTRAST_WORDS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--out", default="results/run")
    ap.add_argument("--groups", choices=sorted(GROUPSETS), default="historical")
    a = ap.parse_args()
    out = {}

    docs = load(a.tokens)
    c470 = docs[docs.cth_number == "470"]
    ebo = docs[docs.txtid.str.startswith("EBo")]
    out["orphans"] = {
        "cth470_texts": int(len(c470)), "cth470_median_words": float(c470.n_words.median()),
        "ebo_texts": int(len(ebo)), "ebo_median_words": float(ebo.n_words.median()),
        "ebo_filed_under": ebo.cth_number.value_counts().head(10).to_dict(),
        "orphans_total": int(sum(is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)))}

    hist = label_map(GROUPSETS[a.groups])
    ref = docs[docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)
               & np.array([not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)])]
    rows = [{"word": w, "tradition": hist[d.cth_number], "cth": d.cth_number, "txtid": d.txtid, "plene": has_plene(sg)}
            for _, d in ref.iterrows() for w, sg in zip(d.words, d.signs) if w in CONTRAST_WORDS]
    r = pd.DataFrame(rows)
    clusters = {}
    for (w, t), g in r.groupby(["word", "tradition"]):
        p = g[g.plene]
        clusters.setdefault(w, {})[t] = {"texts": int(g.txtid.nunique()), "texts_with_plene": int(p.txtid.nunique()),
                                         "plene_cths": sorted(p.cth.unique().tolist(), key=int)}
    out["plene_clusters"] = clusters

    with open(f"{a.out}/corpus_stats.json", "w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out["orphans"], indent=1))


if __name__ == "__main__":
    main()
