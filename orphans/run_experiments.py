"""Orphans and Archetypes: experiments for the Mainz Hittite & AI workshop.

E1  Reference space: leave-one-text-out nearest-centroid assignment across traditions
    (word tf-idf vs sign n-grams vs both), with a label-permutation baseline.
E2  Coverage curve: how assignment accuracy falls as witnesses shrink to k-word windows
    (simulates orphan-sized fragments from well-attested texts).
E3  CTH 701 internal validation: same procedure on the Salvini-Wegner subgroups
    (needs a `subgroup` column; skipped otherwise).
E4  Ablation: drop logograms (Sumero-/Akkadograms) to separate scribal orthography
    from cultic vocabulary.
E5  Orphan placement: score each orphan against every tradition centroid, with an
    open-set abstention margin calibrated on E2.

Usage: python run_experiments.py CORPUS.csv [--orphans ORPHANS.csv] [--out results]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from qtm.corpus import load
from qtm.features import tokens, vectorizer
from qtm.assign import centroids, scores, assign

REF = ["670", "701", "832"]                 # traditions named in the abstract
CONTROLS = ["628", "699", "500", "694"]     # well-defined controls
MIN_WORDS = 17                              # as in Gordin, Yavasan & Romach 2025
RNG = np.random.default_rng(0)


def loo_accuracy(docs, label_col, space, n_perm=200, **kw):
    """Leave-one-text-out nearest-centroid accuracy and permutation p-value."""
    toks = [tokens(d, space, **kw) for _, d in docs.iterrows()]
    X = vectorizer().fit_transform(toks)
    y = docs[label_col].to_numpy()

    def run(labels):
        hits = 0
        for i in range(len(labels)):
            mask = np.arange(len(labels)) != i
            C, labs = centroids(X[mask], labels[mask])
            pred, _, _ = assign(scores(X[i], C), labs)
            hits += pred[0] == labels[i]
        return hits / len(labels)

    acc = run(y)
    null = np.array([run(RNG.permutation(y)) for _ in range(n_perm)])
    majority = pd.Series(y).value_counts(normalize=True).iloc[0]
    return {"acc": acc, "majority": majority, "null_mean": null.mean(),
            "p": (1 + (null >= acc).sum()) / (1 + n_perm), "n": len(y)}


def coverage_curve(docs, label_col, space, ks=(5, 10, 17, 25, 40, 60), reps=20):
    """Accuracy when a held-out text is cut to a random contiguous k-word window."""
    rows = []
    for k in ks:
        hits = tot = 0
        for i, d in docs.iterrows():
            if d.n_words < k:
                continue
            train = docs.drop(index=i)
            vec = vectorizer()
            X = vec.fit_transform([tokens(r, space) for _, r in train.iterrows()])
            C, labs = centroids(X, train[label_col].to_numpy())
            for _ in range(reps):
                s = RNG.integers(0, d.n_words - k + 1)
                frag = {"words": d.words[s:s + k], "signs": d.signs[s:s + k]}
                pred, top, gap = assign(scores(vec.transform([tokens(frag, space)]), C), labs)
                hits += pred[0] == d[label_col]
                tot += 1
        rows.append({"k": k, "space": space, "acc": hits / tot if tot else np.nan, "n": tot})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpus")
    ap.add_argument("--orphans")
    ap.add_argument("--out", default="results")
    ap.add_argument("--perm", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    docs = load(a.corpus, cths=REF + CONTROLS, min_words=MIN_WORDS)
    docs.groupby("cth_number").n_words.describe().to_csv(f"{a.out}/corpus_stats.csv")
    report = {}

    for name, sub in {"E1_abstract_ref": docs[docs.cth_number.isin(REF)],
                      "E1_with_controls": docs}.items():
        report[name] = {sp: loo_accuracy(sub, "cth_number", sp, a.perm)
                        for sp in ("words", "signs", "both")}

    report["E4_no_logograms"] = {sp: loo_accuracy(docs, "cth_number", sp, a.perm, drop_logograms=True)
                                 for sp in ("words", "signs")}

    curve = sum((coverage_curve(docs, "cth_number", sp) for sp in ("words", "signs", "both")), [])
    pd.DataFrame(curve).to_csv(f"{a.out}/E2_coverage_curve.csv", index=False)

    if "subgroup" in docs.columns:
        d701 = docs[(docs.cth_number == "701") & docs.subgroup.notna()]
        d701 = d701[d701.subgroup.map(d701.subgroup.value_counts()) >= 3]
        report["E3_cth701_subgroups"] = {sp: loo_accuracy(d701, "subgroup", sp, a.perm)
                                         for sp in ("words", "signs", "both")}

    if a.orphans:
        orph = load(a.orphans, min_words=5)
        vec = vectorizer()
        X = vec.fit_transform([tokens(r, "both") for _, r in docs.iterrows()])
        C, labs = centroids(X, docs.cth_number.to_numpy())
        S = scores(vec.transform([tokens(r, "both") for _, r in orph.iterrows()]), C)
        pred, top, gap = assign(S, labs, margin=0.02)
        out = pd.DataFrame(S, columns=[f"sim_{l}" for l in labs])
        out.insert(0, "txtid", orph.txtid)
        out.insert(1, "n_words", orph.n_words)
        out["assigned"], out["top"], out["gap"] = pred, top, gap
        out.to_csv(f"{a.out}/E5_orphan_placement.csv", index=False)

    with open(f"{a.out}/report.json", "w") as f:
        json.dump(report, f, indent=2, default=float)
    print(json.dumps(report, indent=2, default=float))


if __name__ == "__main__":
    main()
