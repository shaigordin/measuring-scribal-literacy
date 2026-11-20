"""Join candidates for one orphan: its nearest manuscripts in the whole release, checked word by word.

Step 1 ranks every manuscript of the TLHdig release with at least --min-words analysed words
(reference, residue, orphans and fragment collections alike) by similarity to the fragment, in the
main model's space (word forms + sign n-grams, vocabulary and idf fitted on the reference).
Step 2 draws a "join barcode" for the top --top: one cell per content word of the fragment, in
line order, marking whether the candidate has the word written the same way (same spelling),
the word written differently, or not at all. It also checks the fragment's two-word phrases
(adjacent words, e.g. NINDA takarmun + paršiya) in the candidate.
Step 3 flags candidates that pass three checks fixed in advance: (a) at least half of the
fragment's content words, (b) every shared word spelled exactly as in the fragment (one scribal
habit), (c) at least one shared two-word phrase. The barcode cannot tell a join from a duplicate
copy; the photographs and the Konkordanz data (find spot, script) are the next step.

Usage: python run_join_candidates.py data/tokens.csv --run results/tlhdig03_literature --txtid "EBo 133" \
          --out results/tlhdig03_literature/case
"""
import argparse
import json
import re

import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize

from qtm.corpus import load
from qtm.features import tokens
from qtm.groups import GROUPSETS, RESIDUE, label_map, is_orphan
from run_experiments import MIN_WORDS, featurise

SKIP = re.compile(r"^(\d+|~.*|x)$")


def norm_sp(t):
    """Spelling as written, editorial marks removed (breaks, half brackets, primes)."""
    return re.sub(r"[\[\]⸢⸣()?!<>«»#*]", "", str(t)).strip()


def same_spelling(a, b):
    """Spellings agree on every sign both pieces preserve (∅ = not on the tablet, see qtm.variants)."""
    if "∅" not in a + b:
        return a == b
    sa, sb = re.split(r"[-.\s{}]+", a), re.split(r"[-.\s{}]+", b)
    return len(sa) == len(sb) and all(x == y or "∅" in (x, y) for x, y in zip(sa, sb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--run", required=True)
    ap.add_argument("--txtid", default="EBo 133")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--min-words", type=int, default=5)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    hist = label_map(GROUPSETS[rep["groups"]])
    res = {str(c): name for name, cs in RESIDUE.items() for c in cs}
    docs = load(a.tokens)
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    ref = docs[~docs.orphan & docs.cth_number.isin(hist) & (docs.n_words >= MIN_WORDS)].reset_index(drop=True)
    pool = docs[(docs.n_words >= a.min_words) & (docs.txtid != a.txtid)].reset_index(drop=True)
    frag = docs[docs.txtid == a.txtid].iloc[0]

    vec, _ = featurise(ref, "both")
    x = normalize(vec.transform([tokens(frag, "both")]))
    P = normalize(vec.transform([tokens(r, "both") for _, r in pool.iterrows()]))
    sim = np.asarray((P @ x.T).todense()).ravel()

    fw = [(w, norm_sp(t)) for w, t in zip(frag.words, frag.translits) if not SKIP.match(w)]
    cols, seen = [], set()
    for w, t in sorted(fw, key=lambda p: p[1].count("∅")):  # each word's most complete spelling
        if w not in seen:
            seen.add(w)
            cols.append((w, t))
    cols.sort(key=lambda c: [w for w, _ in fw].index(c[0]))
    pairs = sorted({(w1, w2) for (w1, _), (w2, _) in zip(fw, fw[1:]) if w1 != w2})

    out = {"txtid": a.txtid, "pool_size": int(len(pool)), "min_words": a.min_words,
           "columns": [{"word": w, "spelling": t} for w, t in cols],
           "phrases": [list(p) for p in pairs], "candidates": []}
    for rank, i in enumerate(np.argsort(-sim)[:a.top], 1):
        d = pool.iloc[i]
        spell = {}
        for w, t in zip(d.words, d.translits):
            spell.setdefault(w, set()).add(norm_sp(t))
        cells = "".join("S" if w in spell and any(same_spelling(t, u) for u in spell[w]) else ("W" if w in spell else ".")
                        for w, t in cols)
        seq = list(d.words)
        bigr = set(zip(seq, seq[1:]))
        shared_ph = [list(p) for p in pairs if p in bigr]
        n_shared = sum(c != "." for c in cells)
        checks = {"half_the_words": n_shared >= len(cols) / 2,
                  "same_spellings": n_shared > 0 and "W" not in cells,
                  "shared_phrase": bool(shared_ph)}
        c = d.cth_number
        out["candidates"].append({
            "rank": rank, "txtid": d.txtid, "cth": c,
            "group": hist.get(c, res.get(c, "orphan" if d.orphan else "")),
            "n_words": int(d.n_words), "similarity": round(float(sim[i]), 4),
            "barcode": cells, "shared_words": n_shared, "different_spellings": [
                {"word": w, "fragment": t, "candidate": sorted(spell[w])} for (w, t), ch in zip(cols, cells) if ch == "W"],
            "shared_phrases": shared_ph, "checks": checks, "flagged": all(checks.values())})
    fn = f"{a.out}/joins_{a.txtid.replace(' ', '_').replace('.', '_')}.json"
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False)
    for r in out["candidates"]:
        print(r["rank"], r["txtid"], r["cth"], r["group"], r["n_words"], r["similarity"], r["barcode"],
              r["shared_phrases"], "FLAG" if r["flagged"] else "", r["different_spellings"][:2])
    print([c["word"] for c in out["columns"]], out["phrases"])


if __name__ == "__main__":
    main()
