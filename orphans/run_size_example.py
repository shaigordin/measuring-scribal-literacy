"""One manuscript cut into growing windows: a concrete example for the coverage curve (E2).

The manuscript is left out of the reference; the remaining reference manuscripts (literature
traditions, 17+ words) give the tradition centroids, in the words+spellings space. Windows of
k words start at fixed positions (nested: the 3-word window is the start of the 10-word one,
which is the start of the 40-word one). For each k we also report how often windows of that
size from this manuscript, at every start position, are placed correctly and confidently
(gap >= the calibrated margin of report.json).

Usage: python run_size_example.py data/tokens.csv --run results/tlhdig03_literature \
         --txtid "KUB 29.4+" --starts 0 200 400 --out results/tlhdig03_literature/case
"""
import argparse
import json

import numpy as np

from qtm.assign import assign, centroids, scores
from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, is_orphan, label_map
from run_experiments import MIN_WORDS, featurise

KS = (3, 10, 40)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", default="KUB 29.4+")
    ap.add_argument("--starts", type=int, nargs="+", default=[0])
    ap.add_argument("--space", default="both")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    docs = load(a.tokens, cths=sorted(hist))
    docs = docs[[not is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]]
    docs = docs[docs.n_words >= MIN_WORDS].assign(label=lambda d: d.cth_number.map(hist))
    d = docs[docs.txtid == a.txtid].iloc[0]
    train = docs[docs.txtid != a.txtid]
    vec, X = featurise(train, a.space)
    C, labs = centroids(X, train.label.to_numpy())

    def place(s, k):
        S = scores(vec.transform([tokens({"words": d.words[s:s + k], "signs": d.signs[s:s + k]}, a.space)]), C)
        order = np.argsort(-S[0])
        pred, top, gap = assign(S, labs)
        return {"words": list(d.words[s:s + k]), "translit": [str(t) for t in d.translits[s:s + k]], "nearest": pred[0], "runner_up": labs[order[1]],
                "gap": round(float(gap[0]), 4), "placed": bool(gap[0] >= margin),
                "right": bool(pred[0] == d.label)}

    examples = [{"start": s, "windows": {k: place(s, k) for k in KS}} for s in a.starts]
    rates = {}
    for k in KS:
        res = [place(s, k) for s in range(0, d.n_words - k + 1)]
        rates[k] = {"windows": len(res),
                    "right": round(float(np.mean([r["right"] for r in res])), 3),
                    "placed": round(float(np.mean([r["placed"] for r in res])), 3),
                    "right_when_placed": round(float(np.mean([r["right"] for r in res if r["placed"]] or [np.nan])), 3)}
    out = {"txtid": a.txtid, "cth": d.cth_number, "tradition": d.label, "n_words": int(d.n_words),
           "space": a.space, "margin": margin, "examples": examples, "all_windows": rates}
    fn = f"{a.out}/size_example_{a.txtid.replace(' ', '_').replace('+', '')}.json"
    json.dump(out, open(fn, "w"), ensure_ascii=False, indent=1)
    print(json.dumps({"tradition": d.label, "n": int(d.n_words), "rates": rates}, ensure_ascii=False))
    for e in examples:
        for k, w in e["windows"].items():
            print(e["start"], k, w["nearest"], w["gap"], w["placed"], w["right"], " ".join(w["words"][:12]))


if __name__ == "__main__":
    main()
