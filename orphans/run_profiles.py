"""E7 Tradition profiles: what is cultural/religious content and what is scribal habit?

E7a  Which layer identifies a tradition? Leave-one-out nearest-centroid accuracy per
     layer (logograms, foreign-language words, Hittite lexicon, spelling choice, and the
     same words with spelling collapsed), and a 10-fold LDA on seven orthographic indices.
     spelling > collapsed means the spelling choice carries information beyond vocabulary.
E7b  Profiles: the most distinctive features of each tradition per layer (weighted log-odds
     with an informative Dirichlet prior, Monroe et al. 2008, on document frequencies),
     and each tradition's mean orthographic indices (z-scores).
E7d  Spelling contrasts: share of plene spellings of a few frequent verbs and adverbs
     per tradition (the same word, written differently).
E7c  Date check: do the orthographic indices separate Middle from New Script in CTH 701?
     If they do, part of the "scribal" profile may be date rather than tradition.

Usage: python run_profiles.py TOKENS.csv --labels701 CTH701.csv --out results/<run>
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from qtm.corpus import load
from qtm.features import vectorizer
from qtm.groups import GROUPSETS, RESIDUE, HISTORICAL, label_map, is_orphan
from qtm.layers import INDICES, has_plene, indices, layer_tokens, variable_words
from run_experiments import MIN_WORDS, loo_eval

CONTRAST_WORDS = ("memai", "peran", "ḫalzai", "akuanzi", "šer")
LAYERS = ("logograms", "foreign", "lexicon", "spelling", "collapsed")
RNG = np.random.default_rng(0)


def layer_matrix(docs, layer, variable):
    toks = [layer_tokens(d, layer, variable) for _, d in docs.iterrows()]
    vec = vectorizer()
    return vec, vec.fit_transform(toks), toks


def lda_eval(F, y, n_perm):
    model = make_pipeline(StandardScaler(), LinearDiscriminantAnalysis())
    cv = StratifiedKFold(10, shuffle=True, random_state=0)
    acc = float(np.mean(cross_val_predict(model, F, y, cv=cv) == y))
    null = np.array([np.mean(cross_val_predict(model, F, p, cv=cv) == p)
                     for p in (RNG.permutation(y) for _ in range(n_perm))])
    vc = pd.Series(y).value_counts(normalize=True)
    return {"acc": round(acc, 3), "majority": round(float(vc.iloc[0]), 3),
            "null_mean": round(float(null.mean()), 3),
            "p": round(float((1 + (null >= acc).sum()) / (1 + n_perm)), 4),
            "n": int(len(y)), "classes": int(len(vc))}


def log_odds(toks, y, top=15, alpha0=500.0):
    """Distinctive features per class vs all other classes (z of weighted log-odds), by document frequency."""
    df = pd.DataFrame([(lab, t) for ts, lab in zip(toks, y) for t in set(ts)], columns=["lab", "tok"])
    if df.empty:
        return pd.DataFrame()
    cnt = pd.crosstab(df.tok, df.lab)
    tot = cnt.sum(1)
    a = alpha0 * tot / tot.sum()
    A = a.sum()
    rows = []
    for lab in cnt.columns:
        yi, yj = cnt[lab], tot - cnt[lab]
        ni, nj = yi.sum(), yj.sum()
        d = np.log((yi + a) / (ni + A - yi - a)) - np.log((yj + a) / (nj + A - yj - a))
        z = d / np.sqrt(1 / (yi + a) + 1 / (yj + a))
        for tok in z.sort_values(ascending=False).index[:top]:
            rows.append({"tradition": lab, "feature": tok, "z": round(float(z[tok]), 2),
                         "texts_with": int(yi[tok]), "texts_in_tradition": int((np.array(y) == lab).sum())})
    return pd.DataFrame(rows)


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
    y = ref.label.to_numpy()
    variable = variable_words(ref)
    report["corpus"] = {"texts": int(len(ref)), "variable_words": len(variable)}

    # E7a sparse layers
    toks_by_layer = {}
    report["E7a_layers"] = {}
    for layer in LAYERS:
        _, X, toks = layer_matrix(ref, layer, variable)
        toks_by_layer[layer] = toks
        has = np.asarray(X.getnnz(axis=1) > 0)
        r, _ = loo_eval(X[has], y[has], a.perm)
        r["texts_with_layer"] = int(has.sum())
        report["E7a_layers"][layer] = r
        print(layer, r["acc"], r["majority"], r["n"], flush=True)
    # E7a dense orthographic indices
    F = pd.DataFrame([indices(d) for _, d in ref.iterrows()])[INDICES]
    F.insert(0, "txtid", ref.txtid)
    F.insert(1, "tradition", y)
    F.to_csv(f"{a.out}/E7_indices_per_text.csv", index=False)
    Fx = F[INDICES].fillna(F[INDICES].median())
    report["E7a_layers"]["orthographic_indices"] = lda_eval(Fx.to_numpy(), y, a.perm)
    print("indices", report["E7a_layers"]["orthographic_indices"], flush=True)

    # E7b profiles
    prof = pd.concat([log_odds(toks_by_layer[l], y).assign(layer=l) for l in ("logograms", "foreign", "lexicon", "spelling")])
    prof.to_csv(f"{a.out}/E7_distinctive_features.csv", index=False)
    z = (Fx - Fx.mean()) / Fx.std()
    zt = z.groupby(y).mean().round(3)
    zt.to_csv(f"{a.out}/E7_index_profile.csv")
    report["E7b_index_profile_z"] = zt.to_dict(orient="index")

    # E7d spelling contrasts
    rows = [{"word": w, "tradition": lab, "plene": has_plene(sg)}
            for (_, d), lab in zip(ref.iterrows(), y) for w, sg in zip(d.words, d.signs) if w in CONTRAST_WORDS]
    con = pd.DataFrame(rows).groupby(["word", "tradition"]).plene.agg(["mean", "size"]).round(3)
    con.to_csv(f"{a.out}/E7_spelling_contrasts.csv")

    # E7c script date inside CTH 701
    if a.labels701:
        lab = pd.read_csv(a.labels701)
        key = lambda t: str(t).rstrip("+").strip()
        lab["key"] = lab.txtid.map(key)
        F701 = F.assign(key=F.txtid.map(key)).merge(lab[["key", "Zeit"]], on="key")
        F701 = F701[F701.Zeit.isin(["mh.", "jh."])]
        Fd = F701[INDICES].fillna(Fx.median())
        report["E7c_701_script_date"] = {
            "lda": lda_eval(Fd.to_numpy(), F701.Zeit.to_numpy(), a.perm),
            "means": F701.groupby("Zeit")[INDICES].mean().round(3).to_dict(orient="index")}

    with open(f"{a.out}/E7_report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(report, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
