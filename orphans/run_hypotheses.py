"""E10 The method against scholarly attributions.

E10a Leave one composition out. Every reference composition (one CTH number) is removed from the
     reference in turn, with all its manuscripts, and placed against the traditions built from
     the rest. Unlike leave-one-manuscript-out (E1), duplicates and other copies of the same
     composition cannot help, so this asks whether the method recovers the grouping that the
     defining studies argued for, composition by composition.
E10b Contested attributions. For a set of texts that scholarship attributes to a tradition
     (default: the Ambazzi rituals, CTH 391, 429, 463, sometimes grouped with the western /
     Arzawa rituals), the pooled texts are scored against every tradition. The statistic is the
     lead of the claimed tradition over the best other one; its null distribution comes from
     random sets of the same number of ritual texts that no study assigns (CTH 390-469 residue).
     The same is done for every tradition, so the table says which tradition the texts DO fit.
E10c The words behind it. Each tradition's most distinctive words (weighted log-odds, E7b) and
     how many of them the contested texts attest; and the contested texts' own most distinctive
     words, with the share of manuscripts of each tradition that attest them.

Usage: python run_hypotheses.py TOKENS.csv --out results/<run> [--cths 391 429 463 --claim TRADITION]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, RESIDUE, label_map, is_orphan
from run_experiments import MIN_WORDS, SEED, featurise
from run_profiles import log_odds

AMBAZZI = ["391", "429", "463"]
CLAIM = "Arzawa / western rituals"


def loco(ref):
    """Leave one composition (CTH) out: text-level and composition-level placement."""
    rows = []
    for cth, held in ref.groupby("cth_number"):
        train = ref[ref.cth_number != cth]
        lab = held.label.iloc[0]
        if lab not in set(train.label):
            continue  # the tradition has no other composition: untestable
        vec, X = featurise(train, "both")
        C, labs = centroids(X, train.label.to_numpy())
        Xh = vec.transform([tokens(r, "both") for _, r in held.iterrows()])
        pred, _, _ = assign(scores(Xh, C), labs)
        pooled, _, gap = assign(scores(normalize(np.asarray(Xh.sum(0))), C), labs)
        rows.append({"cth": cth, "tradition": lab, "texts": len(held),
                     "texts_correct": int((pred == lab).sum()), "composition_pred": pooled[0],
                     "composition_correct": pooled[0] == lab, "gap": round(float(gap[0]), 4)})
    return pd.DataFrame(rows)


def contested(ref, test, pool, n_null, rng):
    """Lead of each tradition over the best other for the pooled test texts, against random pool sets."""
    vec, X = featurise(ref, "both")
    C, labs = centroids(X, ref.label.to_numpy())
    vt = lambda d: vec.transform([tokens(r, "both") for _, r in d.iterrows()])
    Xt, Xp = vt(test), vt(pool)

    def lead(Xs):
        s = scores(normalize(np.asarray(Xs.sum(0))), C)[0]
        return np.array([s[j] - np.max(np.delete(s, j)) for j in range(len(labs))]), s

    obs, sim = lead(Xt)
    k = Xt.shape[0]
    null = np.array([lead(Xp[rng.choice(Xp.shape[0], k, replace=False)])[0] for _ in range(n_null)])
    per_text = pd.DataFrame(scores(Xt, C).round(4), columns=labs, index=test.txtid)
    per_text["nearest"] = assign(scores(Xt, C), labs)[0]
    tab = pd.DataFrame({"tradition": labs, "similarity": sim.round(4), "lead_over_best_other": obs.round(4),
                        "null_mean": null.mean(0).round(4),
                        "null_q05": np.quantile(null, 0.05, axis=0).round(4),
                        "null_q95": np.quantile(null, 0.95, axis=0).round(4),
                        "p_fits_better_than_random_rituals": ((1 + (null >= obs).sum(0)) / (1 + n_null)).round(4)})
    return tab.sort_values("similarity", ascending=False), per_text


def word_evidence(ref, test, pool, top=20):
    toks = lambda d: [tokens(r, "words") for _, r in d.iterrows()]
    sig = log_odds(toks(ref), ref.label.to_numpy(), top=top)
    have = {w for ts in toks(test) for w in ts}
    sig["in_contested_texts"] = [sum(w in set(ts) for ts in toks(test)) for w in sig.feature]
    cover = sig.assign(hit=sig.in_contested_texts > 0).groupby("tradition").hit.mean().round(3)
    # the contested texts' own distinctive words, against the ritual pool, and where else they occur
    both = pd.concat([test.assign(label="contested"), pool.assign(label="pool")])
    own = log_odds(toks(both), both.label.to_numpy(), top=top)
    own = own[own.tradition == "contested"].copy()
    df = {lab: pd.Series([w for ts in toks(g) for w in set(ts)]).value_counts() / len(g)
          for lab, g in ref.groupby("label")}
    for lab, s in df.items():
        own[lab] = [round(float(s.get(w, 0.0)), 3) for w in own.feature]
    return sig, cover, own, len(have)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--out", required=True)
    ap.add_argument("--groups", choices=sorted(GROUPSETS), default="literature")
    ap.add_argument("--cths", nargs="+", default=AMBAZZI)
    ap.add_argument("--claim", default=CLAIM)
    ap.add_argument("--null", type=int, default=2000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(SEED)
    hist = label_map(GROUPSETS[a.groups])
    res = {str(c) for c in RESIDUE["CTH 390–469 residue"]}
    docs = load(a.tokens, cths=list(hist) + sorted(res))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    docs = docs[docs.n_words >= MIN_WORDS].reset_index(drop=True)
    ref = docs[docs.cth_number.isin(hist)].assign(label=lambda d: d.cth_number.map(hist))
    test = docs[docs.cth_number.isin(a.cths)]
    pool = docs[docs.cth_number.isin(res) & ~docs.cth_number.isin(a.cths)]

    report = {"contested": {"cths": a.cths, "claim": a.claim, "texts": int(len(test)), "pool_texts": int(len(pool))}}
    lo = loco(ref)
    lo.to_csv(f"{a.out}/E10a_leave_composition_out.csv", index=False)
    w = lo.texts
    report["E10a"] = {
        "compositions": int(len(lo)), "compositions_correct": int(lo.composition_correct.sum()),
        "texts": int(w.sum()), "texts_correct": int(lo.texts_correct.sum()),
        "by_tradition": lo.groupby("tradition").agg(compositions=("cth", "size"),
                                                    correct=("composition_correct", "sum"),
                                                    texts=("texts", "sum"), texts_correct=("texts_correct", "sum"))
        .astype(int).to_dict(orient="index"),
        "untestable": sorted(set(ref.label) - set(lo.tradition))}

    tab, per_text = contested(ref, test, pool, a.null, rng)
    tab.to_csv(f"{a.out}/E10b_contested_fit.csv", index=False)
    per_text.to_csv(f"{a.out}/E10b_contested_per_text.csv")
    report["E10b"] = {"table": tab.to_dict(orient="records"),
                      "per_text_nearest": per_text.nearest.value_counts().to_dict()}

    sig, cover, own, nvocab = word_evidence(ref, test, pool)
    sig.to_csv(f"{a.out}/E10c_signatures_in_contested.csv", index=False)
    own.to_csv(f"{a.out}/E10c_contested_own_words.csv", index=False)
    report["E10c"] = {"signature_coverage": cover.to_dict(), "contested_vocabulary": nvocab}

    with open(f"{a.out}/E10_report.json", "w") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(report, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
