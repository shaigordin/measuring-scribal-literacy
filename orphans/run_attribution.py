"""E11 What a decision rests on: word classes, frequent words, and writing.

The assignment score is a cosine, so the decision between the nearest tradition and the
runner-up splits exactly over the features:

    margin = cos(x, c_top) - cos(x, c_2) = sum_f x_f * (c_top,f - c_2,f)

where x is the fragment's tf-idf vector and c the (unit) centroids. Each feature's term is its
contribution. A feature is a word form (vocabulary) or a sign n-gram within a word (writing:
spelling, logograms, determinatives); every occurrence belongs to a word with a word class
(qtm/wordclass.py, the StBoT 73 Table 4 categories), so each contribution is split over the
word classes of the words it occurs in, in proportion to its occurrences in that text. This
gives, for every text, an exact decomposition of its margin into
    layer (word form / syllabic spelling / logographic writing) x word category
(qtm.wordclass.LAYERS, CATEGORIES; the same grouping as the workshop playground).

The margin is not the similarity. The playground's category shares divide a text's cosine to its
own tradition; that similarity is dominated by what all traditions share (nu, the sign a), which
cancels in the margin. E11a reports both, so the two can be compared.

E11a Reference texts (leave-one-out: the text is removed from its own centroid, as in E1),
     summed per tradition over the correctly placed texts: which categories and layers carry the
     decision for each tradition. Orphans (E5) are decomposed against the full centroids.
E11b Frequent words and common features. The share of the margin carried by occurrences of the
     25 most frequent word forms (by number of reference texts that attest them: nu, tai, anta
     ...; their word form and their signs), the share carried by common features (attested in at
     least a quarter of the reference texts, e.g. the single signs nu, a, i), for reference
     texts and orphans by length, and the single features that contribute most per tradition.
E11c Removing the frequent words. Leave-one-out accuracy when the k most frequent word forms
     are deleted from every text (word and signs), k = 0, 10, 25, 50, 100, 200.

E11d Does it matter? Short windows (5, 10, 20 words) of reference texts, placed as in E2 with
     the E2 margin: precision of the placed windows whose margin rests mostly (> 50%) on common
     features or on frequent words, against the rest.

E11e Orphans without function words / without the 25 most frequent words: the reference is
     refitted without them and the orphans placed again with the E2 margin; how many keep their
     tradition, move, or drop out. E11a_by_tradition.csv collects the per-tradition shares.

Usage: python run_attribution.py TOKENS.csv --report results/<run>/report.json --out results/<run>
"""
import argparse
import json
import os
from collections import Counter, defaultdict

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, class_sums, loo_scores, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import ABSTRACT, GROUPSETS, HISTORICAL, RESIDUE, label_map, is_orphan
from qtm.wordclass import CATEGORIES, LAYERS, category, layer
from run_experiments import MIN_WORDS, SEED, featurise

FREQ_TOP = 25
KS = (0, 10, 25, 50, 100, 200)
TOP_FEATURES = 12
COMMON = 0.25
WINDOW_KS = (5, 10, 20)


def occurrences(doc, frequent):
    """feature -> Counter of (word class, word is frequent) over the words it occurs in
    (the same tokens as qtm.features)."""
    occ = defaultdict(Counter)
    for w, sg, c in zip(doc["words"], doc["signs"], doc["wclasses"]):
        key = (category(c), w in frequent)
        occ[w][key] += 1
        for t in tokens({"words": [], "signs": [sg]}, "both"):
            occ[t][key] += 1
    return occ


def decompose(x, d, occ, names, common):
    """Split the margin x.d over (layer, category); also the part carried by occurrences in frequent
    words, the part carried by common features, and the per-feature contributions."""
    cells, feats, freq, comm = Counter(), {}, 0.0, 0.0
    for j, v in zip(x.indices, x.data):
        f, val = names[j], v * d[j]
        if val == 0:
            continue
        feats[f] = val
        comm += val * common[j]
        cnt = occ[f]
        tot = sum(cnt.values())
        for (c, fr), n in cnt.items():
            cells[(layer(f), c)] += val * n / tot
            freq += val * n / tot * fr
    return cells, feats, freq, comm


def table(rows, extra):
    df = pd.DataFrame([{**e, **{f"{a}|{c}": v for (a, c), v in cells.items()}} for e, cells in zip(extra, rows)])
    return df.fillna(0.0)


def check(df):
    cols = [c for c in df.columns if "|" in c]
    assert np.allclose(df[cols].sum(1), df.margin, atol=1e-9), "decomposition does not sum to the margin"


def shares(df, by):
    """Ratio of sums: each cell's summed contribution over the summed margin of the group."""
    cols = [c for c in df.columns if "|" in c]
    g = df.groupby(by)[cols + ["margin"]].sum()
    out = {}
    for key, r in g.iterrows():
        cell = (r[cols] / r.margin)
        per_layer = {a: round(float(cell[[c for c in cols if c.startswith(a + "|")]].sum()), 3) for a in LAYERS}
        per_cat = {k: round(float(cell[[c for c in cols if c.endswith("|" + k)]].sum()), 3) for k in CATEGORIES}
        out[key] = {"texts": int((df[by] == key).sum()), "by_layer": per_layer, "by_category": per_cat,
                    "cells": {c: round(float(v), 4) for c, v in cell.items() if abs(v) >= 0.005}}
    return out


def common_mask(X):
    """Features attested in at least COMMON of the reference texts (e.g. the sign nu, the word nu)."""
    return np.asarray((X > 0).mean(0)).ravel() >= COMMON


def run_loo(ref, frequent):
    vec, X = featurise(ref, "both")
    names = vec.get_feature_names_out()
    common = common_mask(X)
    y = ref.label.to_numpy()
    labs = np.array(sorted(set(y)))
    sums = class_sums(X, y, labs)
    C = normalize(sums)
    S, _ = loo_scores(X, y)
    pred, _, _ = assign(S, labs)
    rows, extra, featrows, sim_rows, sim_extra = [], [], [], [], []
    for i, (_, doc) in enumerate(ref.iterrows()):
        x = X[i]
        own = np.searchsorted(labs, y[i])
        Ci = C.copy()
        Ci[own] = normalize((sums[own] - x.toarray().ravel())[None])[0]
        s = np.asarray(x @ Ci.T).ravel()
        o = np.argsort(-s)
        d = Ci[o[0]] - Ci[o[1]]
        occ = occurrences(doc, frequent)
        cells, feats, freq, comm = decompose(x, d, occ, names, common)
        rows.append(cells)
        # the similarity to the text's own tradition, decomposed the same way (what the playground shows)
        sc, _, sfreq, scomm = decompose(x, Ci[own], occ, names, common)
        sim_rows.append(sc)
        sim_extra.append({"txtid": doc.txtid, "tradition": y[i], "correct": labs[o[0]] == y[i],
                          "margin": float(s[own]), "frequent_words": sfreq, "common_features": scomm})
        extra.append({"txtid": doc.txtid, "kind": "reference", "tradition": y[i], "nearest": labs[o[0]],
                      "runner_up": labs[o[1]], "correct": labs[o[0]] == y[i], "margin": float(s[o[0]] - s[o[1]]),
                      "n_words": doc.n_words, "frequent_words": freq, "common_features": comm})
        featrows += [(y[i], labs[o[0]] == y[i], f, v) for f, v in feats.items()]
    assert np.all(pred == np.array([e["nearest"] for e in extra])), "closed-form LOO and explicit LOO disagree"
    df, sim = table(rows, extra), table(sim_rows, sim_extra)
    check(df)
    check(sim)
    return df, sim, pd.DataFrame(featrows, columns=["tradition", "correct", "feature", "contribution"])


def run_orphans(ref, orph, frequent):
    vec, X = featurise(ref, "both")
    names = vec.get_feature_names_out()
    common = common_mask(X)
    C, labs = centroids(X, ref.label.to_numpy())
    Xo = vec.transform([tokens(r, "both") for _, r in orph.iterrows()])
    rows, extra, top = [], [], []
    for i, (_, doc) in enumerate(orph.iterrows()):
        x = Xo[i]
        s = scores(x, C).ravel()
        o = np.argsort(-s)
        cells, feats, freq, comm = decompose(x, C[o[0]] - C[o[1]], occurrences(doc, frequent), names, common)
        rows.append(cells)
        extra.append({"txtid": doc.txtid, "kind": "orphan", "tradition": None, "nearest": labs[o[0]],
                      "runner_up": labs[o[1]], "correct": None, "margin": float(s[o[0]] - s[o[1]]),
                      "n_words": doc.n_words, "frequent_words": freq, "common_features": comm})
        best = sorted(feats.items(), key=lambda kv: -abs(kv[1]))[:TOP_FEATURES]
        top.append(json.dumps([[f, round(v, 4)] for f, v in best], ensure_ascii=False))
    df = table(rows, extra)
    check(df)
    df["top_features"] = top
    return df


def frequent_ablation(ref, freq_rank):
    out = {}
    y = ref.label.to_numpy()
    for k in KS:
        drop = set(freq_rank[:k])
        sub = ref.assign(**{c: [[v for v, w in zip(vals, ws) if w not in drop] for vals, ws in zip(ref[c], ref.words)]
                            for c in ("signs", "wclasses")})
        sub["words"] = [[w for w in ws if w not in drop] for ws in ref.words]
        _, X = featurise(sub, "both")
        S, labs = loo_scores(X, y)
        p, _, _ = assign(S, labs)
        kept = sum(map(len, sub.words)) / sum(map(len, ref.words))
        out[k] = {"acc": round(float(np.mean(p == y)), 3), "word_tokens_kept": round(kept, 3),
                  "removed": list(freq_rank[:k])[:25]}
    return out


def window_test(ref, frequent, margin, ks=WINDOW_KS, reps=10, max_texts=40):
    """E11d Short windows of reference texts (as in E2: texts of >= 40 words, at most 40 per
    tradition, the text removed and the features refitted): is a placement that rests mostly on
    common features or frequent words less often right?"""
    rng = np.random.default_rng(SEED)
    long_ = ref[ref.n_words >= 40]
    long_ = long_.sample(frac=1, random_state=0).groupby("label").head(max_texts)
    rows = []
    for i, d in long_.iterrows():
        train = ref.drop(index=i)
        vec, X = featurise(train, "both")
        names = vec.get_feature_names_out()
        common = common_mask(X)
        C, labs = centroids(X, train.label.to_numpy())
        for k in ks:
            for _ in range(reps):
                s0 = rng.integers(0, d.n_words - k + 1)
                w = {"words": d.words[s0:s0 + k], "signs": d.signs[s0:s0 + k], "wclasses": d.wclasses[s0:s0 + k]}
                x = vec.transform([tokens(w, "both")])
                sc = scores(x, C).ravel()
                o = np.argsort(-sc)
                cells, _, freq, comm = decompose(x, C[o[0]] - C[o[1]], occurrences(w, frequent), names, common)
                m = float(sc[o[0]] - sc[o[1]])
                rows.append({"k": k, "tradition": d.label, "correct": labs[o[0]] == d.label, "margin": m,
                             "placed": m >= margin, "common_share": comm / m if m > 0 else np.nan,
                             "frequent_share": freq / m if m > 0 else np.nan,
                             "word_form_share": sum(v for (a_, _), v in cells.items() if a_ == "Word form") / m if m > 0 else np.nan})
    W = pd.DataFrame(rows)
    out = {}
    for k, g in W[W.placed].groupby("k"):
        mc = g.common_share > 0.5
        mf = g.frequent_share > 0.5
        out[int(k)] = {"placed": int(len(g)), "precision": round(float(g.correct.mean()), 3),
                       "mostly_common": int(mc.sum()), "precision_mostly_common": round(float(g[mc].correct.mean()), 3),
                       "precision_rest": round(float(g[~mc].correct.mean()), 3),
                       "mostly_frequent_words": int(mf.sum()),
                       "precision_mostly_frequent_words": round(float(g[mf].correct.mean()), 3) if mf.any() else None}
    return W, out


def drop_words(d, keep):
    """The same texts with the words for which keep(word, class) is False removed (word and signs)."""
    idx = [[i for i, (w, c) in enumerate(zip(ws, cs)) if keep(w, c)] for ws, cs in zip(d.words, d.wclasses)]
    return d.assign(**{col: [[v[i] for i in ix] for v, ix in zip(d[col], idx)] for col in ("words", "signs", "wclasses")})


def orphan_stability(ref, orph, frequent, margin):
    """E11e Refit without function words / without the frequent words: how many orphans change place."""
    def place(r, o):
        vec, X = featurise(r, "both")
        C, labs = centroids(X, r.label.to_numpy())
        return assign(scores(vec.transform([tokens(x, "both") for _, x in o.iterrows()]), C), labs, margin=margin)[0]
    base = place(ref, orph)
    out = {"assigned": int(pd.notna(base).sum())}
    for name, keep in (("without_function_words", lambda w, c: c != "function"),
                       ("without_frequent_words", lambda w, c: w not in frequent)):
        p = place(drop_words(ref, keep), drop_words(orph, keep))
        a = pd.notna(base)
        out[name] = {"assigned": int(pd.notna(p).sum()),
                     "same_tradition": int((a & (p == base)).sum()),
                     "other_tradition": int((a & pd.notna(p) & (p != base)).sum()),
                     "now_unassigned": int((a & pd.isna(p)).sum()),
                     "newly_assigned": int((~a & pd.notna(p)).sum())}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--report", required=True, help="report.json of run_experiments.py (groups)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--orphan-min-words", type=int, default=5)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = json.load(open(a.report))
    hist = label_map(GROUPSETS[rep["groups"]])
    allcths = sorted({str(c) for g in (HISTORICAL, ABSTRACT, GROUPSETS[rep["groups"]], RESIDUE)
                      for cs in g.values() for c in cs} | {"470"})  # the orphan pool of E5
    docs = load(a.tokens, cths=allcths)
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)]
    ref = ref.assign(label=lambda d: d.cth_number.map(hist)).reset_index(drop=True)
    orph = docs[docs.orphan & (docs.n_words >= a.orphan_min_words)].reset_index(drop=True)

    df = Counter(w for ws in ref.words for w in set(ws))
    freq_rank = [w for w, _ in sorted(df.items(), key=lambda kv: (-kv[1], kv[0]))]
    frequent = set(freq_rank[:FREQ_TOP])
    report = {"groups": rep["groups"], "frequent_words": {w: df[w] for w in freq_rank[:FREQ_TOP]},
              "reference_texts": int(len(ref))}

    R, Sim, F = run_loo(ref, frequent)
    R.to_csv(f"{a.out}/E11a_reference_decomposition.csv.gz", index=False)
    ok = R[R.correct]
    report["E11a"] = {"accuracy": round(float(R.correct.mean()), 3),
                      "all_correct": shares(ok.assign(all="all"), "all")["all"],
                      "by_tradition": shares(ok, "tradition"),
                      "similarity_all_correct": shares(Sim[Sim.correct].assign(all="all"), "all")["all"],
                      "similarity_by_tradition": shares(Sim[Sim.correct], "tradition")}
    # categories x layers over all correctly placed texts, for the figure
    cols = [c for c in R.columns if "|" in c]
    grid = (ok[cols].sum() / ok.margin.sum()).rename("share").reset_index()
    grid[["layer", "category"]] = grid["index"].str.split("|", expand=True)
    grid.pivot(index="category", columns="layer", values="share").reindex(CATEGORIES).fillna(0).round(4)[
        LAYERS].to_csv(f"{a.out}/E11a_category_by_layer.csv")

    O = run_orphans(ref, orph, frequent)
    O.to_csv(f"{a.out}/E11a_orphan_decomposition.csv", index=False)
    report["E11a"]["orphans_by_nearest"] = shares(O, "nearest")

    # E11b frequent words and single features
    ratio = lambda g, c: round(float(g[c].sum() / g.margin.sum()), 3)
    bands = pd.cut(O.n_words, [0, 10, 20, 50, 10**6], labels=["5-10", "11-20", "21-50", ">50"])
    report["E11b"] = {
        "frequent_words_share": {"all_correct": ratio(ok, "frequent_words"),
                                 **{t: ratio(g, "frequent_words") for t, g in ok.groupby("tradition")},
                                 "orphans": ratio(O, "frequent_words")},
        "similarity_frequent_words_share": ratio(Sim[Sim.correct], "frequent_words"),
        "similarity_common_features_share": ratio(Sim[Sim.correct], "common_features"),
        "common_features_share": {"all_correct": ratio(ok, "common_features"),
                                  **{t: ratio(g, "common_features") for t, g in ok.groupby("tradition")},
                                  "orphans": ratio(O, "common_features")},
        "orphans_by_length": {str(b): {"orphans": int(len(g)), "frequent_words": ratio(g, "frequent_words"),
                                       "common_features": ratio(g, "common_features"),
                                       "word_form": ratio(g.assign(w=g.filter(like="Word form|").sum(1)), "w")}
                              for b, g in O.groupby(bands, observed=True)}}
    # orphans the E2 margin assigns although most of their margin is common features
    placed = O[O.margin >= rep["E2_abstention"]["margin"]]
    mostly = placed[placed.common_features > 0.5 * placed.margin]
    report["E11b"]["assigned_orphans"] = int(len(placed))
    report["E11b"]["assigned_orphans_mostly_common"] = int(len(mostly))
    report["E11b"]["assigned_orphans_mostly_frequent_words"] = int((placed.frequent_words > 0.5 * placed.margin).sum())
    Fo = F[F.correct].groupby(["tradition", "feature"]).contribution.agg(["sum", "size"]).reset_index()
    tot = ok.groupby("tradition").margin.sum()
    Fo["share"] = (Fo["sum"] / Fo.tradition.map(tot)).round(4)
    Fo["layer"] = Fo.feature.map(layer)
    Fo["frequent_word"] = Fo.feature.isin(frequent)
    top = Fo.sort_values("share", ascending=False).groupby("tradition").head(15)
    top.to_csv(f"{a.out}/E11b_top_features.csv", index=False)
    report["E11b"]["top_features"] = {t: g[["feature", "share", "size"]].values.tolist() for t, g in top.groupby("tradition")}

    # one table per tradition, for the paper: category and layer shares of the decision
    tab = []
    for key, src in [("all reference (correct)", report["E11a"]["all_correct"]),
                     *report["E11a"]["by_tradition"].items(),
                     ("assigned orphans", shares(O[O.margin >= rep["E2_abstention"]["margin"]].assign(all="all"), "all")["all"])]:
        tab.append({"group": key, "texts": src["texts"], **src["by_category"], **src["by_layer"]})
    tab = pd.DataFrame(tab)
    fq = report["E11b"]["frequent_words_share"]
    cm = report["E11b"]["common_features_share"]
    placed_o = O[O.margin >= rep["E2_abstention"]["margin"]]
    tab["frequent words (top 25)"] = [fq.get(g, fq["all_correct"] if g.startswith("all") else ratio(placed_o, "frequent_words")) for g in tab.group]
    tab["common features"] = [cm.get(g, cm["all_correct"] if g.startswith("all") else ratio(placed_o, "common_features")) for g in tab.group]
    tab.round(3).to_csv(f"{a.out}/E11a_by_tradition.csv", index=False)
    report["E11e"] = orphan_stability(ref, orph, frequent, rep["E2_abstention"]["margin"])

    report["E11c"] = frequent_ablation(ref, freq_rank)
    W, report["E11d"] = window_test(ref, frequent, rep["E2_abstention"]["margin"])
    W.to_csv(f"{a.out}/E11d_windows.csv.gz", index=False)
    with open(f"{a.out}/E11_report.json", "w") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False, default=str)
    print(json.dumps({k: v for k, v in report.items() if k != "E11b"}, indent=1, ensure_ascii=False, default=str)[:6000])
    print(json.dumps({k: v for k, v in report["E11b"].items() if k != "top_features"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
