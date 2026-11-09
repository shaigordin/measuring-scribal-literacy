"""Concrete examples for Test 1 (leave one manuscript out): per manuscript, where it lands.

Writes the leave-one-out placement of every reference manuscript (literature traditions,
17+ words, words+spellings space): true tradition, nearest, runner-up, gap, placed (gap >=
margin) and its transliteration, so the deck can show real hits and misses next to the
corpus accuracy.

Usage: python run_test_examples.py data/tokens.csv --run results/tlhdig03_literature \
         --out results/tlhdig03_literature/case
"""
import argparse
import json

import numpy as np
import pandas as pd

from qtm.assign import assign, loo_scores
from qtm.corpus import load
from qtm.groups import GROUPSETS, is_orphan, label_map
from run_experiments import MIN_WORDS, featurise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--space", default="both")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    docs = load(a.tokens, cths=sorted(hist))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    docs = docs[docs.n_words >= MIN_WORDS].reset_index(drop=True)
    y = docs.cth_number.map(hist).to_numpy()
    _, X = featurise(docs, a.space)
    S, labs = loo_scores(X, y)
    pred, top, gap = assign(S, labs)
    second = labs[np.argsort(-S, axis=1)[:, 1]]
    out = pd.DataFrame({"txtid": docs.txtid, "cth": docs.cth_number, "true": y, "nearest": pred,
                        "runner_up": second, "gap": gap.round(4), "placed": gap >= margin,
                        "right": pred == y, "n_words": docs.n_words,
                        "translit": [" ".join(map(str, t)) for t in docs.translits]})
    out.to_csv(f"{a.out}/test1_loo_placements.csv", index=False)
    print("accuracy", round(out.right.mean(), 3), "n", len(out))
    print(out.groupby("true").right.mean().round(3))


if __name__ == "__main__":
    main()
