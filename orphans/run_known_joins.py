"""Known joins and duplicates from the Konkordanz, checked against the closest-manuscript ranking.

For every CTH page cached by qtm.konkordanz (data/konkordanz/hetkonk_c<CTH>.html) the notes of each
fragment row are searched for statements that tie it to another piece:
  join       "vermutet Join mit X", "(erwägt) indirekten Join mit X", "(+) X", "Join mit X"
             (a suspected, indirect or proposed join with a piece TLHdig edits separately)
  duplicate  "Dupl. X" (a duplicate manuscript of the same composition)
Each piece named in the statement is matched to a TLHdig text (a piece of a join "KBo 17.54+" maps
to that text). Pairs whose two pieces are the same TLHdig text (the join is already made in
TLHdig) are left out, as are texts under 5 words.

For each remaining pair (fragment A, partner B) we rank every TLHdig text of 5+ words by
similarity to A in the main model's space, exactly as run_join_candidates.py does, and report
B's rank and the three join checks (half the words, same spellings, a shared phrase).
The question is how often the method puts the known partner among A's closest manuscripts.

Writes the relations to labels/konkordanz_joins_duplicates.csv and the ranks to --out.

Usage: python run_known_joins.py data/tokens.csv --run results/tlhdig03_literature \
          --cache data/konkordanz --out results/tlhdig03_literature/known_joins
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import html
from sklearn.preprocessing import normalize

from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, is_orphan, label_map
from run_experiments import MIN_WORDS, featurise
from run_join_candidates import SKIP, norm_sp

SIGLUM = re.compile(r"\b(KBo|KUB|IBoT|ABoT|VBoT|HT|FHG|FHL|KpT|CHDS|HFAC|AT|BoTU|KuSa|DBH|Bo)\s?(\d+(?:/[a-z\d]+)?(?:\.\d+[a-z]?)?)")
RELATIONS = [
    ("join", re.compile(r"vermutet(?:e)?\s+Join\s+mit|indirekte[nr]?\s+Join\s+(?:mit|zu)|\(\+\)\??|Join\s+mit")),
    ("duplicate", re.compile(r"Dupl\.(?:/par\.)?")),
]


def rows(page):
    for tr in html.fromstring(page).iter("tr"):
        tds = tr.findall("td")
        if len(tds) < 7 or tds[0].get("id") != "y1":
            continue
        y3 = [td for td in tds if td.get("id") == "y3"]
        yr = [td for td in tds if td.get("id") == "yr"]
        if y3 and yr:
            # the notes cell repeats itself after "ↂ"; keep the first copy
            yield (" ".join(y3[0].text_content().split()), " ".join(y3[1].text_content().split()) if len(y3) > 1 else "",
                   " ".join(yr[0].text_content().split()).split("ↂ")[0])


def statements(note):
    """(relation, partner sigla, clause) for each join or duplicate statement in one note."""
    for rel, pat in RELATIONS:
        for m in pat.finditer(note):
            clause = re.split(r";|\s-\s|Dupl\.|Join", note[m.end():], maxsplit=1)[0][:160]
            # "(= 410/t)" gives the find number of the same piece: keep the publication only
            sig = [" ".join(s) for s in SIGLUM.findall(re.sub(r"\(=[^)]*\)", "", clause))]
            if sig:
                yield rel, sig, (note[m.start():m.end()] + clause).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--cache", default="data/konkordanz")
    ap.add_argument("--min-words", type=int, default=5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--labels", default="labels/konkordanz_joins_duplicates.csv")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rep = json.load(open(f"{a.run}/report.json"))
    hist = label_map(GROUPSETS[rep["groups"]])
    docs = load(a.tokens)
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].reset_index(drop=True)
    pool = docs[docs.n_words >= a.min_words].reset_index(drop=True)

    # piece -> TLHdig text ("KBo 17.54+" holds the piece KBo 17.54)
    piece = {}
    for t in docs.txtid:
        for p in str(t).split("+"):
            if p.strip():
                piece.setdefault(" ".join(p.split()), t)

    pairs, pages = [], sorted(Path(a.cache).glob("hetkonk_c*.html"))
    for f in pages:
        for pub, cth_full, note in rows(f.read_text(encoding="utf-8", errors="replace")):
            A = piece.get(pub.rstrip("+").strip())
            if not A:
                continue
            for rel, sig, clause in statements(note):
                for s in sig:
                    B = piece.get(s)
                    if B and B != A:
                        pairs.append({"relation": rel, "fragment": A, "konkordanz_row": pub, "konkordanz_cth": cth_full,
                                      "partner": B, "partner_named_as": s, "statement": clause,
                                      "page": f.name})
    P = pd.DataFrame(pairs).drop_duplicates(["relation", "fragment", "partner"])
    # the relations themselves, as labels other scripts can read (e.g. the Zenodo dataset's recall check)
    accessed = sorted({(Path(a.cache) / f.replace(".html", ".accessed")).read_text().strip()
                       for f in P.page if (Path(a.cache) / f.replace(".html", ".accessed")).exists()})
    P.assign(accessed=", ".join(accessed)).to_csv(a.labels, index=False)

    vec, _ = featurise(ref, "both")
    X = normalize(vec.transform([tokens(r, "both") for _, r in pool.iterrows()]))
    pos = {t: i for i, t in enumerate(pool.txtid)}
    res = []
    for _, p in P.iterrows():
        if p.fragment not in pos or p.partner not in pos:
            continue
        i, j = pos[p.fragment], pos[p.partner]
        sim = np.asarray((X @ X[i].T).todense()).ravel()
        sim[i] = -np.inf
        rank = int((sim > sim[j]).sum()) + 1
        A, B = pool.iloc[i], pool.iloc[j]
        fw = [(w, norm_sp(t)) for w, t in zip(A.words, A.translits) if not SKIP.match(w)]
        cols, seen = [], set()
        for w, t in fw:
            if w not in seen:
                seen.add(w)
                cols.append((w, t))
        pairs_ = {(w1, w2) for (w1, _), (w2, _) in zip(fw, fw[1:]) if w1 != w2}
        spell = {}
        for w, t in zip(B.words, B.translits):
            spell.setdefault(w, set()).add(norm_sp(t))
        cells = "".join("S" if w in spell and t in spell[w] else ("W" if w in spell else ".") for w, t in cols)
        shared = sum(c != "." for c in cells)
        phrase = bool(pairs_ & set(zip(B.words, B.words[1:])))
        res.append({**p.to_dict(), "fragment_cth": A.cth_number, "partner_cth": B.cth_number,
                    "fragment_words": int(A.n_words), "partner_words": int(B.n_words),
                    "similarity": round(float(sim[j]), 4), "rank": rank, "pool": int(len(pool) - 1),
                    "barcode": cells, "shared_words": shared,
                    "passes_join_checks": bool(shared >= len(cols) / 2 and shared > 0 and "W" not in cells and phrase)})
    R = pd.DataFrame(res).sort_values(["relation", "rank"])
    R.to_csv(out / "known_joins.csv", index=False)
    summary = {"pages": [f.stem.replace("hetkonk_c", "") for f in pages], "statements_matched": int(len(P)),
               "pool": int(len(pool) - 1)}
    for rel, g in R.groupby("relation"):
        summary[rel] = {"pairs": int(len(g)), "median_rank": float(g["rank"].median()),
                        "top1": int((g["rank"] <= 1).sum()), "top5": int((g["rank"] <= 5).sum()),
                        "top20": int((g["rank"] <= 20).sum()), "top100": int((g["rank"] <= 100).sum())}
    json.dump(summary, open(out / "known_joins.json", "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print(R.head(40)[["relation", "fragment", "partner", "rank", "similarity", "barcode", "passes_join_checks"]].to_string())


if __name__ == "__main__":
    main()
