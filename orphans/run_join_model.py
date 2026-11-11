"""J1 Join model: can the closest-manuscript ranking be turned into a ranking of joins?

The similarity ranking (run_join_candidates.py, make_release.py) finds duplicates and parallels: the
Konkordanz partner ranks in the top 20 for 165 of 212 duplicates but for 3 of 11 suspected joins
(run_known_joins.py). Two pieces of one tablet share context (composition, tradition, scribe,
find spot) but usually not text. This experiment learns how to weigh those signals.

Known joins. TLHdig 0.3 stores 1,623 joined texts (ids ending in "+") and marks on every line the
pieces it is preserved on ({€1}, {€2+1} ...). qtm.pieces splits them back into their pieces (lines
across a join are left out). Every pair of pieces of one text with 5+ analysed words each is a
known join.

Task. Each piece is a query. The pool is every TLHdig text with 5+ analysed words, the joined texts
replaced by their pieces. Step 1 takes the K nearest units in the main model's space (word forms +
sign n-grams, tf-idf fitted on the reference traditions). Step 2 re-ranks them with a logistic
regression over pair features:
  cosine            similarity in the main model's space (text and context together)
  tradition_cos     cosine of the two units' similarity profiles over the 10 reference traditions
  composition_cos   the same over the compositions (centroids of every CTH number outside the residual
                    bins, from texts that are not joins, so no piece is part of a centroid)
  word_overlap      Jaccard overlap of content words
  phrase_overlap    Jaccard overlap of two-word phrases (high for duplicates)
  same_spelling     share of shared words spelled identically (0 when no word is shared)
  scribal_distance  mean absolute difference of the E7 orthographic indices (qtm.layers.indices)
  column_overlap    Jaccard overlap of the preserved sides/columns (Vs. I, Rs. IV ...)
  same_series       same publication series and volume (e.g. KBo 41)
  same_find_series  same excavation-number series (e.g. ".../c", "Bo ..."; Konkordanz find number)
  log_words_a/b     size of the two units
Two more checks are reported but not fitted (see FLAGS): the same find spot in the Konkordanz, and
incompatible script dates. For known joins the Konkordanz often derives these from the join itself.
Labels: 1 for the pieces of the same joined text, 0 for every other candidate (duplicates and
parallels among them). Weights are fitted on standardised features; evaluation is grouped by the
CTH number of the query (5 folds), so the model is always tested on compositions it was not fitted
on. Reported: recall@1/5/20 of the partner for the similarity ranking and for the model, the
weights with 95% intervals (bootstrap over CTH numbers), and the same for the 11 suspected joins
and 212 duplicates of the Konkordanz (labels/konkordanz_joins_duplicates.csv), never seen in fitting.

Konkordanz metadata (find number, find spot, date) is read from the cached CTH pages of qtm.konkordanz
(data/konkordanz/hetkonk_c<CTH>.html; --fetch downloads the missing ones, one per second).
Not used, because they carry the join itself: the CTH number (pieces of a TLHdig join share it by
construction), the Konkordanz's manuscript letters and its notes.

Usage: python run_join_model.py data/tokens.csv --run results/tlhdig03_literature \
          --xml data/TLHbasisONLINE25_1_ZENODO_Beta_03 --cache data/konkordanz --out results/tlhdig03_literature/joins
"""
import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import html
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler, normalize

from qtm.assign import centroids, scores
from qtm.corpus import load, signs
from qtm.features import tokens
from qtm.groups import ABSTRACT, GROUPSETS, HISTORICAL, RESIDUE, is_orphan, label_map
from qtm.konkordanz import fetch
from qtm.layers import INDICES, indices
from qtm.pieces import headers, piece_of
from run_experiments import MIN_WORDS, SEED, featurise
from run_join_candidates import SKIP, norm_sp, same_spelling

FEATURES = ["cosine", "tradition_cos", "composition_cos", "word_overlap", "phrase_overlap", "same_spelling",
            "scribal_distance", "column_overlap", "same_series", "same_find_series", "log_words_a", "log_words_b"]
# Konkordanz find spot and date are reported for each candidate but not fitted: for pieces of known joins
# the Konkordanz often derives them from the join itself ("T.I *: Fundort bestimmt durch Join"), and the
# extra pieces of a join have no row of their own, so in the training data they would carry the answer.
FLAGS = ["same_findspot", "date_conflict"]
MIN = 5
SERIES = re.compile(r"^([A-Za-zÄÖÜ]+(?:\s?\d+_\d+)?)\s*(\d+)?")


# ---------- units: texts, with the joined texts replaced by their pieces
def units(tokens_csv, hdr):
    raw = pd.read_csv(tokens_csv, low_memory=False, dtype=str)
    raw = raw.dropna(subset=["txtid"])
    joined = raw.txtid.str.endswith("+")
    raw["piece"] = np.where(joined, raw.lnr.map(piece_of), 0)
    raw = raw[~joined | raw.piece.notna()].copy()
    joined = raw.txtid.str.endswith("+")
    raw["unit"] = np.where(joined, raw.txtid + " #" + raw.piece.astype(float).astype("Int64").astype(str), raw.txtid)
    w = raw.dropna(subset=["word"])
    U = w.groupby("unit", sort=False).agg(txtid=("txtid", "first"), cth_number=("cth_number", "first"),
                                          piece=("piece", "first"), words=("word", list), translits=("translit", list),
                                          langs=("lang", list), lnrs=("lnr", list)).reset_index()
    U["signs"] = U.translits.map(lambda ts: [signs(t) for t in ts])
    U["n_words"] = U.words.str.len()
    U = U[U.n_words >= MIN].reset_index(drop=True)
    U["is_piece"] = U.unit.str.contains(" #")
    pub = hdr.set_index(["txtid", "piece"])
    U["publication"] = [pub.publication.get((t, int(p)), "") if ip else t for t, p, ip in zip(U.txtid, U.piece, U.is_piece)]
    U["inventory"] = [pub.inventory.get((t, int(p) if ip else 1), "") for t, p, ip in zip(U.txtid, U.piece, U.is_piece)]
    return U


def columns(lnrs):
    out = set()
    for l in lnrs:
        l = PIECE_RE.sub("", str(l)).strip()
        m = re.match(r"(Vs\.|Rs\.|lk\. Rd\.|o\. Rd\.|u\. Rd\.|Rd\.|Obv\.|Rev\.)\s*([IVX]+)?", l)
        if m:
            out.add((m.group(1), m.group(2) or ""))
    return out


PIECE_RE = re.compile(r"\{€[\d+]+\}")


def series(publ):
    m = SERIES.match(str(publ).strip())
    return f"{m.group(1)} {m.group(2) or ''}".strip() if m else ""


def find_series(inv):
    inv = str(inv).split("+")[0].strip()
    if inv.startswith("Bo"):
        return "Bo"
    m = re.search(r"/([a-z]+)", inv)
    return m.group(1) if m else ""


# ---------- Konkordanz: find spot and date of every publication
def konkordanz_meta(cache, cths, do_fetch):
    rows = []
    for c in cths:
        f = Path(cache) / f"hetkonk_c{c}.html"
        if not f.exists():
            if not do_fetch:
                continue
            try:
                fetch(c, Path(cache))
                time.sleep(1.0)
            except Exception as e:  # a missing page leaves its pieces without metadata
                print("konkordanz", c, e)
                continue
        for tr in html.fromstring(f.read_text(encoding="utf-8", errors="replace")).iter("tr"):
            tds = tr.findall("td")
            if len(tds) >= 6 and tds[0].get("id") == "x1":           # a further piece of a join: find number only
                x3 = [" ".join(td.text_content().split()) for td in tds if td.get("id") == "x3"]
                if x3 and x3[0]:
                    rows.append({"publication": x3[0], "findspot": "", "date": "",
                                 "find_number": " ".join(tds[1].text_content().split()).lstrip("+")})
                continue
            if len(tds) < 7 or tds[0].get("id") != "y1":
                continue
            y3 = [" ".join(td.text_content().split()) for td in tds if td.get("id") == "y3"]
            y4 = [" ".join(td.text_content().split()) for td in tds if td.get("id") == "y4"]
            if len(y3) < 3:
                continue
            spot = y3[2].split(":")[0].strip()
            rows.append({"publication": y3[0], "findspot": "" if "*" in spot or spot in ("---", "") else spot, "date": y4[0] if y4 else "",
                         "find_number": " ".join(tds[0].text_content().split())})
    m = pd.DataFrame(rows)
    m = m[(m.publication != "") & (m.publication != "(publ.)")]
    return m.drop_duplicates("publication").set_index("publication") if len(m) else m


def dates(s):
    return {d for d in ("ah", "mh", "jh") if d in str(s)}


# ---------- pair features
def prep(U):
    U["content"] = [{w for w in ws if not SKIP.match(w)} for ws in U.words]
    U["spell"] = [fullest(ws, ts) for ws, ts in zip(U.words, U.translits)]
    U["bigrams"] = [{(a, b) for a, b in zip(ws, ws[1:]) if a != b and not SKIP.match(a) and not SKIP.match(b)} for ws in U.words]
    U["cols"] = U.lnrs.map(columns)
    idx = pd.DataFrame([indices(d) for _, d in U.iterrows()])[INDICES]
    U["idx"] = list(idx.to_numpy())
    U["series"] = U.publication.map(series)
    U["find_series"] = U.inventory.map(find_series)


def fullest(ws, ts):
    """Each content word's spelling; of several, the one with fewest signs missing (∅, version C)."""
    sp = {}
    for w, t in zip(ws, ts):
        if not SKIP.match(w):
            t = norm_sp(t)
            if w not in sp or t.count("∅") < sp[w].count("∅"):
                sp[w] = t
    return sp


def jacc(a, b):
    return len(a & b) / len(a | b) if a or b else 0.0


def pair(a, b, cos, tcos, ccos, meta):
    shared = a.content & b.content
    same = sum(same_spelling(a.spell[w], b.spell[w]) for w in shared)
    d = np.abs(a.idx - b.idx)
    ma, mb = meta.get(a.publication), meta.get(b.publication)
    fa, fb = (ma or {}).get("findspot", ""), (mb or {}).get("findspot", "")
    da, db = dates((ma or {}).get("date", "")), dates((mb or {}).get("date", ""))
    return [cos, tcos, ccos, jacc(a.content, b.content), jacc(a.bigrams, b.bigrams),
            same / len(shared) if shared else 0.0, float(np.nanmean(d)) if np.isfinite(d).any() else 0.5,
            jacc(a.cols, b.cols),
            float(a.series != "" and a.series == b.series), float(a.find_series != "" and a.find_series == b.find_series),
            np.log(a.n_words), np.log(b.n_words),
            float(fa != "" and fa == fb), float(bool(da) and bool(db) and not (da & db))]


def candidates(sim, comp, k, self_i):
    """The k nearest units by text similarity and the k nearest by composition profile (joins share
    the composition more than the text)."""
    comp = comp.copy()
    comp[self_i] = -np.inf
    return np.union1d(np.argpartition(-sim, k)[:k], np.argpartition(-comp, k)[:k])


def recall(ranks, ks=(1, 5, 20)):
    r = np.asarray(ranks, dtype=float)
    return {f"recall@{k}": round(float(np.mean(r <= k)), 3) for k in ks} | {"queries": int(len(r)),
            "median_rank": float(np.nanmedian(np.where(np.isfinite(r), r, np.nan))) if np.isfinite(r).any() else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--xml", required=True)
    ap.add_argument("--cache", default="data/konkordanz")
    ap.add_argument("--fetch", action="store_true", help="download missing Konkordanz CTH pages")
    ap.add_argument("--k", type=int, default=200)
    ap.add_argument("--known", default="labels/konkordanz_joins_duplicates.csv")
    ap.add_argument("--meta-snapshot", default="labels/konkordanz_meta.csv")
    ap.add_argument("--refresh-konkordanz", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rep = json.load(open(f"{a.run}/report.json"))
    trad_of = label_map(GROUPSETS[rep["groups"]])

    hdr = headers(a.xml)
    U = units(a.tokens, hdr)
    # Konkordanz metadata: the committed snapshot (labels/konkordanz_meta.csv), or rebuilt from the cached
    # CTH pages with --refresh-konkordanz (--fetch downloads missing pages first)
    snap = Path(a.meta_snapshot)
    if snap.exists() and not a.refresh_konkordanz:
        meta = pd.read_csv(snap, dtype=str, keep_default_na=False).set_index("publication")
    else:
        meta = konkordanz_meta(a.cache, sorted(U.cth_number.dropna().unique(), key=lambda c: (len(c), c)), a.fetch)
        meta.reset_index().to_csv(snap, index=False)
        Path(str(snap).replace(".csv", ".source.txt")).write_text(
            "Parsed from https://hethport.net/hetkonk/hetkonk_abfrage.php?c=<CTH> for every CTH number of TLHdig 0.3, "
            f"pages accessed {sorted({p.read_text().strip() for p in Path(a.cache).glob('*.accessed')})}\n")
    meta = meta.to_dict(orient="index") if len(meta) else {}
    # a piece is found in the Konkordanz under its own publication; a text under its id without "+"
    U["publication"] = [p if p in meta else p.rstrip("+").strip() for p in U.publication]
    U["inventory"] = [meta[p]["find_number"] if p in meta and meta[p]["find_number"] else i
                      for p, i in zip(U.publication, U.inventory)]
    # a few pieces of TLHdig joins are also edited as texts of their own: leave those copies out
    piece_pubs = set(U[U.is_piece].publication)
    U = U[U.is_piece | ~U.txtid.isin(piece_pubs)].reset_index(drop=True)
    prep(U)
    print(f"{len(U)} units, {U.is_piece.sum()} pieces; Konkordanz rows {len(meta)}; "
          f"units with Konkordanz metadata {U.publication.isin(meta.keys()).sum()}")

    # main model space, exactly as in the experiments
    allcths = sorted({str(c) for gs in (HISTORICAL, ABSTRACT, GROUPSETS[rep["groups"]], RESIDUE)
                      for cs in gs.values() for c in cs} | {"470"})
    exp = load(a.tokens, cths=allcths)
    exp = exp[[not is_orphan(t, c) for t, c in zip(exp.txtid, exp.cth_number)]]
    ref = exp[exp.cth_number.isin(trad_of) & (exp.n_words >= MIN_WORDS)].reset_index(drop=True)
    vec, X = featurise(ref, "both")
    C, labs = centroids(X, ref.cth_number.map(trad_of).to_numpy())
    XU = normalize(vec.transform([tokens(r, "both") for _, r in U.iterrows()]))
    T = normalize(scores(XU, C))                                       # tradition profiles
    bins = {"470", "500", "670", "832"}
    cm = (~U.is_piece & ~U.cth_number.isin(bins)
          & np.array([not is_orphan(t, c) for t, c in zip(U.txtid, U.cth_number)])).to_numpy()
    CC, _ = centroids(XU[cm], U.cth_number[cm].to_numpy())
    CP = normalize(scores(XU, CC))                                     # composition profiles

    R = list(U.itertuples(index=False))                               # fast row access
    # queries: pieces whose joined text has another piece in the pool
    npieces = U[U.is_piece].groupby("txtid").size()
    Q = np.flatnonzero(U.is_piece & U.txtid.map(npieces).fillna(0).ge(2))
    rows, base_ranks = [], []
    for s0 in range(0, len(Q), 300):
        qs = Q[s0:s0 + 300]
        S = np.asarray((XU[qs] @ XU.T).todense())
        S[np.arange(len(qs)), qs] = -np.inf
        for r, qi in enumerate(qs):
            s = S[r]
            partners = np.flatnonzero((U.txtid.to_numpy() == U.txtid[qi]) & (np.arange(len(U)) != qi))
            base_ranks.append(int((s > s[partners].max()).sum()) + 1)
            cand = candidates(s, CP[qi] @ CP.T, a.k, qi)
            for ci in cand:
                rows.append([qi, ci, int(U.txtid[ci] == U.txtid[qi]),
                             *pair(R[qi], R[ci], float(s[ci]), float(T[qi] @ T[ci]), float(CP[qi] @ CP[ci]), meta)])
    P = pd.DataFrame(rows, columns=["q", "c", "label", *FEATURES, *FLAGS])
    P["group"] = U.cth_number.to_numpy()[P.q]
    print(f"{len(Q)} query pieces, {len(P)} pairs, {P.label.sum()} partner pairs in the top {a.k}")

    # grouped cross-validation: compositions of the test fold are never seen in fitting
    P["prob"] = np.nan
    for tr, te in GroupKFold(5).split(P, P.label, P.group):
        sc = StandardScaler().fit(P.loc[P.index[tr], FEATURES])
        m = LogisticRegression(max_iter=2000).fit(sc.transform(P.loc[P.index[tr], FEATURES]), P.label.iloc[tr])
        P.loc[P.index[te], "prob"] = m.predict_proba(sc.transform(P.loc[P.index[te], FEATURES]))[:, 1]

    def ranks_by(col):
        out = []
        for q, g in P.groupby("q"):
            g = g.sort_values(col, ascending=False).reset_index(drop=True)
            hit = np.flatnonzero(g.label.to_numpy() == 1)
            out.append(hit[0] + 1 if len(hit) else np.inf)
        return out
    res = {"units": int(len(U)), "pieces": int(U.is_piece.sum()), "query_pieces": int(len(Q)),
           "joined_texts": int(U.loc[Q, "txtid"].nunique()), "k": a.k, "pairs": int(len(P)),
           "partner_in_top_k": round(float(P.groupby("q").label.max().mean()), 3),
           "similarity_ranking": recall(base_ranks),
           "model_reranking": recall(ranks_by("prob") + [np.inf] * (len(Q) - P.q.nunique()))}

    # weights: fit on everything; 95% intervals from a bootstrap over CTH numbers
    sc = StandardScaler().fit(P[FEATURES])
    full = LogisticRegression(max_iter=2000).fit(sc.transform(P[FEATURES]), P.label)
    rng = np.random.default_rng(SEED)
    groups = P.group.unique()
    boot = []
    for _ in range(200):
        pick = rng.choice(groups, len(groups))
        B = pd.concat([P[P.group == g] for g in pick])
        if B.label.nunique() < 2:
            continue
        sb = StandardScaler().fit(B[FEATURES])
        boot.append(LogisticRegression(max_iter=2000).fit(sb.transform(B[FEATURES]), B.label).coef_[0])
    boot = np.array(boot)
    W = pd.DataFrame({"feature": FEATURES, "weight": full.coef_[0].round(3),
                      "ci_low": np.percentile(boot, 2.5, axis=0).round(3), "ci_high": np.percentile(boot, 97.5, axis=0).round(3),
                      "mean_joins": P[P.label == 1][FEATURES].mean().round(3).to_numpy(),
                      "mean_other": P[P.label == 0][FEATURES].mean().round(3).to_numpy()})
    W.to_csv(out / "J1_weights.csv", index=False)
    res["flags"] = {f: {"joins": round(float(P[P.label == 1][f].mean()), 4), "other": round(float(P[P.label == 0][f].mean()), 4)}
                    for f in FLAGS}
    res["weights"] = W.set_index("feature")[["weight", "ci_low", "ci_high"]].to_dict(orient="index")

    # outside check: Konkordanz joins and duplicates (pairs of whole TLHdig texts)
    if Path(a.known).exists():
        K = pd.read_csv(a.known)
        pos = {u: i for i, u in enumerate(U.unit)}
        model_rows = {}
        for rel, g in K.groupby("relation"):
            sim_r, mod_r = [], []
            for _, k in g.iterrows():
                qi, pi = pos.get(k.fragment), pos.get(k.partner)
                if qi is None or pi is None:
                    continue
                s = np.asarray((XU[qi] @ XU.T).todense()).ravel()
                s[qi] = -np.inf
                sim_r.append(int((s > s[pi]).sum()) + 1)
                cand = candidates(s, CP[qi] @ CP.T, a.k, qi)
                if pi not in cand:
                    mod_r.append(np.inf)
                    continue
                F = np.array([pair(R[qi], R[ci], float(s[ci]), float(T[qi] @ T[ci]), float(CP[qi] @ CP[ci]), meta)
                              for ci in cand])
                p = full.predict_proba(sc.transform(pd.DataFrame(F[:, :len(FEATURES)], columns=FEATURES)))[:, 1]
                mod_r.append(int((p > p[list(cand).index(pi)]).sum()) + 1)
            model_rows[rel] = {"similarity_ranking": recall(sim_r), "model_reranking": recall(mod_r)}
        res["konkordanz"] = model_rows

    json.dump(res, open(out / "J1_report.json", "w"), indent=1, ensure_ascii=False, default=float)
    print(json.dumps(res, indent=1, ensure_ascii=False, default=float))


if __name__ == "__main__":
    main()
