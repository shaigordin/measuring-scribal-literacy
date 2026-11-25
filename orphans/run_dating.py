"""E12 Script date as a rival explanation of the traditions.

Hittite manuscripts are dated by their script: Old (OS), Middle (MS) and New (NS, including late
New Script). Spelling and the use of logograms change over time, and the traditions are not
copied evenly over time (the Hattian cult layer has most of the Old Script manuscripts, the
Huwassanna festivals many Middle Script ones). So a tradition could be recognised partly by its
date. These tests ask how much of the placement survives when date is held fixed.

E12a  Date mix: reference manuscripts per tradition and script period (Konkordanz date), and
      Cramer's V of the association.
E12b  Date alone: accuracy of guessing the tradition from the script period only (the most
      frequent tradition of each period), against the majority baseline.
E12c  Date-preserving shuffle: the main method's leave-one-out accuracy against a null that
      shuffles the tradition labels only among manuscripts of the same period. Whatever date
      explains, this null keeps; accuracy above it is tradition beyond date.
E12d  One period at a time: leave-one-out accuracy with reference and test drawn from New Script
      only, and from older script (OS and MS) only.
E12e  Across periods: centroids built from New Script manuscripts only place the older
      manuscripts, and the reverse. If a tradition were its date, this would fail.
E12f  Layers within New Script: the per-layer accuracies of E7a (Table "Each layer alone"),
      recomputed on New Script manuscripts only, and the seven orthographic rates: share of their
      variance explained by tradition and by period (eta squared), and their LDA (E7a) on New
      Script only.
E12g  Date inside a tradition: can the words tell Middle from New Script within the same
      tradition? Balanced accuracy (mean recall of MS and NS) against labels shuffled only within
      each tradition.

Dates come from the Konkordanz snapshot labels/konkordanz_meta.csv (accessed 2026-11-10), matched
on the publication number. "k.A." (no date given) and non-Hittite scripts count as unknown.

Usage: python run_dating.py TOKENS.csv --out results/<run> [--perm 200]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from qtm.assign import assign, centroids, loo_scores, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, is_orphan, label_map
from qtm.layers import INDICES, indices, variable_words
from run_experiments import MIN_WORDS, SEED, featurise
from run_profiles import LAYERS, layer_matrix, lda_eval

PERIOD = {"ah.": "OS", "ah.?": "OS", "mh.": "MS", "mh.?": "MS", "ah.?/mh.?": "MS", "jh.": "NS", "sjh.": "NS"}


def period_of(ref, meta):
    key = lambda t: str(t).rstrip("+").replace("(+)", "").strip()  # TLHdig marks joins with "+"
    date = meta.drop_duplicates("publication").set_index("publication").date
    return ref.txtid.map(key).map(date).map(PERIOD).fillna("unknown").to_numpy()


def loo_acc(X, y):
    return float(np.mean(assign(*loo_scores(X, y))[0] == y))


def loo_balanced(X, y):
    """Mean recall over classes (for two unequal classes, where plain accuracy favours the larger)."""
    hit = assign(*loo_scores(X, y))[0] == y
    return float(pd.Series(hit).groupby(y).mean().mean())


def shuffled_within(y, strata, rng):
    p = y.copy()
    for s in np.unique(strata):
        i = np.flatnonzero(strata == s)
        p[i] = rng.permutation(y[i])
    return p


def perm_test(X, y, strata, n_perm):
    """LOO accuracy against a free shuffle and a shuffle within strata."""
    rng = np.random.default_rng(SEED)
    acc = loo_acc(X, y)
    out = {"acc": round(acc, 3), "n": int(len(y))}
    for name, draw in (("free", lambda: rng.permutation(y)),
                       ("within_period", lambda: shuffled_within(y, strata, rng))):
        null = np.array([loo_acc(X, draw()) for _ in range(n_perm)])
        out[f"null_{name}_mean"] = round(float(null.mean()), 3)
        out[f"null_{name}_max"] = round(float(null.max()), 3)
        out[f"p_{name}"] = round(float((1 + (null >= acc).sum()) / (1 + n_perm)), 4)
    return out


def transfer(train, test, space="both"):
    vec, X = featurise(train, space)
    C, labs = centroids(X, train.label.to_numpy())
    known = test[test.label.isin(labs)]
    pred = assign(scores(vec.transform([tokens(r, space) for _, r in known.iterrows()]), C), labs)[0]
    hit = pred == known.label.to_numpy()
    return {"acc": round(float(hit.mean()), 3), "n": int(len(known)),
            "by_tradition": pd.Series(hit).groupby(known.label.to_numpy()).agg(["mean", "size"])
            .round(3).to_dict(orient="index")}


def eta2(v, g):
    v = pd.Series(v, dtype=float)
    ok = v.notna().to_numpy()
    v, g = v[ok].to_numpy(), np.asarray(g)[ok]
    tot = ((v - v.mean()) ** 2).sum()
    between = sum(len(v[g == k]) * (v[g == k].mean() - v.mean()) ** 2 for k in np.unique(g))
    return round(float(between / tot), 3) if tot else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--meta", default="labels/konkordanz_meta.csv")
    ap.add_argument("--groups", choices=sorted(GROUPSETS), default="literature")
    ap.add_argument("--out", default="results/run")
    ap.add_argument("--perm", type=int, default=200)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    lm = label_map(GROUPSETS[a.groups])
    docs = load(a.tokens, cths=list(lm))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    ref = docs[docs.n_words >= MIN_WORDS].assign(label=lambda d: d.cth_number.map(lm)).reset_index(drop=True)
    ref["period"] = period_of(ref, pd.read_csv(a.meta))
    y, per = ref.label.to_numpy(), ref.period.to_numpy()
    rep = {"texts": int(len(ref))}

    # E12a
    ct = pd.crosstab(ref.label, ref.period)
    ct.to_csv(f"{a.out}/E12a_tradition_by_period.csv")
    dated = ct.drop(columns="unknown", errors="ignore")
    chi2, p, dof, _ = chi2_contingency(dated)
    rep["E12a"] = {"periods": ref.period.value_counts().to_dict(),
                   "dated_share": round(float((per != "unknown").mean()), 3),
                   "cramers_v": round(float(np.sqrt(chi2 / dated.values.sum() / (min(dated.shape) - 1))), 3),
                   "chi2_p": float(p),
                   "older_share_by_tradition": (dated[["OS", "MS"]].sum(axis=1) / dated.sum(axis=1)).round(3).to_dict()}

    # E12b: date alone (each period's most frequent tradition; on the dated manuscripts)
    d = ref[ref.period != "unknown"]
    guess = d.groupby("period").label.agg(lambda s: s.value_counts().index[0])
    rep["E12b"] = {"acc": round(float((d.period.map(guess) == d.label).mean()), 3),
                   "majority": round(float(d.label.value_counts(normalize=True).iloc[0]), 3),
                   "guess": guess.to_dict(), "n": int(len(d))}

    # E12c: main method, date-preserving shuffle (unknown date is its own stratum)
    _, X = featurise(ref, "both")
    rep["E12c"] = perm_test(X, y, per, a.perm)
    print("E12c", rep["E12c"], flush=True)

    # E12d: one period at a time (traditions with at least 5 manuscripts in that period)
    rep["E12d"] = {}
    older = np.isin(per, ["OS", "MS"])
    for name, sel in (("NS", per == "NS"), ("older", older), ("all_dated", per != "unknown")):
        sub = ref[sel]
        sub = sub[sub.label.map(sub.label.value_counts()) >= 5]
        _, Xs = featurise(sub, "both")
        same = loo_acc(X[sub.index], y[sub.index])         # these manuscripts, full reference
        rep["E12d"][name] = {"acc_within": round(loo_acc(Xs, sub.label.to_numpy()), 3),
                             "acc_full_reference": round(same, 3), "n": int(len(sub)),
                             "traditions": int(sub.label.nunique()),
                             "majority": round(float(sub.label.value_counts(normalize=True).iloc[0]), 3)}
    print("E12d", rep["E12d"], flush=True)

    # E12e: across periods
    ns, old = ref[per == "NS"], ref[older]
    rep["E12e"] = {"NS_to_older": transfer(ns, old), "older_to_NS": transfer(old, ns),
                   "older_full_reference_loo": round(float(np.mean(
                       assign(*loo_scores(X, y))[0][older] == y[older])), 3)}
    print("E12e", {k: (v["acc"], v["n"]) if isinstance(v, dict) else v for k, v in rep["E12e"].items()}, flush=True)

    # E12f: layers within New Script, and eta squared of the orthographic rates
    variable = variable_words(ref)
    rep["E12f"] = {"layers_NS": {}}
    nsel = per == "NS"
    for layer in LAYERS:
        _, XL, _ = layer_matrix(ref, layer, variable)
        has = np.asarray(XL.getnnz(axis=1) > 0)
        both = has & nsel
        rep["E12f"]["layers_NS"][layer] = {"acc_NS_only": round(loo_acc(XL[both], y[both]), 3),
                                           "acc_all": round(loo_acc(XL[has], y[has]), 3), "n_NS": int(both.sum())}
    F = pd.DataFrame([indices(r) for _, r in ref.iterrows()])[INDICES]
    dsel = per != "unknown"
    rep["E12f"]["orthographic_eta2"] = {
        ix: {"tradition": eta2(F[ix][dsel], y[dsel]), "period": eta2(F[ix][dsel], per[dsel]),
             "tradition_within_NS": eta2(F[ix][nsel], y[nsel]),
             # period after removing each tradition's mean: date effect inside the traditions
             "period_within_tradition": eta2((F[ix] - F[ix].groupby(y).transform("mean"))[dsel], per[dsel])}
        for ix in INDICES}
    Fx = F.fillna(F.median())
    rep["E12f"]["orthographic_lda"] = {"all": lda_eval(Fx.to_numpy(), y, a.perm),
                                       "NS_only": lda_eval(Fx[nsel].to_numpy(), y[nsel], a.perm)}
    print("E12f", json.dumps(rep["E12f"], ensure_ascii=False), flush=True)

    # E12g: Middle vs New Script inside the same traditions (shuffle within tradition)
    ms_ns = ref[np.isin(per, ["MS", "NS"])]
    keep = ms_ns.groupby("label").period.transform(lambda s: min((s == "MS").sum(), (s == "NS").sum()) >= 5)
    g = ms_ns[keep.astype(bool)]
    _, Xg = featurise(g, "both")
    rng = np.random.default_rng(SEED)
    yp, strata = g.period.to_numpy(), g.label.to_numpy()
    acc = loo_balanced(Xg, yp)
    null = np.array([loo_balanced(Xg, shuffled_within(yp, strata, rng)) for _ in range(a.perm)])
    rep["E12g"] = {"balanced_acc": round(acc, 3), "chance": 0.5, "n": int(len(g)), "traditions": int(g.label.nunique()),
                   "ms_share": round(float((yp == "MS").mean()), 3),
                   "null_within_tradition_mean": round(float(null.mean()), 3),
                   "p": round(float((1 + (null >= acc).sum()) / (1 + a.perm)), 4)}
    print("E12g", rep["E12g"], flush=True)

    with open(f"{a.out}/E12_report.json", "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False, default=str)


if __name__ == "__main__":
    main()
