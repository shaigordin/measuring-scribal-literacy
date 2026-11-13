"""Archetype barcodes for one fragment (deck slide "barcode"), in the run's own token version.

An archetype is a tradition's centroid in the words+spellings space (as in E2/E5). For each
reference tradition we take its CORE most characteristic features (largest centroid weights,
strongest first, as the playground's "Archetype barcode" does) and mark which of them the
fragment attests: 'd' distinctive, 'c' common (attested in at least a quarter of the reference
manuscripts, E11's definition, e.g. nu), '.' absent. Rows are sorted by distinctive matches.

Usage: python run_barcode.py results/../tokens_C.csv --run results/tlhdig03_literature_C \
         --txtid "KBo 44.52" --out results/tlhdig03_literature_C/case
"""
import argparse
import json
import os

import numpy as np

from qtm.assign import assign, centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, label_map, is_orphan
from run_attribution import common_mask
from run_experiments import MIN_WORDS, featurise

CORE = 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    hist = label_map(GROUPSETS[rep["groups"]])
    import pandas as pd
    raw = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str}, usecols=["txtid", "cth_number"])
    cth = raw.loc[raw.txtid == a.txtid, "cth_number"].iloc[0]
    docs = load(a.tokens, cths=sorted(set(hist) | {cth}))
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].assign(
        label=lambda d: d.cth_number.map(hist)).reset_index(drop=True)
    frag = docs[docs.txtid == a.txtid].iloc[0]
    vec, X = featurise(ref, "both")
    names = vec.get_feature_names_out()
    C, labs = centroids(X, ref.label.to_numpy())
    x = vec.transform([tokens(frag, "both")])
    s = scores(x, C).ravel()
    pred, top, gap = assign(s[None], labs, margin=rep["E2_abstention"]["margin"])
    has = set(x.indices[x.data > 0].tolist())
    common = np.asarray(common_mask(X)).ravel()
    rows = []
    for j, lab in enumerate(labs):
        core = np.argsort(-C[j])[:CORE]
        cells = "".join(("c" if common[k] else "d") if k in has else "." for k in core)
        rows.append({"tradition": lab, "cells": cells, "attested": sum(c != "." for c in cells),
                     "distinctive": cells.count("d"),
                     "terms": [names[k] for k in core if k in has and not common[k]]})
    rows.sort(key=lambda r: -r["distinctive"])
    o = np.argsort(-s)
    out = {"txtid": a.txtid, "version": os.path.basename(a.run.rstrip("/")), "core": CORE,
           "top": labs[o[0]], "runner_up": labs[o[1]], "margin": round(float(s[o[0]] - s[o[1]]), 4),
           "assigned": None if pred[0] is None else str(pred[0]), "rows": rows}
    os.makedirs(a.out, exist_ok=True)
    fn = os.path.join(a.out, "barcode_" + a.txtid.replace(" ", "_").replace(".", "_").replace("+", "") + ".json")
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False)
    print(fn, out["top"], out["margin"], [(r["tradition"], r["distinctive"]) for r in rows])


if __name__ == "__main__":
    main()
