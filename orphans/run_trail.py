"""The Konkordanz trail for one orphan, checked against our feature space.

For KBo 41.22 the Konkordanz (accessed 2026-11-09) lists CTH 458 and a suspected join with
KBo 17.54++ (J. Miller, 15.01.2024), and the same suspected join for KUB 35.146; F. Fuscagni
(29.01.2024) suspects a join of KBo 17.54 with KBo 47.130 (CTH 409.IV). This script ranks those
pieces by similarity to the fragment among the pool of run_case.py (reference manuscripts and the
unassigned CTH 390-469 / 500 rituals), in the words+spellings space of the main model. KBo 17.54+
carries no word analyses in TLHdig, so it is also ranked in the spellings-only space.

Usage: python run_trail.py data/tokens.csv --run results/tlhdig03_literature --out results/tlhdig03_literature/case
"""
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.corpus import load, signs
from qtm.features import tokens
from qtm.groups import GROUPSETS, RESIDUE, label_map, is_orphan
from run_experiments import MIN_WORDS, featurise

TRAIL = {"KUB 35.146": "Miller 2024: suspected join with KBo 17.54++",
         "KBo 17.54+": "CTH 458.1.1 (Fuscagni ed.); Miller 2024: suspected join partner",
         "KBo 47.130+": "CTH 409.IV; Fuscagni 2024: suspected join with KBo 17.54"}


def ranked(pool, frag, space, ref):
    vec, _ = featurise(ref, space)
    P = normalize(vec.transform([tokens(r, space) for _, r in pool.iterrows()]))
    x = normalize(vec.transform([tokens(frag, space)]))
    sim = np.asarray((P @ x.T).todense()).ravel()
    out = pool[["txtid", "cth_number"]].assign(similarity=sim.round(4))
    out["rank"] = out.similarity.rank(ascending=False, method="min").astype(int)
    return out.sort_values("rank")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", default="KBo 41.22")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    hist = label_map(GROUPSETS[rep["groups"]])
    res = {str(c): name for name, cs in RESIDUE.items() for c in cs}
    raw = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str})
    cth = raw.loc[raw.txtid == a.txtid, "cth_number"].iloc[0]
    docs = load(a.tokens, cths=sorted(set(hist) | set(res) | {cth}))
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].reset_index(drop=True)
    keep = docs.txtid.isin(TRAIL)
    pool = docs[(~docs.orphan & docs.cth_number.isin(set(hist) | set(res)) & (docs.n_words >= MIN_WORDS)) | keep]
    pool = pool[pool.txtid != a.txtid].reset_index(drop=True)
    # trail pieces without word analyses (e.g. KBo 17.54+ in BESRIT) are dropped by load();
    # add them with their spellings only, so they can be ranked in the spellings space
    for t in set(TRAIL) - set(pool.txtid):
        rows = raw[(raw.txtid == t) & raw.translit.notna()]
        if len(rows):
            tl = rows.translit.astype(str).tolist()
            pool = pd.concat([pool, pd.DataFrame([{"txtid": t, "cth_number": rows.cth_number.iloc[0], "words": [],
                              "translits": tl, "signs": [signs(x) for x in tl], "n_words": 0, "orphan": False}])],
                             ignore_index=True)
    frag = docs[docs.txtid == a.txtid].iloc[0]
    out = {"txtid": a.txtid, "pool_size": int(len(pool)), "pieces": {}}
    for space in ("both", "signs"):
        r = ranked(pool, frag, space, ref)
        out[f"top20_{space}"] = r.head(20).values.tolist()
        for t, why in TRAIL.items():
            row = r[r.txtid == t]
            if len(row):
                out["pieces"].setdefault(t, {"note": why, "cth": row.cth_number.iloc[0],
                                             "analysed_words": int(pool.loc[pool.txtid == t, "n_words"].iloc[0])})
                out["pieces"][t][space] = {"similarity": float(row.similarity.iloc[0]), "rank": int(row["rank"].iloc[0])}
    json.dump(out, open(f"{a.out}/trail_{a.txtid.replace(' ', '_').replace('.', '_')}.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
