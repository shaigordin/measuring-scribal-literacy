"""Robustness check: does the picture hold when manuscripts without word analyses are included?

TLHdig 0.3 has transliterations but no word analyses for some texts (all of the Luwian corpus,
CTH 758-763, and many BESRIT rituals). The main model needs analysed words, so it leaves these out.
Here every text is read from its spellings only (sign 1-3-grams of every legible word, analysed or
not), so they can join the reference. Compared, in the same spellings space:
  A. reference = analysed manuscripts only (as in the main run, 17+ words)
  B. reference = all manuscripts with 17+ legible words
Reports per-tradition sizes and leave-one-out accuracy, placements of selected fragments, and how
often the orphan placements of the main model (E5) agree with B.

Usage: python run_spellings_only.py data/tokens.csv --run results/tlhdig03_literature
"""
import argparse
import json
import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, loo_scores, scores
from qtm.corpus import signs
from qtm.features import tokens
from qtm.groups import GROUPSETS, is_orphan, label_map
from run_experiments import MIN_WORDS, featurise

PIECES = ["KBo 41.22", "KBo 17.54+", "KUB 35.146", "KBo 61.39", "KBo 47.130+", "EBo 133"]


def legible(t):
    t = str(t)
    return t not in ("nan", "…") and re.search(r"[^x\s\-.…]", t.replace("x", "")) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    raw = pd.read_csv(a.tokens, low_memory=False, dtype=str)
    raw = raw[raw.translit.map(legible)]
    docs = raw.groupby("txtid").agg(cth_number=("cth_number", "first"), translits=("translit", list),
                                    n_analysed=("word", lambda s: int(s.notna().sum()))).reset_index()
    docs["signs"] = docs.translits.map(lambda ts: [signs(t) for t in ts])
    docs["n_legible"] = docs.translits.str.len()
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    docs["trad"] = docs.cth_number.map(hist)
    base = docs[~docs.orphan & docs.trad.notna()]
    refs = {"A_analysed_only": base[base.n_analysed >= MIN_WORDS].reset_index(drop=True),
            "B_all_legible": base[base.n_legible >= MIN_WORDS].reset_index(drop=True)}
    out = {"margin": margin, "space": "signs", "runs": {}}
    orph = docs[docs.orphan & (docs.n_analysed >= 5)].reset_index(drop=True)
    for name, ref in refs.items():
        vec, X = featurise(ref, "signs")
        S, labs = loo_scores(X, ref.trad.to_numpy())
        pred, _, _ = assign(S, labs)
        y = ref.trad.to_numpy()
        C, labs = centroids(X, y)
        run = {"n": int(len(ref)), "loo_acc": round(float(np.mean(pred == y)), 3),
               "per_tradition": {l: {"n": int((y == l).sum()), "loo_acc": round(float(np.mean(pred[y == l] == l)), 3)}
                                 for l in labs}, "pieces": {}}
        for t in PIECES:
            row = docs[docs.txtid == t]
            if not len(row):
                continue
            x = normalize(vec.transform([tokens(row.iloc[0], "signs")]))
            s = scores(x, C)[0]
            o = np.argsort(-s)
            run["pieces"][t] = {"n_legible": int(row.n_legible.iloc[0]), "n_analysed": int(row.n_analysed.iloc[0]),
                                "top3": [(labs[i], round(float(s[i]), 4)) for i in o[:3]],
                                "gap": round(float(s[o[0]] - s[o[1]]), 4),
                                "placed": bool(s[o[0]] - s[o[1]] >= margin)}
        Xo = normalize(vec.transform([tokens(r, "signs") for _, r in orph.iterrows()]))
        p, _, _ = assign(scores(Xo, C), labs, margin)
        run["orphans"] = dict(zip(orph.txtid, p))
        out["runs"][name] = run
    e5 = pd.read_csv(f"{a.run}/E5_orphan_placement.csv").set_index("txtid").assigned
    for name, run in out["runs"].items():
        o = pd.Series(run.pop("orphans"))
        both = e5.dropna().index.intersection(o.dropna().index)
        run["orphans_vs_main"] = {"main_placed": int(e5.notna().sum()), "placed_here": int(o.notna().sum()),
                                  "placed_in_both": int(len(both)),
                                  "same_tradition": int((e5[both] == o[both]).sum()),
                                  "to_puriyanni_kuwattalla": int((o == "Luwian rituals (Puriyanni, Kuwattalla)").sum()),
                                  "to_arzawa": int((o == "Arzawa / western rituals").sum())}
    fn = f"{a.run}/R1_spellings_only.json"
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
