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

APP = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))      # playground/
sys.path.insert(0, os.path.join(APP, "..", "orphans"))
from qtm.corpus import load  # noqa: E402
from qtm.features import tokens, vectorizer  # noqa: E402
from qtm.assign import centroids, scores, loo_scores, assign  # noqa: E402
from qtm.groups import GROUPSETS, HISTORICAL, ABSTRACT, RESIDUE, label_map, is_orphan  # noqa: E402
from qtm.wordclass import CATEGORY, CATEGORIES, LAYERS, category, layer  # noqa: E402
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


# Word classes of experiment E8 grouped for display (qtm/wordclass.py, shared with E11).
# Every feature is attributed to the words that produce it: a word form to its occurrences, a
# sign n-gram to the words it occurs in. So each word's share of a score splits into three
# layers: its form (what is written), its syllabic spelling and its logographic writing (how).
COMMON = 0.25       # a feature attested in at least a quarter of the reference texts is "common" (E11)


def word_ngrams(sg):
    return ["§" + "·".join(sg[i:i + k]) for k in (1, 2, 3) for i in range(len(sg) - k + 1)]


def attribute(words, signs, classes, x, c, index):
    """(category x layer) contributions to x . c, distributing each feature over its words."""
    out = np.zeros((len(CATEGORIES), len(LAYERS)))
    per_word = [[w] + word_ngrams(sg) for w, sg in zip(words, signs)]
    total = {}
    for feats in per_word:
        for f in feats:
            total[f] = total.get(f, 0) + 1
    for feats, cl in zip(per_word, classes):
        ci = CATEGORIES.index(category(cl))
        for f in feats:
            j = index.get(f)
            if j is not None:
                out[ci, LAYERS.index(layer(f))] += x[j] * c[j] / total[f]
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
    ap.add_argument("--run", default=os.path.join(APP, "..", "orphans",
                                                  "results", "tlhdig03_literature"))
    ap.add_argument("--out", default=os.path.join(APP, "data"))
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

    # E9 genre gate: reference traditions and outside genres as classes, fitted on both
    gdocs = pd.concat([ref, oth])
    gvec = vectorizer()
    GX = gvec.fit_transform([tokens(d, "both") for _, d in gdocs.iterrows()])
    GC, glabs = centroids(GX, gdocs.label.to_numpy())
    ks = np.array(sorted(floors))
    floor_of = lambda n: floors[int(ks[ks <= n].max())] if n >= ks.min() else floors[int(ks.min())]
    common = np.asarray((X > 0).mean(0)).ravel() >= COMMON

    def judge(df):
        """Placement (E5), open-set check (E9) and common-feature share of the margin (E11b)
        for texts outside the reference."""
        Xd = vec.transform([tokens(d, "both") for _, d in df.iterrows()]).tocsr()
        S = scores(Xd, C)
        pred, top, gap = assign(S, labs, margin=margin)
        gpred, _, ggap = assign(scores(gvec.transform([tokens(d, "both") for _, d in df.iterrows()]), GC), glabs)
        out = np.array([g in outside and round(gg, 4) >= margin for g, gg in zip(gpred, ggap)])  # E9 rounds the gap
        low = np.array([round(t, 4) < floor_of(n) for t, n in zip(top, df.n_words)])  # E9 rounds the score
        share = np.zeros(len(df))
        for i in range(len(df)):
            o = np.argsort(-S[i])
            x = Xd[i]
            dv = C[o[0], x.indices] - C[o[1], x.indices]
            m = float(x.data @ dv)
            share[i] = float((x.data * dv * common[x.indices]).sum()) / m if m > 0 else 0.0
        return S, [{"assigned": pred[i], "gap": round(float(gap[i]), 4), "low_fit": bool(low[i]),
                    "outside": gpred[i] if out[i] else None, "common": round(float(share[i]), 3)}
                   for i in range(len(df))]

    So, ov = judge(orph)

    # translit -> normalised word form, for words in the vocabulary
    tl = pd.read_csv(a.tokens, usecols=["word", "translit", "wclass"], low_memory=False).dropna(subset=["word", "translit"])
    # word class of each word form: its most frequent definite E8 class in the corpus
    definite = tl[tl.wclass.isin(list(CATEGORY))]
    wclass = definite.groupby("word").wclass.agg(lambda s: s.value_counts().index[0]).to_dict()
    tl["clean"] = tl.translit.map(canon)
    words_in_vocab = {v for v in vocab if not v.startswith("§")}
    tl = tl[tl.word.isin(words_in_vocab)]
    lookup = tl.groupby("clean").word.agg(lambda s: s.value_counts().index[0]).to_dict()

    core = {lab: np.argsort(-C[j])[:CORE].tolist() for j, lab in enumerate(labs)}

    # How each tradition's reference texts divide (a) their similarity to their own centroid and
    # (b) their decision margin (nearest minus runner-up, E11) among word classes and layers, with
    # leave-one-out centroids as in E11a: ratio of sums over the correctly placed texts.
    index = {t: i for i, t in enumerate(vocab)}
    sums = np.vstack([np.asarray(X[y == lab].sum(0)).ravel() for lab in labs])
    Cn = sums / np.linalg.norm(sums, axis=1, keepdims=True)
    own = np.searchsorted(labs, y)
    Xd = X.tocsr()
    sim, dec, simtot, dectot, ok = [], [], [], [], []
    for i, (_, d) in enumerate(ref.iterrows()):
        row = Xd[i].toarray().ravel()
        Ci = Cn.copy()
        Ci[own[i]] = (sums[own[i]] - row) / np.linalg.norm(sums[own[i]] - row)
        s = Ci @ row
        o = np.argsort(-s)
        sim.append(attribute(d.words, d.signs, d.wclasses, row, Ci[own[i]], index))
        dec.append(attribute(d.words, d.signs, d.wclasses, row, Ci[o[0]] - Ci[o[1]], index))
        simtot.append(s[own[i]])
        dectot.append(s[o[0]] - s[o[1]])
        ok.append(o[0] == own[i])
    sim, dec, simtot, dectot, ok = map(np.array, (sim, dec, simtot, dectot, ok))
    assert np.allclose(dec.sum((1, 2)), dectot) and np.allclose(sim.sum((1, 2)), simtot)
    ratio = lambda m, t, sel: (m[sel].sum(0) / t[sel].sum()).round(3).tolist()
    baseline = {lab: ratio(sim, simtot, ok & (own == j)) for j, lab in enumerate(labs)}
    decision = {lab: ratio(dec, dectot, ok & (own == j)) for j, lab in enumerate(labs)}
    pd.DataFrame([{"tradition": lab, "word_class": CATEGORIES[ci], "layer": LAYERS[li],
                   "similarity_share": baseline[lab][ci][li], "decision_share": decision[lab][ci][li]}
                  for lab in labs for ci in range(len(CATEGORIES)) for li in range(len(LAYERS))]
                 ).to_csv(f"{a.out}/category_shares.csv", index=False)
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
        "categories": CATEGORIES,
        "layers": LAYERS,
        "wordCategory": {w: category(c) for w, c in wclass.items() if w in index},
        "categoryBaseline": baseline,
        "decisionBaseline": decision,
        "common": np.nonzero(common)[0].tolist(),
    }
    dump(model, f"{a.out}/model.json")
    dump({"vocab": gvec.get_feature_names_out().tolist(), "idf": r(gvec.idf_, 5), "classes": glabs.tolist(),
          "centroids": [[np.nonzero(c)[0].tolist(), r(c[np.nonzero(c)[0]], 6)] for c in GC]},
         f"{a.out}/gate.json")

    # --- corpus: every TLHdig text (reference texts with leave-one-out scores) ---
    def rows(df, S, kind, extra, with_scores=True):
        out = []
        for i, (_, d) in enumerate(df.iterrows()):
            s = {"s": r(np.where(np.isfinite(S[i]), S[i], 0))} if with_scores else {}
            out.append({"id": d.txtid, "cth": d.cth_number, "kind": kind, "n": int(d.n_words), **s, **extra(i, d)})
        return out

    # every other TLHdig text, judged the same way, so the page can show each CTH bin
    seen = set(ref.txtid) | set(orph.txtid)
    rest = load(a.tokens)
    rest = rest[~rest.txtid.isin(seen)]
    rest_long = rest[rest.n_words >= ORPHAN_MIN_WORDS]
    Sr, rv = judge(rest_long)
    trained = set(oth.txtid)  # texts the genre gate was fitted on: their gate verdict is in-sample
    short = pd.concat([docs[docs.orphan & pool & (docs.n_words < ORPHAN_MIN_WORDS)].assign(kind="orphan"),
                       rest[rest.n_words < ORPHAN_MIN_WORDS].assign(kind="other")])

    corpus = rows(ref, loo, "ref", lambda i, d: {"label": d.label}) + \
        rows(orph, So, "orphan", lambda i, d: ov[i]) + \
        rows(rest_long, Sr, "other", lambda i, d: {**rv[i], **({"gate_fit": True} if d.txtid in trained else {})},
             with_scores=False) + \
        [{"id": d.txtid, "cth": d.cth_number, "kind": d.kind, "n": int(d.n_words), "short": True} for _, d in short.iterrows()]
    dump(corpus, f"{a.out}/corpus.json")
    titles = pd.read_csv(os.path.join(APP, "sources", "cth_titles.csv"), dtype=str)  # build/cth_titles.py
    dump(dict(zip(titles.cth, titles.title)), f"{a.out}/cth_titles.json")
    # transliterations: the model's texts first, the rest of TLHdig in a second file loaded on demand
    dump({d.txtid: text_of(d) for df in (ref, orph) for _, d in df.iterrows()}, f"{a.out}/texts.json")
    dump({d.txtid: text_of(d) for _, d in pd.concat([rest, short[short.kind == "orphan"]]).iterrows()},
         f"{a.out}/texts_more.json")

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
    n = lambda k: sum(bool(v[k]) for v in ov)
    print(f"reference {len(ref)}, orphans {len(orph)}, vocab {len(vocab)}, LOO acc {acc:.3f}, "
          f"orphans assigned {n('assigned')}, below fit floor {n('low_fit')}, outside genre by margin {n('outside')}, "
          f"assigned with mostly common features {sum(bool(v['assigned']) and v['common'] > 0.5 for v in ov)}")
    print(f"other TLHdig texts {len(rest_long)} judged, {len(short)} under {ORPHAN_MIN_WORDS} words")


if __name__ == "__main__":
    main()
