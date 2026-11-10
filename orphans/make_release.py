"""Zenodo release: closest traditions, compositions, manuscripts and join candidates for every fragment
in Laroche's residual bins.

Scope: every TLHdig text filed under CTH 470 (fragments of rituals), 500 (fragments of Kizzuwatna
rituals), 670 (fragments of festivals), 832 (fragments of various content) or the CTH 390-469
rituals that no study groups (qtm.groups.RESIDUE), and every EBo text wherever TLHdig files it.
Texts with fewer than MIN_PLACE analysed words get a row but no results ("too_small").

All scores use the main model of the paper and talk (results/tlhdig03_literature): word forms +
sign 1-3-grams, tf-idf fitted on the literature-defined reference traditions (qtm.groups.LITERATURE,
reference manuscripts of 17+ words), cosine similarity.

  traditions    cosine to the 10 tradition centroids; placed when the gap to the runner-up reaches
                the E2 margin (report.json E2_abstention), exactly as E5_orphan_placement.csv.
  open set      the E9 fit floor (5th percentile of reference windows, by fragment size) and the
                nearest class when outside genres are added as classes (E9_orphan_fit.csv).
  spellings     the R1 check: nearest tradition in sign n-grams only, reference = every manuscript
                with 17+ legible words (R1_spellings_only.json, run B).
  common        the share of the margin carried by features attested in >= 25% of reference texts
                (E11b); > 0.5 means the placement rests mostly on common material.
  compositions  cosine to the centroid of every CTH number outside the residual bins (all its
                non-orphan manuscripts of 5+ words; the fragment itself left out of its own CTH).
  manuscripts   the 20 nearest manuscripts in the whole release (5+ analysed words, the fragment
                itself excluded), with the join barcode of run_join_candidates.py: shared content
                words, identical spellings, shared two-word phrases, and the three join checks fixed
                in advance (half the words, every shared word spelled the same, a shared phrase).
  categories    share of the fragment's analysed words in each of the 10 word categories
                (qtm.wordclass.CATEGORIES; rules over TLHdig's analyses, audited).

Usage: python make_release.py data/tokens.csv --run results/tlhdig03_literature --out release
"""
import argparse
import json
import os
import re
from urllib.parse import quote

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, scores
from qtm.corpus import load, signs
from qtm.features import tokens
from qtm.groups import ABSTRACT, GROUPSETS, HISTORICAL, RESIDUE, is_orphan, label_map
from qtm.wordclass import CATEGORIES, category
from run_experiments import MIN_WORDS, featurise
from run_join_candidates import SKIP, norm_sp
from run_openset import KS, outside_genres
from run_spellings_only import legible

BINS = {"470": "CTH 470 fragments of rituals", "500": "CTH 500 fragments of Kizzuwatna rituals",
        "670": "CTH 670 fragments of festivals", "832": "CTH 832 fragments of various content",
        **{str(c): "CTH 390-469 rituals no study groups" for c in RESIDUE["CTH 390–469 residue"]}}
NOT_COMPOSITIONS = {"470", "500", "670", "832"}
MIN_PLACE = 5        # analysed words needed for a result (as for the orphans in E5)
TOP_MSS, TOP_CTH, TOP_TRAD = 20, 5, 3
COMMON = 0.25        # as in run_attribution.py
PORTAL = "https://hethport.net"
SEP = "; "
# the study that defines each reference tradition (as in README.md, "Why each reference tradition ...")
STUDIES = {
    "Kizzuwatna–Lower Land (Hurrian)": "Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3; Wegner and Salvini 1991 (ChS I/4)",
    "Syro-Mesopotamia (Hurrian)": "Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3; Salvini and Wegner 1986 (ChS I/2)",
    "Mixed (Hurrian, Syrian, Luwian)": "Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3",
    "Luwian festivals (Ištanuwa, Lallupiya)": "HFR edition module 'Luwian festivals' (hethport.net/HFR)",
    "Ḫuwaššanna festivals": "HFR edition module 'Ḫuwaššanna'; Laroche, CTH titles",
    "Palaic festivals": "HFR edition module 'Palaic festivals' (hethport.net/HFR)",
    "Kizzuwatna rituals": "Miller 2004 (StBoT 46); Strauß 2006; Görke 2010",
    "Arzawa / western rituals": "Bawanypeck 2005 (THeth 25); Mouton 2010; Archi 2015 (BiOr 72)",
    "Luwian rituals (Puriyanni, Kuwattalla)": "Mouton and Yakubovich 2021 (JLR 19/1); Yakubovich and Mouton 2023 (StBoT 72)",
    "Hattian cult layer": "Klinger 1996 (StBoT 37)",
}


def tlhdig_url(txtid, cth):
    return f"{PORTAL}/TLHdig/tlh_xtx.php?d={quote(txtid)}&o={quote('CTH ' + str(cth))}"


def konkordanz_url(txtid):
    return f"{PORTAL}/hetkonk/hetkonk_abfrage.php?p={quote(re.split(r'\s*\+', txtid)[0].strip())}"


def topk(S, k):
    """Indices of the k largest values per row, best first."""
    idx = np.argpartition(-S, min(k, S.shape[1] - 1), axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(S, idx, 1), axis=1)
    return np.take_along_axis(idx, order, 1)


def barcode(frag, cand):
    """The join barcode of run_join_candidates.py for one fragment-candidate pair."""
    fw = [(w, norm_sp(t)) for w, t in zip(frag.words, frag.translits) if not SKIP.match(w)]
    cols, seen = [], set()
    for w, t in fw:
        if w not in seen:
            seen.add(w)
            cols.append((w, t))
    pairs = sorted({(w1, w2) for (w1, _), (w2, _) in zip(fw, fw[1:]) if w1 != w2})
    spell = {}
    for w, t in zip(cand.words, cand.translits):
        spell.setdefault(w, set()).add(norm_sp(t))
    cells = "".join("S" if w in spell and t in spell[w] else ("W" if w in spell else ".") for w, t in cols)
    bigr = set(zip(cand.words, cand.words[1:]))
    shared_ph = [" ".join(p) for p in pairs if p in bigr]
    n_shared = sum(c != "." for c in cells)
    checks = {"check_half_the_words": bool(cols) and n_shared >= len(cols) / 2,
              "check_same_spellings": n_shared > 0 and "W" not in cells,
              "check_shared_phrase": bool(shared_ph)}
    return {"barcode": cells, "fragment_content_words": len(cols), "shared_words": n_shared,
            "same_spelling": cells.count("S"), "different_spelling": cells.count("W"),
            "shared_phrases": SEP.join(shared_ph), **checks, "passes_join_checks": all(checks.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True, help="results folder of the main model (report.json, E9_report.json)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    floors = {int(k): v["fit_floor"] for k, v in json.load(open(f"{a.run}/E9_report.json"))["by_k"].items()}
    trad_of = label_map(GROUPSETS[rep["groups"]])
    res_of = {str(c): n for n, cs in RESIDUE.items() for c in cs}

    # --- texts in scope (every text, analysed or not). The experiments load only the CTHs they use, and
    # a few TLHdig ids occur under two CTH numbers (two source files); loading as they do keeps every
    # score identical to E5/E9 (a text takes the first of its CTH numbers among the loaded ones).
    raw = pd.read_csv(a.tokens, low_memory=False, dtype=str)
    in_bins = raw[raw.cth_number.isin(BINS)].groupby("txtid", sort=False).cth_number.first()
    allt = raw.groupby("txtid", sort=False).agg(cth=("cth_number", "first"),
                                                n_analysed=("word", lambda s: int(s.notna().sum())),
                                                n_legible=("translit", lambda s: int(s.map(legible).sum())))
    scope = allt[allt.index.isin(in_bins.index) | allt.index.str.startswith("EBo")].copy()
    scope["cth"] = [in_bins.get(t, c) for t, c in zip(scope.index, scope.cth)]
    scope["bin"] = [BINS.get(c, "EBo filed under other CTH numbers") for c in scope.cth]

    allcths = sorted({str(c) for gs in (HISTORICAL, ABSTRACT, GROUPSETS[rep["groups"]], RESIDUE)
                      for cs in gs.values() for c in cs} | {"470"})      # as run_experiments.py
    docs = load(a.tokens)                                                # the whole release
    exp = load(a.tokens, cths=allcths)
    for d in (docs, exp):
        d["orphan"] = [is_orphan(t, c) for t, c in zip(d.txtid, d.cth_number)]
    frags = pd.concat([exp[exp.txtid.isin(scope.index)],
                       docs[docs.txtid.isin(scope.index) & ~docs.txtid.isin(exp.txtid)]])
    frags = frags[frags.n_words >= MIN_PLACE].reset_index(drop=True)
    print(f"{len(scope)} texts in scope, {len(frags)} with {MIN_PLACE}+ analysed words")

    # --- main model: traditions
    ref = exp[~exp.orphan & exp.cth_number.isin(trad_of) & (exp.n_words >= MIN_WORDS)].reset_index(drop=True)
    vec, X = featurise(ref, "both")
    y = ref.cth_number.map(trad_of).to_numpy()
    C, labs = centroids(X, y)
    Xf = normalize(vec.transform([tokens(r, "both") for _, r in frags.iterrows()]))
    S = scores(Xf, C)
    placed, top, gap = assign(S, labs, margin=margin)
    o = np.argsort(-S, axis=1)
    common = np.asarray((X > 0).mean(0)).ravel() >= COMMON
    D = C[o[:, 0]] - C[o[:, 1]]                                       # margin direction per fragment
    comm = np.asarray(Xf.multiply(sparse.csr_matrix(D * common)).sum(1)).ravel()

    # --- open set (E9): fit floor by size, nearest class with outside genres added
    out_map = label_map(outside_genres(trad_of))
    gd = load(a.tokens, cths=list(trad_of) + list(out_map))              # as run_openset.py
    gd = gd[[not is_orphan(t, c) for t, c in zip(gd.txtid, gd.cth_number)]]
    gd = gd[gd.n_words >= MIN_WORDS].reset_index(drop=True)
    gref = gd[gd.cth_number.isin(trad_of)].assign(label=lambda d: d.cth_number.map(trad_of))
    oth = gd[gd.cth_number.isin(out_map)].assign(label=lambda d: d.cth_number.map(out_map)).reset_index(drop=True)
    oth = oth.sample(frac=1, random_state=0).groupby("label").head(300)   # as run_openset.py
    g = pd.concat([gref, oth])
    gvec, GX = featurise(g, "both")
    GC, glabs = centroids(GX, g.label.to_numpy())
    gpred, _, ggap = assign(scores(gvec.transform([tokens(r, "both") for _, r in frags.iterrows()]), GC), glabs)
    outside = set(outside_genres(trad_of))
    kk = np.array(KS)
    floor = np.array([floors[int(kk[kk <= n].max())] for n in frags.n_words])

    # --- spellings only (R1, run B: every manuscript with 17+ legible words in the reference)
    rl = raw[raw.translit.map(legible)]
    sd = rl.groupby("txtid", sort=False).agg(cth_number=("cth_number", "first"), translits=("translit", list)).reset_index()
    sd["signs"] = sd.translits.map(lambda ts: [signs(t) for t in ts])
    sd["n_legible"] = sd.translits.str.len()
    sd["orphan"] = [is_orphan(t, c) for t, c in zip(sd.txtid, sd.cth_number)]
    sref = sd[~sd.orphan & sd.cth_number.isin(trad_of) & (sd.n_legible >= MIN_WORDS)].reset_index(drop=True)
    svec, SX = featurise(sref, "signs")
    SC, slabs = centroids(SX, sref.cth_number.map(trad_of).to_numpy())
    sfr = sd.set_index("txtid").loc[frags.txtid].reset_index()
    spred, _, _ = assign(scores(normalize(svec.transform([tokens(r, "signs") for _, r in sfr.iterrows()])), SC),
                         slabs, margin)

    # --- compositions: every CTH outside the residual bins, non-orphan manuscripts of 5+ words
    cd = docs[~docs.orphan & ~docs.cth_number.isin(NOT_COMPOSITIONS) & (docs.n_words >= MIN_PLACE)].reset_index(drop=True)
    XC = normalize(vec.transform([tokens(r, "both") for _, r in cd.iterrows()]))
    clabs = np.array(sorted(cd.cth_number.unique()))       # lexicographic, for searchsorted
    Y = sparse.csr_matrix((np.ones(len(cd)), (np.searchsorted(clabs, cd.cth_number), np.arange(len(cd)))),
                          shape=(len(clabs), len(cd)), dtype=float)
    sums = np.asarray((Y @ XC).todense())
    n_mss = np.asarray(Y.sum(1)).ravel().astype(int)
    pos = {t: i for i, t in enumerate(cd.txtid)}
    SCo = np.zeros((len(frags), len(clabs)))
    for i, (_, f) in enumerate(frags.iterrows()):
        s = sums
        j = pos.get(f.txtid)
        if j is not None:                                   # leave the fragment out of its own CTH
            s = sums.copy()
            k = np.searchsorted(clabs, cd.cth_number[j])
            s[k] -= XC[j].toarray().ravel()
        nrm = np.linalg.norm(s, axis=1)
        SCo[i] = np.where(nrm > 0, (s @ Xf[i].toarray().ravel()) / np.maximum(nrm, 1e-12), -np.inf)
    ctop = topk(SCo, TOP_CTH)

    # --- manuscripts: whole release, 5+ analysed words
    pool = docs[docs.n_words >= MIN_PLACE].reset_index(drop=True)
    XP = normalize(vec.transform([tokens(r, "both") for _, r in pool.iterrows()]))
    ppos = {t: i for i, t in enumerate(pool.txtid)}
    group_of = lambda r: trad_of.get(r.cth_number) or res_of.get(r.cth_number) or (
        "orphan" if r.orphan else BINS.get(r.cth_number, ""))
    pgroup = [group_of(r) for _, r in pool.iterrows()]
    long_rows, mss_top = [], []
    for s0 in range(0, len(frags), 500):
        blk = np.asarray((Xf[s0:s0 + 500] @ XP.T).todense())
        for r, i in enumerate(range(s0, min(s0 + 500, len(frags)))):
            if frags.txtid[i] in ppos:
                blk[r, ppos[frags.txtid[i]]] = -np.inf
        idx = topk(blk, TOP_MSS)
        for r, i in enumerate(range(s0, min(s0 + 500, len(frags)))):
            f = frags.iloc[i]
            mss_top.append([(pool.txtid[j], float(blk[r, j])) for j in idx[r]])
            for rank, j in enumerate(idx[r], 1):
                c = pool.iloc[j]
                long_rows.append({"txtid": f.txtid, "rank": rank, "candidate_txtid": c.txtid,
                                  "candidate_cth": c.cth_number, "candidate_group": pgroup[j],
                                  "candidate_n_words": int(c.n_words), "similarity": round(float(blk[r, j]), 4),
                                  **barcode(f, c), "candidate_tlhdig_url": tlhdig_url(c.txtid, c.cth_number)})
    J = pd.DataFrame(long_rows)

    # --- one row per text in scope
    rows = {}
    for i, f in frags.iterrows():
        cats = pd.Series([category(c) for c in f.wclasses]).value_counts(normalize=True)
        jf = J[(J.txtid == f.txtid) & J.passes_join_checks]
        rows[f.txtid] = {
            "status": "placed" if placed[i] is not None else "below_margin",
            **{k: v for t in range(TOP_TRAD) for k, v in
               ((f"tradition_{t + 1}", labs[o[i, t]]), (f"similarity_{t + 1}", round(float(S[i, o[i, t]]), 4)))},
            "margin": round(float(gap[i]), 4), "placed_tradition": placed[i] or "",
            "fit_floor": round(float(floor[i]), 4), "below_fit_floor": bool(top[i] < floor[i]),
            "nearest_with_outside_genres": gpred[i],
            "nearest_is_outside_genre": bool(gpred[i] in outside and ggap[i] >= margin),
            "spellings_only_placed": spred[i] or "",
            "spellings_only_agrees": "" if placed[i] is None or spred[i] is None else bool(spred[i] == placed[i]),
            "common_features_share": round(float(comm[i] / gap[i]), 3) if gap[i] > 0 else "",
            "rests_on_common_features": bool(gap[i] > 0 and comm[i] > 0.5 * gap[i]),
            "compositions_top5": SEP.join(f"CTH {clabs[j]}" for j in ctop[i]),
            "compositions_top5_similarity": SEP.join(f"{SCo[i, j]:.4f}" for j in ctop[i]),
            "manuscripts_top5": SEP.join(t for t, _ in mss_top[i][:5]),
            "manuscripts_top5_similarity": SEP.join(f"{s:.4f}" for _, s in mss_top[i][:5]),
            "manuscripts_top20": SEP.join(t for t, _ in mss_top[i]),
            "join_candidates": SEP.join(jf.candidate_txtid),
            **{"words_" + re.sub(r"\W+", "_", c.lower()).strip("_"): round(float(cats.get(c, 0.0)), 3) for c in CATEGORIES}}
    F = []
    for t, s in scope.iterrows():
        F.append({"txtid": t, "filed_under_cth": s.cth, "laroche_bin": s.bin, "is_ebo": t.startswith("EBo"),
                  "n_words_analysed": int(s.n_analysed), "n_words_legible": int(s.n_legible),
                  "tlhdig_url": tlhdig_url(t, s.cth), "konkordanz_url": konkordanz_url(t),
                  **rows.get(t, {"status": "too_small"})})
    F = pd.DataFrame(F)
    natural = lambda t: [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", t)]
    bin_order = {b: i for i, b in enumerate(list(dict.fromkeys(BINS.values())) + ["EBo filed under other CTH numbers"])}
    F = F.iloc[sorted(range(len(F)), key=lambda i: (bin_order[F.laroche_bin[i]], natural(F.txtid[i])))]
    F.to_csv(f"{a.out}/fragments.csv", index=False)
    J.to_csv(f"{a.out}/join_candidates.csv", index=False)
    J.to_csv(f"{a.out}/join_candidates.csv.gz", index=False)        # the copy kept in git

    # traditions and compositions used
    T = pd.DataFrame([{"tradition": l, "cth": " ".join(str(c) for c in GROUPSETS[rep["groups"]][l]),
                       "reference_manuscripts": int((y == l).sum()), "defining_study": STUDIES[l]} for l in labs])
    T.to_csv(f"{a.out}/traditions.csv", index=False)
    pd.DataFrame({"cth": clabs, "manuscripts": n_mss,
                  "tradition": [trad_of.get(c, res_of.get(c, "")) for c in clabs]}).to_csv(
        f"{a.out}/compositions.csv", index=False)

    summary = {"texts_in_scope": int(len(F)), "with_results": int(len(frags)),
               "status": F.status.value_counts().to_dict(),
               "by_bin": F.assign(join=F.join_candidates.fillna("") != "").groupby("laroche_bin", sort=False).agg(
                   texts=("txtid", "size"), too_small=("status", lambda s: int((s == "too_small").sum())),
                   below_margin=("status", lambda s: int((s == "below_margin").sum())),
                   placed=("status", lambda s: int((s == "placed").sum())),
                   with_join_candidates=("join", "sum")).astype(int).to_dict(orient="index"),
               "fragments_with_join_candidates_by_size": F[F.status != "too_small"].assign(
                   join=lambda d: d.join_candidates.fillna("") != "",
                   size=lambda d: pd.cut(d.n_words_analysed, [4, 9, 16, 39, 10**6],
                                         labels=["5-9", "10-16", "17-39", "40+"])).groupby(
                   "size", observed=True).join.agg(["size", "sum"]).astype(int).to_dict(orient="index"),
               "placed_by_tradition": F.placed_tradition.replace("", np.nan).dropna().value_counts().to_dict(),
               "fragments_with_join_candidates": int((F.join_candidates.fillna("") != "").sum()),
               "join_candidate_pairs": int(J.passes_join_checks.sum()),
               "margin": margin, "precision_above_margin": rep["E2_abstention"]["precision_above_margin"],
               "loo_accuracy": rep["E1_historical"]["both"]["acc"], "loo_majority": rep["E1_historical"]["both"]["majority"], "reference_manuscripts": int(len(ref)), "manuscript_pool": int(len(pool)),
               "compositions": int(len(clabs))}
    json.dump(summary, open(f"{a.out}/summary.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(summary, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
