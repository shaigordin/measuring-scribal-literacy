"""E9 Open-set test: does the method notice a fragment that belongs to no reference tradition?

The margin rule of E2 only asks whether a fragment is closer to one tradition than to the
runner-up. A myth or an oracle fragment can pass that rule and be placed in a ritual or
festival tradition it has nothing to do with. This experiment measures how often that happens,
using texts whose genre is known and lies outside the reference (Laroche's own genre blocks):

  myths 321-370, prayers and hymns 371-389, oracles 561-582, historical texts and treaties
  1-220, instructions 251-275, cult inventories 501-530 (Cammarosano 2021, StBoT 68: local-cult
  vocabulary close to festival texts), and two hard cases of the same genres with an unknown
  tradition: festivals of traditions not in the reference (591-720 minus the reference CTHs and
  the orphan pool CTH 670), and the Luwian rituals of Puriyanni, Kuwattalla and Šilalluḫi
  (758-763; Yakubovich and Mouton 2023, StBoT 72: a Lower Land tradition, not Kizzuwatna).

Protocol (5 folds over texts): centroids come from the reference texts outside the fold; every
held-out reference text and out-of-reference text yields `reps` random windows of k words.
For each k:
  - placed: share of windows that pass the E2 margin (wrongly placed, for outside texts);
  - AUROC: how well the top cosine similarity ("fit") separates reference from outside windows;
  - fit floor: the 5th percentile of the reference windows' fit; share of outside windows below it.
  - genre gate: the outside genres become classes of their own (centroids from the training
    folds); share of windows whose nearest class is an outside genre (for reference windows,
    the share wrongly sent away).
Then fit floor and gate are applied to the orphans (E5): an orphan whose nearest class, by the
E2 margin, is an outside genre is a candidate for something other than a ritual or festival.

Usage: python run_openset.py TOKENS.csv --report results/<run>/report.json --out results/<run>
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from qtm.assign import assign, centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, label_map, is_orphan
from run_experiments import MIN_WORDS, SEED, featurise

KS = (5, 10, 17, 40)
FIT_QUANTILE = 0.05


def outside_genres(reference_cths):
    ref = {int(c) for c in reference_cths}
    festivals = [c for c in range(591, 721) if c not in ref and c != 670]
    return {"Myths": list(range(321, 371)),
            "Prayers and hymns": list(range(371, 390)),
            "Oracles": list(range(561, 583)),
            "Historical texts, treaties": list(range(1, 221)),
            "Instructions": list(range(251, 276)),
            "Cult inventories": list(range(501, 531)),
            "Festivals of other traditions": festivals,
            "Luwian rituals (Puriyanni, Kuwattalla)": list(range(758, 764))}


def windows(doc, k, reps, rng):
    out = []
    for _ in range(reps):
        s = rng.integers(0, doc.n_words - k + 1)
        out.append(tokens({"words": doc.words[s:s + k], "signs": doc.signs[s:s + k]}, "both"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--report", required=True, help="report.json of run_experiments.py (margin, groups)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--max-texts", type=int, default=300, help="per outside genre")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = json.load(open(a.report))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    outside = outside_genres(hist)
    out_map = label_map(outside)
    rng = np.random.default_rng(SEED)

    docs = load(a.tokens, cths=list(hist) + list(out_map))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    docs = docs[docs.n_words >= MIN_WORDS].reset_index(drop=True)
    ref = docs[docs.cth_number.isin(hist)].assign(label=lambda d: d.cth_number.map(hist), kind="reference")
    oth = docs[docs.cth_number.isin(out_map)].assign(label=lambda d: d.cth_number.map(out_map), kind="outside")
    oth = oth.sample(frac=1, random_state=0).groupby("label").head(a.max_texts)

    folds = StratifiedKFold(5, shuffle=True, random_state=0)
    ref = ref.reset_index(drop=True)
    ref["fold"] = -1
    for f, (_, te) in enumerate(folds.split(ref, ref.label)):
        ref.loc[te, "fold"] = f
    oth = oth.reset_index(drop=True).assign(fold=lambda d: rng.integers(0, 5, len(d)))

    rows = []
    for f in range(5):
        train = ref[ref.fold != f]
        vec, X = featurise(train, "both")
        C, labs = centroids(X, train.label.to_numpy())
        gtrain = pd.concat([train, oth[oth.fold != f]])
        gvec, GX = featurise(gtrain, "both")
        GC, glabs = centroids(GX, gtrain.label.to_numpy())
        test = pd.concat([ref[ref.fold == f], oth[oth.fold == f]])
        for k in KS:
            for _, d in test[test.n_words >= k].iterrows():
                win = windows(d, k, a.reps, rng)
                pred, top, gap = assign(scores(vec.transform(win), C), labs, margin=margin)
                gpred, _, _ = assign(scores(gvec.transform(win), GC), glabs)
                for p, t, g in zip(pred, top, gpred):
                    rows.append({"k": k, "kind": d.kind, "group": d.label, "cth": d.cth_number,
                                 "placed": p is not None, "correct": p == d.label, "fit": t,
                                 "gate_outside": g in outside, "gate_correct": g == d.label})
    W = pd.DataFrame(rows)
    W.to_csv(f"{a.out}/E9_windows.csv.gz", index=False)

    report = {"margin": margin, "fit_quantile": FIT_QUANTILE, "reps": a.reps,
              "texts": {"reference": int(len(ref)), **oth.label.value_counts().to_dict()}, "by_k": {}}
    floors = {}
    for k in KS:
        wk = W[W.k == k]
        r = wk[wk.kind == "reference"]
        floor = float(r.fit.quantile(FIT_QUANTILE))
        floors[k] = floor
        e = {"fit_floor": round(floor, 4),
             "reference": {"placed": round(float(r.placed.mean()), 3),
                           "correct_if_placed": round(float(r[r.placed].correct.mean()), 3),
                           "below_floor": round(float((r.fit < floor).mean()), 3),
                           "gate_sent_outside": round(float(r.gate_outside.mean()), 3)}}
        for g, o in wk[wk.kind == "outside"].groupby("group"):
            y = np.r_[np.zeros(len(r)), np.ones(len(o))]
            e[g] = {"placed": round(float(o.placed.mean()), 3),
                    "auroc": round(float(roc_auc_score(y, -np.r_[r.fit, o.fit])), 3),
                    "below_floor": round(float((o.fit < floor).mean()), 3),
                    "placed_and_above_floor": round(float((o.placed & (o.fit >= floor)).mean()), 3),
                    "gate_sent_outside": round(float(o.gate_outside.mean()), 3),
                    "gate_right_genre": round(float(o.gate_correct.mean()), 3)}
        report["by_k"][str(k)] = e

    # the fit floor applied to the orphans; what the low-fit orphans look like instead
    run = os.path.dirname(a.report)
    orph = pd.read_csv(f"{run}/E5_orphan_placement.csv")
    kk = np.array(KS)
    orph["fit_floor"] = [floors[int(kk[kk <= n].max())] for n in orph.n_words]
    orph["below_floor"] = orph.top_sim < orph.fit_floor
    vec, X = featurise(pd.concat([ref, oth]), "both")
    C, labs = centroids(X, pd.concat([ref, oth]).label.to_numpy())
    od = load(a.tokens, cths=[str(c) for c in sorted({*orph.filed_under.astype(str)})])
    od = od[od.txtid.isin(orph.txtid)].set_index("txtid").loc[orph.txtid]
    S = scores(vec.transform([tokens(r, "both") for _, r in od.iterrows()]), C)
    gpred, _, ggap = assign(S, labs)
    orph["nearest_genre_or_tradition"], orph["genre_gap"] = gpred, ggap.round(4)
    orph["nearest_is_outside"] = orph.nearest_genre_or_tradition.isin(list(outside)) & (orph.genre_gap >= margin)
    orph.drop(columns=[c for c in orph.columns if c in set(hist.values())]).to_csv(
        f"{a.out}/E9_orphan_fit.csv", index=False)
    low = orph[orph.below_floor]
    report["orphans"] = {
        "scored": int(len(orph)), "below_fit_floor": int(len(low)),
        "assigned_but_below_floor": int(low.assigned.notna().sum()),
        "below_floor_nearest_outside_genre": low[low.nearest_is_outside].nearest_genre_or_tradition.value_counts().to_dict(),
        "outside_by_margin": orph[orph.nearest_is_outside].nearest_genre_or_tradition.value_counts().to_dict(),
        "assigned_but_outside_by_margin": int((orph.assigned.notna() & orph.nearest_is_outside).sum()),
        "assigned_but_outside_by_tradition": orph[orph.assigned.notna() & orph.nearest_is_outside]
        .groupby("assigned").nearest_genre_or_tradition.value_counts().unstack(fill_value=0).to_dict(orient="index")}
    with open(f"{a.out}/E9_report.json", "w") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
