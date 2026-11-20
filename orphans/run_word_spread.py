"""Where one word occurs across the whole TLHdig release: manuscripts per CTH, with each CTH's
reference tradition (if any). Used for the EBo 133 deck ("where else is the takarmu bread broken").

Usage: python run_word_spread.py data/tokens.csv --word takarmun --exclude "EBo 133" \
          --out results/tlhdig03_literature/case/spread_takarmun.json
"""
import argparse, json
import pandas as pd
from qtm.groups import LITERATURE as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens"); ap.add_argument("--word", required=True)
    ap.add_argument("--exclude", default=""); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str})
    hits = raw[(raw.word == a.word) & (raw.txtid != a.exclude)]
    trad = {str(c): t for t, cs in G.items() for c in cs}
    by_cth = hits.groupby("cth_number").txtid.nunique().sort_values(ascending=False)
    rows = [{"cth": c, "manuscripts": int(n), "tradition": trad.get(c)} for c, n in by_cth.items()]
    by_trad = {}
    for r in rows:
        k = r["tradition"] or ("CTH 670 (festival fragments)" if r["cth"] == "670" else "other")
        by_trad[k] = by_trad.get(k, 0) + r["manuscripts"]
    out = {"word": a.word, "excluded": a.exclude, "manuscripts": int(hits.txtid.nunique()),
           "by_tradition": dict(sorted(by_trad.items(), key=lambda kv: -kv[1])), "by_cth": rows}
    json.dump(out, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
