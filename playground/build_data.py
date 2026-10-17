"""Export the orphan-assignment model to JSON for the static playground.

Reuses ../orphans/qtm so the page scores fragments exactly as run_experiments.py does
(the deck's main reference: literature-defined groups with the HFR split; "both" feature space,
nearest-centroid cosine, abstention margin), and adds the E9 open-set check of run_openset.py
(fit floor per fragment size, and a genre gate with the outside genres as classes).

Usage: python build_data.py TOKENS.csv [--run ../orphans/results/tlhdig03_literature] [--out data]
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "orphans"))
from qtm.corpus import load  # noqa: E402
from qtm.features import tokens, vectorizer  # noqa: E402
from qtm.assign import centroids, scores, loo_scores, assign  # noqa: E402
from qtm.groups import GROUPSETS, HISTORICAL, ABSTRACT, RESIDUE, label_map, is_orphan  # noqa: E402
from run_openset import outside_genres  # noqa: E402

MIN_WORDS = 17
ORPHAN_MIN_WORDS = 5
CORE = 200          # size of each tradition's "archetype" vocabulary (as in E6)
_EDIT = re.compile(r"[\[\]⸢⸣()?!~′'<>«»#*]")


def r(x, n=4):
    return [round(float(v), n) for v in x]


def sparse_rows(X, n=4):
    """CSR rows as [[col, ...], [val, ...]] pairs."""
    X = X.tocsr()
    out = []
    for i in range(X.shape[0]):
        s, e = X.indptr[i], X.indptr[i + 1]
        out.append([X.indices[s:e].tolist(), r(X.data[s:e], n)])
    return out


def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{path}: {os.path.getsize(path) / 1e6:.2f} MB")


def canon(t):
    """One whitespace-free form per word, so pasted text splits into words on spaces."""
    t = _EDIT.sub("", str(t)).strip()
    t = re.sub(r"\s*([{}])\s*", r"\1", t)
    return re.sub(r"\s+", "-", t)


def text_of(d):
    return " ".join(canon(t) for t in d.translits)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", default=os.path.join(os.path.dirname(__file__), "..", "orphans",
                                                  "results", "tlhdig03_literature"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "data"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report = json.load(open(f"{a.run}/report.json"))
    e9 = json.load(open(f"{a.run}/E9_report.json"))
    margin = report["E2_abstention"]["margin"]
    groups = GROUPSETS[report["groups"]]
    floors = {int(k): v["fit_floor"] for k, v in e9["by_k"].items()}
    # unrounded floors, as run_openset.py applies them (the report rounds them to 4 places)
    fit = pd.read_csv(f"{a.run}/E9_orphan_fit.csv")
    for k in floors:
        exact = fit.loc[fit.fit_floor.round(4) == floors[k], "fit_floor"]
        if len(exact):
            floors[k] = float(exact.iloc[0])

    hist = label_map(groups)
    outside = outside_genres(hist)
    out_map = label_map(outside)
    # the CTHs run_experiments.py loads (its orphan pool), plus the outside genres of run_openset.py
    allcths = set(hist) | {str(c) for g in (HISTORICAL, ABSTRACT, RESIDUE) for cs in g.values() for c in cs} | {"470"} | set(out_map)
    docs = load(a.tokens, cths=sorted(allcths))  # same pool as run_experiments.py
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & (docs.n_words >= MIN_WORDS) & docs.cth_number.isin(hist)].copy()
    ref["label"] = ref.cth_number.map(hist)
    pool = docs.cth_number.isin(allcths - set(out_map))  # the orphan pool of run_experiments.py
    orph = docs[docs.orphan & pool & (docs.n_words >= ORPHAN_MIN_WORDS)].copy()
    y = ref.label.to_numpy()
    # outside-genre texts, sampled exactly as run_openset.py does
    oth = docs[~docs.orphan & (docs.n_words >= MIN_WORDS) & docs.cth_number.isin(out_map)].copy()
    oth["label"] = oth.cth_number.map(out_map)
    oth = oth.sample(frac=1, random_state=0).groupby("label").head(300)

    # --- scoring model ("both" space, as in E5) ---
    vec = vectorizer()
    X = vec.fit_transform([tokens(d, "both") for _, d in ref.iterrows()])
    C, labs = centroids(X, y)
    vocab = vec.get_feature_names_out().tolist()
    loo, _ = loo_scores(X, y)
    Xo = vec.transform([tokens(d, "both") for _, d in orph.iterrows()])
    So = scores(Xo, C)
    pred, top, gap = assign(So, labs, margin=margin)

    # E9 genre gate: reference traditions and outside genres as classes, fitted on both
    gdocs = pd.concat([ref, oth])
    gvec = vectorizer()
    GX = gvec.fit_transform([tokens(d, "both") for _, d in gdocs.iterrows()])
    GC, glabs = centroids(GX, gdocs.label.to_numpy())
    gpred, _, ggap = assign(scores(gvec.transform([tokens(d, "both") for _, d in orph.iterrows()]), GC), glabs)
    ks = np.array(sorted(floors))
    floor_of = lambda n: floors[int(ks[ks <= n].max())] if n >= ks.min() else floors[int(ks.min())]
    out_flag = np.array([g in outside and round(gg, 4) >= margin for g, gg in zip(gpred, ggap)])  # E9 compares the rounded gap
    low_flag = np.array([round(t, 4) < floor_of(n) for t, n in zip(top, orph.n_words)])  # E9 uses the rounded score

    # translit -> normalised word form, for words in the vocabulary
    tl = pd.read_csv(a.tokens, usecols=["word", "translit"], low_memory=False).dropna()
    tl["clean"] = tl.translit.map(canon)
    words_in_vocab = {v for v in vocab if not v.startswith("§")}
    tl = tl[tl.word.isin(words_in_vocab)]
    lookup = tl.groupby("clean").word.agg(lambda s: s.value_counts().index[0]).to_dict()

    core = {lab: np.argsort(-C[j])[:CORE].tolist() for j, lab in enumerate(labs)}
    model = {
        "source": "TLHdig Beta 0.3 (Zenodo 10.5281/zenodo.20328284)",
        "traditions": labs.tolist(),
        "cths": {lab: groups[lab] for lab in labs},
        "margin": margin,
        "vocab": vocab,
        "idf": r(vec.idf_, 5),
        "centroids": [[np.nonzero(c)[0].tolist(), r(c[np.nonzero(c)[0]], 6)] for c in C],
        "core": core,
        "lookup": lookup,
        "openset": {"floors": floors, "outside": list(outside)},
    }
    dump(model, f"{a.out}/model.json")
    dump({"vocab": gvec.get_feature_names_out().tolist(), "idf": r(gvec.idf_, 5), "classes": glabs.tolist(),
          "centroids": [[np.nonzero(c)[0].tolist(), r(c[np.nonzero(c)[0]], 6)] for c in GC]},
         f"{a.out}/gate.json")

    # --- corpus: every reference text (leave-one-out scores) and every orphan ---
    def rows(df, S, kind, extra):
        out = []
        for i, (_, d) in enumerate(df.iterrows()):
            out.append({"id": d.txtid, "cth": d.cth_number, "kind": kind, "n": int(d.n_words),
                        "s": r(np.where(np.isfinite(S[i]), S[i], 0)), **extra(i, d)})
        return out

    corpus = rows(ref, loo, "ref", lambda i, d: {"label": d.label}) + \
        rows(orph, So, "orphan", lambda i, d: {"assigned": pred[i], "gap": round(float(gap[i]), 4),
                                         "low_fit": bool(low_flag[i]),
                                         "outside": gpred[i] if out_flag[i] else None})
    texts = {d.txtid: text_of(d) for df in (ref, orph) for _, d in df.iterrows()}
    dump(corpus, f"{a.out}/corpus.json")
    dump(texts, f"{a.out}/texts.json")

    # --- word-level tf-idf per manuscript (words space), for the comparison view ---
    wvec = vectorizer()
    W = wvec.fit_transform([tokens(d, "words") for _, d in ref.iterrows()])
    Wo = wvec.transform([tokens(d, "words") for _, d in orph.iterrows()])
    WC, _ = centroids(W, y)
    dump({"vocab": wvec.get_feature_names_out().tolist(), "idf": r(wvec.idf_, 5),
          "ids": ref.txtid.tolist() + orph.txtid.tolist(),
          "rows": sparse_rows(W) + sparse_rows(Wo),
          "centroids": [[np.nonzero(c)[0].tolist(), r(c[np.nonzero(c)[0]], 5)] for c in WC]},
         f"{a.out}/words.json")

    acc = float(np.mean(assign(loo, labs)[0] == y))
    print(f"reference {len(ref)}, orphans {len(orph)}, vocab {len(vocab)}, LOO acc {acc:.3f}, "
          f"orphans assigned {int(pd.notna(pred).sum())}, below fit floor {int(low_flag.sum())}, "
          f"outside genre by margin {int(out_flag.sum())}")


if __name__ == "__main__":
    main()
