"""E8 Word classes: which classes of words carry a tradition, and which carry scribal habit?

Follows the categories of StBoT 73 Table 4 (agent, deity, function word, Hurrian/foreign,
realia, verb) and the experiment announced in its section 5: remove one class of words at a
time and see how far the groups hold together. For each class, leave-one-out nearest-centroid
accuracy is measured (a) with that class alone and (b) with everything except that class,
in two spaces: word forms (what is written) and sign n-grams (how it is written).
Word classes come from TLHdig's morphological analyses (qtm/wordclass.py).

Usage: python run_wordclass.py TOKENS.csv --labels701 CTH701.csv --out results/<run>
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from qtm.corpus import load
from qtm.features import sign_ngrams, vectorizer
from qtm.groups import GROUPSETS, RESIDUE, HISTORICAL, label_map, is_orphan
from qtm.wordclass import CLASSES
from run_experiments import MIN_WORDS, loo_eval


def select(doc, keep):
    idx = [i for i, c in enumerate(doc["wclasses"]) if keep(c)]
    return [doc["words"][i] for i in idx], [doc["signs"][i] for i in idx]


GENRE = {g: ("ritual" if "rituals" in g else "festival") for gs in GROUPSETS.values() for g in gs}


def evaluate(docs, y, keep, n_perm):
    """Accuracy per space; for the historical groups also the share of errors that stay within
    the same genre (festival vs ritual), since a class could separate genres rather than traditions."""
    out = {}
    parts = [select(d, keep) for _, d in docs.iterrows()]
    for space in ("words", "signs"):
        toks = [w if space == "words" else sign_ngrams(s) for w, s in parts]
        X = vectorizer().fit_transform(toks)
        has = np.asarray(X.getnnz(axis=1) > 0)
        if len(set(y[has])) < 2:
            continue
        r, pred = loo_eval(X[has], y[has], n_perm)
        r.pop("recall_by_class")
        if set(y) <= set(GENRE):
            g_true, g_pred = [GENRE[t] for t in y[has]], [GENRE.get(p) for p in pred]
            r["genre_acc"] = round(float(np.mean([a == b for a, b in zip(g_true, g_pred)])), 3)
        r["texts_with_class"] = int(has.sum())
        out[space] = r
    return out


def run(docs, y, n_perm, name):
    res = {"all": evaluate(docs, y, lambda c: True, n_perm)}
    for cl in CLASSES:
        res[f"only_{cl}"] = evaluate(docs, y, lambda c, cl=cl: c == cl, n_perm)
        res[f"without_{cl}"] = evaluate(docs, y, lambda c, cl=cl: c != cl, n_perm)
        print(name, cl, {k: v["acc"] for k, v in res[f"only_{cl}"].items()},
              {k: v["acc"] for k, v in res[f"without_{cl}"].items()}, flush=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--labels701")
    ap.add_argument("--out", default="results/run")
    ap.add_argument("--groups", choices=sorted(GROUPSETS), default="historical",
                    help="reference traditions: StBoT 73 Table 3 + CTH-range controls, or literature-defined")
    ap.add_argument("--perm", type=int, default=100)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = {}

    hist = label_map(GROUPSETS[a.groups])
    docs = load(a.tokens, cths=list(hist))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    ref = docs[docs.n_words >= MIN_WORDS].assign(label=lambda d: d.cth_number.map(hist)).reset_index(drop=True)

    # class coverage per tradition: share of legible words in each class
    cov = pd.DataFrame([(lab, c) for lab, cs in zip(ref.label, ref.wclasses) for c in cs], columns=["tradition", "wclass"])
    share = pd.crosstab(cov.tradition, cov.wclass, normalize="index").round(3)
    share.to_csv(f"{a.out}/E8_class_shares.csv")
    report["class_shares"] = share.to_dict(orient="index")

    report["historical"] = run(ref, ref.label.to_numpy(), a.perm, "hist")

    if a.labels701:
        lab = pd.read_csv(a.labels701).rename(columns={"sub-category": "subgroup"})
        key = lambda t: str(t).rstrip("+").strip()
        lab["key"] = lab.txtid.map(key)
        d701 = ref[ref.cth_number == "701"].assign(key=lambda d: d.txtid.map(key)).merge(
            lab[["key", "subgroup"]], on="key")
        known = d701[d701.subgroup.astype(str) != "701"]
        known = known[known.subgroup.map(known.subgroup.value_counts()) >= 4].reset_index(drop=True)
        report["cth701_subgroups"] = run(known, known.subgroup.astype(str).to_numpy(), a.perm, "701")

    with open(f"{a.out}/E8_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
