"""A worked example: one orphan, from its text to its placement and the evidence behind it.

For the given fragment: its text by line; its similarity to every tradition and the margin rule
(E2, E5); the words and sign sequences that carry the decision (E11 decomposition); the
manuscripts closest to it among the reference and the texts no study assigns (CTH 390-469
residue, CTH 500), as candidate parallels to check by hand; and, for each of its distinctive
words, the CTH numbers where it is attested.

Usage: python run_case.py TOKENS.csv --run results/<run> --txtid "KBo 41.22" --out results/<run>/case
"""
import argparse
import json
import os
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, RESIDUE, label_map, is_orphan
from run_attribution import decompose, occurrences, common_mask
from run_experiments import MIN_WORDS, featurise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", default="KBo 41.22")
    ap.add_argument("--out", required=True)
    ap.add_argument("--neighbours", type=int, default=10)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    res = {str(c): name for name, cs in RESIDUE.items() for c in cs}
    raw = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str})
    cth = raw.loc[raw.txtid == a.txtid, "cth_number"].iloc[0]
    docs = load(a.tokens, cths=sorted(set(hist) | set(res) | {cth}))
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].assign(
        label=lambda d: d.cth_number.map(hist)).reset_index(drop=True)
    resd = docs[~docs.orphan & docs.cth_number.isin(res) & (docs.n_words >= MIN_WORDS)].assign(
        label=lambda d: d.cth_number.map(res)).reset_index(drop=True)
    frag = docs[docs.txtid == a.txtid].iloc[0]

    vec, X = featurise(ref, "both")
    names = vec.get_feature_names_out()
    C, labs = centroids(X, ref.label.to_numpy())
    x = vec.transform([tokens(frag, "both")])
    s = scores(x, C).ravel()
    pred, top, gap = assign(s[None], labs, margin=margin)
    o = np.argsort(-s)
    df = Counter(w for ws in ref.words for w in set(ws))
    frequent = {w for w, _ in df.most_common(25)}
    cells, feats, freq, comm = decompose(x, C[o[0]] - C[o[1]], occurrences(frag, frequent), names, common_mask(X))
    m = s[o[0]] - s[o[1]]

    # nearest manuscripts: reference and unassigned rituals, in the same feature space
    pool = pd.concat([ref, resd]).reset_index(drop=True)
    P = normalize(vec.transform([tokens(r, "both") for _, r in pool.iterrows()]))
    sim = np.asarray((P @ x.T).todense()).ravel()
    nn = pool.assign(similarity=sim.round(4)).sort_values("similarity", ascending=False).head(a.neighbours)

    # where its distinctive words occur, by CTH, across the whole release
    words = [w for w in dict.fromkeys(frag.words) if w in names and df.get(w, 0) < 0.25 * len(ref)]
    where = {w: raw[raw.word == w].groupby("cth_number").txtid.nunique().sort_values(ascending=False).head(6).to_dict()
             for w in words}

    lines = raw[raw.txtid == a.txtid].groupby("lnr", sort=False).translit.agg(lambda s: " ".join(map(str, s)))
    # each legible word's share of the decision: its word form and its sign n-grams, each feature
    # divided over the words it occurs in (as in E11)
    occ_n = Counter()
    per_word = []
    for w, sg in zip(frag.words, frag.signs):
        fs = [w] + tokens({"words": [], "signs": [sg]}, "both")
        per_word.append(fs)
        occ_n.update(fs)
    word_share = [sum(feats.get(f, 0.0) / occ_n[f] for f in fs) / m for fs in per_word]
    leg = raw[(raw.txtid == a.txtid)].reset_index(drop=True)
    leg = leg[leg.word.notna() & (leg.word != "")].reset_index(drop=True)
    assert len(leg) == len(word_share), "token table and document disagree"
    tokens_out = [[r.lnr, r.translit, r.word, round(float(v), 3)] for r, v in zip(leg.itertuples(), word_share)]
    out = {"txtid": a.txtid, "filed_under": cth, "legible_words": int(frag.n_words),
           "text": [f"{k}  {v}" for k, v in lines.items()],
           "similarity": {labs[j]: round(float(s[j]), 4) for j in o},
           "nearest": labs[o[0]], "runner_up": labs[o[1]], "margin": round(float(m), 4),
           "rule_margin": margin, "assigned": pred[0],
           "decision_by_layer_category": {f"{k[0]} | {k[1]}": round(v / m, 3) for k, v in
                                          sorted(cells.items(), key=lambda kv: -kv[1]) if abs(v / m) >= 0.02},
           "decision_share_common_features": round(comm / m, 3), "decision_share_frequent_words": round(freq / m, 3),
           "decision_features": [[f, round(v / m, 3)] for f, v in sorted(feats.items(), key=lambda kv: -kv[1])[:15]],
           "against_features": [[f, round(v / m, 3)] for f, v in sorted(feats.items(), key=lambda kv: kv[1])[:5]],
           "nearest_manuscripts": nn[["txtid", "cth_number", "label", "n_words", "similarity"]].values.tolist(),
           "distinctive_words_by_cth": where, "word_shares": tokens_out,
           # every non-zero feature of the fragment, for figures that trace the decision term by term
           "dim": int(len(names)), "n_features": int(x.nnz),
           "features": [{"name": names[j], "x": round(float(v), 6), "idf": round(float(vec.idf_[j]), 6),
                         "c_top": round(float(C[o[0], j]), 6), "c_second": round(float(C[o[1], j]), 6),
                         "contribution": round(float(v * (C[o[0], j] - C[o[1], j])), 6)}
                        for j, v in sorted(zip(x.indices, x.data), key=lambda jv: -jv[1] * (C[o[0], jv[0]] - C[o[1], jv[0]]))],
           "ref_counts": ref.label.value_counts().to_dict(),
           "tokens": [{"lnr": r.lnr, "translit": r.translit, "word": r.word if isinstance(r.word, str) else "",
                       "wclass": r.wclass if isinstance(r.wclass, str) else "", "wc_rule": r.wc_rule if isinstance(r.wc_rule, str) else "",
                       "wc_conf": r.wc_conf if isinstance(r.wc_conf, str) else ""}
                      for r in raw[raw.txtid == a.txtid].itertuples()]}
    slug = a.txtid.replace(" ", "_").replace(".", "_")
    with open(f"{a.out}/case_{slug}.json", "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False, default=str)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
