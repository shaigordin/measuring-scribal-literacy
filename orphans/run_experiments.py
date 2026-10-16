"""Orphans and Archetypes: experiments for the Mainz Hittite & AI workshop.

E1  Reference space: leave-one-text-out nearest-centroid assignment of traditions
    (word tf-idf / sign n-grams / both) against majority and permutation baselines.
    Run for (a) the historical groups of StBoT 73 Table 3 + ritual controls and
    (b) CTH 670 / 701 / 832 as named in the abstract.
E2  Coverage curve: accuracy when held-out texts are cut to k-word windows,
    i.e. how small an orphan can be and still be placed. Sets the abstention rule.
E3  CTH 701 internal validation on the Salvini-Wegner subgroups (a-f), with
    script date (MS/NS) as a competing explanation.
E4  Ablations: drop logograms; drop Hurrian-language words.
E5  Orphan placement: CTH 470 + EBo fragments scored against every tradition.
E6  QTM coverage: how much of each tradition's characteristic vocabulary the
    orphans assigned to it attest (orphans as low-coverage witnesses).

Usage: python run_experiments.py TOKENS.csv --labels701 CTH701.csv --out results/<run>
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

from qtm.corpus import load
from qtm.features import tokens, vectorizer
from qtm.assign import centroids, scores, loo_scores, assign
from qtm.groups import GROUPSETS, RESIDUE, HISTORICAL, ABSTRACT, label_map, is_orphan

MIN_WORDS = 17          # as in Gordin, Yavasan & Romach 2025
SEED = 0  # every experiment draws from its own generator seeded with SEED, so results do not
          # depend on which experiments ran before it
SPACES = ("words", "signs", "both")


def featurise(docs, space, **kw):
    vec = vectorizer()
    X = vec.fit_transform([tokens(d, space, **kw) for _, d in docs.iterrows()])
    return vec, X


def loo_eval(X, y, n_perm):
    rng = np.random.default_rng(SEED)
    S, labs = loo_scores(X, y)
    pred, _, _ = assign(S, labs)
    acc = float(np.mean(pred == y))
    null = np.array([np.mean(assign(*loo_scores(X, p))[0] == p)
                     for p in (rng.permutation(y) for _ in range(n_perm))])
    vc = pd.Series(y).value_counts(normalize=True)
    per_class = pd.Series(pred == y).groupby(y).mean().round(3).to_dict()
    return {"acc": round(acc, 3), "majority": round(float(vc.iloc[0]), 3),
            "null_mean": round(float(null.mean()), 3),
            "p": round(float((1 + (null >= acc).sum()) / (1 + n_perm)), 4),
            "n": int(len(y)), "classes": int(len(vc)), "recall_by_class": per_class}, pred


def coverage_curve(docs, y, space, ks=(3, 5, 8, 10, 17, 25, 40), reps=10, max_texts=40):
    """Accuracy and top-vs-runner-up gap when held-out texts are cut to k-word windows.

    Only texts with at least max(ks) words are used, so every k is measured on the
    same texts (no survivorship bias). At most `max_texts` per class keep classes balanced.
    """
    rng = np.random.default_rng(SEED)
    long_ = docs[docs.n_words >= max(ks)]
    long_ = long_.groupby(y[long_.index], group_keys=False).apply(
        lambda g: g.sample(min(len(g), max_texts), random_state=0))
    rows = []
    for i, d in long_.iterrows():
        train = docs.drop(index=i)
        vec, X = featurise(train, space)
        C, labs = centroids(X, y[train.index].to_numpy())
        for k in ks:
            frags = []
            for _ in range(reps):
                s = rng.integers(0, d.n_words - k + 1)
                frags.append(tokens({"words": d.words[s:s + k], "signs": d.signs[s:s + k]}, space))
            pred, top, gap = assign(scores(vec.transform(frags), C), labs)
            for p, g in zip(pred, gap):
                rows.append({"k": k, "space": space, "true": y[i], "hit": p == y[i], "gap": g})
    return pd.DataFrame(rows)


def calibrate_margin(curve, target=0.8):
    """Smallest gap (to 0.001) at which fragments of any size reach the target accuracy."""
    for m in np.arange(0, 0.5, 0.001):
        sel = curve[curve.gap >= m]
        if len(sel) > 50 and sel.hit.mean() >= target:
            return float(m), float(sel.hit.mean()), float(len(sel) / len(curve))
    return None, None, None


def archetype_coverage(X_ref, y_ref, X_orph, assigned, vocab, top=200):
    """Share of each tradition's top-weighted centroid terms attested in its assigned orphans."""
    C, labs = centroids(X_ref, y_ref)
    out = []
    for j, lab in enumerate(labs):
        core = np.argsort(-C[j])[:top]
        mine = X_orph[np.asarray(assigned == lab)]
        seen = (np.asarray((mine[:, core] > 0).sum(0)).ravel() > 0) if mine.shape[0] else np.zeros(top, bool)
        out.append({"tradition": lab, "orphans": int(mine.shape[0]),
                    "core_terms": top, "core_attested": int(seen.sum()),
                    "coverage": round(float(seen.mean()), 3),
                    "unattested_examples": [vocab[c] for c in core[~seen][:10]]})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--labels701")
    ap.add_argument("--out", default="results/run")
    ap.add_argument("--groups", choices=sorted(GROUPSETS), default="historical",
                    help="reference traditions: StBoT 73 Table 3 + CTH-range controls, or literature-defined")
    ap.add_argument("--perm", type=int, default=200)
    ap.add_argument("--orphan-min-words", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = {"groups": a.groups}

    allcths = sorted({str(c) for g in (HISTORICAL, ABSTRACT, GROUPSETS[a.groups], RESIDUE) for cs in g.values() for c in cs} | {"470"})
    docs = load(a.tokens, cths=allcths)
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & (docs.n_words >= MIN_WORDS)].copy()
    orph = docs[docs.orphan & (docs.n_words >= a.orphan_min_words)].copy()
    report["corpus"] = {"reference_texts": int(len(ref)), "orphans_used": int(len(orph)),
                        "orphans_total": int(docs.orphan.sum()),
                        "orphan_words_median": float(docs[docs.orphan].n_words.median())}

    hist = label_map(GROUPSETS[a.groups])
    abst = label_map(ABSTRACT)
    setups = {"historical": ref[ref.cth_number.isin(hist)].assign(label=lambda d: d.cth_number.map(hist)),
              "abstract_670_701_832": ref[ref.cth_number.isin(abst)].assign(label=lambda d: d.cth_number.map(abst))}
    for name, sub in setups.items():
        sub.groupby("label").n_words.describe().round(1).to_csv(f"{a.out}/stats_{name}.csv")

    # E1 + E4
    for name, sub in setups.items():
        y = sub.label.to_numpy()
        report[f"E1_{name}"] = {sp: loo_eval(featurise(sub, sp)[1], y, a.perm)[0] for sp in SPACES}
        report[f"E4_{name}_no_logograms"] = {
            sp: loo_eval(featurise(sub, sp, drop_logograms=True)[1], y, a.perm)[0] for sp in ("words", "signs")}

    # E3: CTH 701 subgroups, and script date as a rival explanation
    if a.labels701:
        lab = pd.read_csv(a.labels701)
        lab = lab.rename(columns={"sub-category": "subgroup"})[["txtid", "subgroup", "Zeit"]]
        key = lambda t: str(t).rstrip("+").strip()  # TLHdig marks joins with a trailing "+"
        lab["key"] = lab.txtid.map(key)
        d701 = ref[ref.cth_number == "701"].assign(key=lambda d: d.txtid.map(key)).merge(
            lab.drop(columns="txtid"), on="key", how="inner")
        known = d701[d701.subgroup.astype(str) != "701"]
        known = known[known.subgroup.map(known.subgroup.value_counts()) >= 4]
        report["E3_cth701_subgroups"] = {sp: loo_eval(featurise(known, sp)[1], known.subgroup.to_numpy(), a.perm)[0]
                                         for sp in SPACES}
        dated = d701[d701.Zeit.isin(["mh.", "jh."])]
        report["E3_cth701_script_date"] = {sp: loo_eval(featurise(dated, sp)[1], dated.Zeit.to_numpy(), a.perm)[0]
                                           for sp in SPACES}
        # where do unclassified 701 and group f texts fall among the defined groups a-e?
        defined = known[known.subgroup != "f"]
        vec, X = featurise(defined, "both")
        C, labs = centroids(X, defined.subgroup.to_numpy())
        unk = d701[d701.subgroup.astype(str).isin(["701", "f"])]
        S = scores(vec.transform([tokens(r, "both") for _, r in unk.iterrows()]), C)
        p, top, gap = assign(S, labs)
        pd.DataFrame({"txtid": unk.txtid, "label": unk.subgroup, "script": unk.Zeit, "n_words": unk.n_words,
                      "nearest": p, "sim": top.round(3), "gap": gap.round(3)}
                     ).to_csv(f"{a.out}/E3_701_unclassified_nearest.csv", index=False)

    # E2: coverage curve on the historical setup
    hsub = setups["historical"]
    y_h = hsub.label
    curve = pd.concat([coverage_curve(hsub, y_h, sp) for sp in SPACES])
    curve.to_csv(f"{a.out}/E2_coverage_raw.csv", index=False)
    summ = curve.groupby(["space", "k"]).agg(acc=("hit", "mean"), gap_median=("gap", "median"), n=("hit", "size"))
    summ.round(3).to_csv(f"{a.out}/E2_coverage_curve.csv")
    cb = curve[curve.space == "both"].reset_index(drop=True)
    margin, prec, kept = calibrate_margin(cb)
    # sampling uncertainty of the margin: bootstrap over the coverage-curve fragments
    boot = [calibrate_margin(cb.sample(len(cb), replace=True, random_state=s))[0] for s in range(200)]
    lo, hi = (float(q) for q in np.nanpercentile(np.array(boot, dtype=float), [5, 95]))
    report["E2_abstention"] = {"margin": margin, "precision_above_margin": prec, "share_assigned": kept,
                               "margin_90ci": [round(lo, 3), round(hi, 3)]}

    # E5 + E6: orphans
    vec, X = featurise(hsub, "both")
    C, labs = centroids(X, y_h.to_numpy())
    Xo = vec.transform([tokens(r, "both") for _, r in orph.iterrows()])
    S = scores(Xo, C)
    pred, top, gap = assign(S, labs, margin=margin or 0.0)
    out = pd.DataFrame(S.round(4), columns=labs)
    out.insert(0, "txtid", orph.txtid.values)
    out.insert(1, "filed_under", orph.cth_number.values)
    out.insert(2, "n_words", orph.n_words.values)
    out["assigned"], out["top_sim"], out["gap"] = pred, top.round(4), gap.round(4)
    out.sort_values("gap", ascending=False).to_csv(f"{a.out}/E5_orphan_placement.csv", index=False)
    report["E5_orphans"] = {
        "assigned": int(pd.notna(pred).sum()), "abstained": int(pd.isna(pred).sum()),
        "by_tradition": pd.Series(pred).value_counts().to_dict(),
        "by_filing": pd.crosstab(out.filed_under, out.assigned.fillna("(abstain)")).to_dict()}
    # sensitivity of the orphan counts to the margin's sampling uncertainty
    report["E5_orphans"]["assigned_at_margin_90ci"] = {
        str(round(m, 3)): pd.Series(assign(S, labs, margin=m)[0]).value_counts().to_dict() for m in (lo, hi)}
    # E5b: the CTH 390-469 texts no study claims are placed like orphans (literature groups only)
    if a.groups == "literature":
        res_c = {str(c) for cs in RESIDUE.values() for c in cs}
        resd = docs[~docs.orphan & docs.cth_number.isin(res_c) & (docs.n_words >= MIN_WORDS)]
        Sr = scores(vec.transform([tokens(r, "both") for _, r in resd.iterrows()]), C)
        pr, tr, gr = assign(Sr, labs, margin=margin or 0.0)
        pd.DataFrame({"txtid": resd.txtid.values, "cth": resd.cth_number.values, "n_words": resd.n_words.values,
                      "assigned": pr, "top_sim": tr.round(4), "gap": gr.round(4)}
                     ).sort_values("gap", ascending=False).to_csv(f"{a.out}/E5b_residue_placement.csv", index=False)
        report["E5b_residue"] = {"texts": int(len(resd)), "assigned": int(pd.notna(pr).sum()),
                                 "by_tradition": pd.Series(pr).value_counts().to_dict()}
    vocab = vec.get_feature_names_out()
    report["E6_archetype_coverage"] = archetype_coverage(X, y_h.to_numpy(), Xo, pred, vocab)

    with open(f"{a.out}/report.json", "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(report, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
