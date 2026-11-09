"""Why an orphan stays unplaced: its tradition scores and nearest manuscripts, with the shared terms.

For one orphan: cosine similarity to each tradition centroid (reference: literature traditions,
17+ words, words+spellings space, as in E5), and its nearest single manuscripts among the
reference plus residue rituals (as in run_trail.py), each with the terms that contribute most
to that similarity (product of the two tf-idf weights).

Usage: python run_unplaced_example.py data/tokens.csv --run results/tlhdig03_literature \
         --txtid "KBo 61.39" --out results/tlhdig03_literature/case
"""
import argparse
import json

import numpy as np
from sklearn.preprocessing import normalize

from qtm.assign import centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, RESIDUE, is_orphan, label_map
from run_experiments import MIN_WORDS, featurise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", default="KBo 61.39")
    ap.add_argument("--space", default="both")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    hist = label_map(GROUPSETS[rep["groups"]])
    res = {str(c): n for n, cs in RESIDUE.items() for c in cs}
    import pandas as pd
    raw = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str})
    cth = raw.loc[raw.txtid == a.txtid, "cth_number"].iloc[0]
    docs = load(a.tokens, cths=sorted(set(hist) | set(res) | {cth}))
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].reset_index(drop=True)
    pool = docs[~docs.orphan & docs.cth_number.isin(set(hist) | set(res)) & (docs.n_words >= MIN_WORDS)].reset_index(drop=True)
    frag = docs[docs.txtid == a.txtid].iloc[0]
    vec, X = featurise(ref, a.space)
    vocab = np.array(vec.get_feature_names_out())
    C, labs = centroids(X, ref.cth_number.map(hist).to_numpy())
    x = normalize(vec.transform([tokens(frag, a.space)]))
    trad = sorted(zip(labs, scores(x, C)[0]), key=lambda t: -t[1])
    P = normalize(vec.transform([tokens(r, a.space) for _, r in pool.iterrows()]))
    sim = np.asarray((P @ x.T).todense()).ravel()
    xd = np.asarray(x.todense()).ravel()
    near = []
    for i in np.argsort(-sim)[:a.top]:
        contrib = np.asarray(P[i].todense()).ravel() * xd
        terms = [(vocab[j], round(float(contrib[j] / sim[i]), 3)) for j in np.argsort(-contrib)[:5] if contrib[j] > 0]
        c = pool.cth_number[i]
        near.append({"txtid": pool.txtid[i], "cth": c, "group": hist.get(c, res.get(c, "")),
                     "similarity": round(float(sim[i]), 4), "top_terms_share": terms})
    out = {"txtid": a.txtid, "cth": cth, "translit": " ".join(map(str, frag.translits)),
           "words": list(frag.words), "margin": rep["E2_abstention"]["margin"],
           "traditions": [(l, round(float(s), 4)) for l, s in trad], "nearest": near, "pool_size": int(len(pool))}
    fn = f"{a.out}/unplaced_{a.txtid.replace(' ', '_').replace('.', '_')}.json"
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
