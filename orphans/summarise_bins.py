"""Placements per residual bin, from the release table (make_release.py): for each of Laroche's
residual bins (and the unclaimed rituals of CTH 390-469 and the EBo texts filed elsewhere) the
number of manuscripts, how many are too small, below the margin or placed, and where the placed
ones go, by tradition and by cultural sphere; how many have duplicate or join candidates that pass the
three match checks (make_release.py); and the same counts for the orphans (CTH 470 and EBo): Kizzuwatna and the Hurrian groups, the Anatolian
festival traditions (Hattian, Luwian, Ḫuwaššanna, Palaic), and the western and Luwian rituals.

Usage: python3 summarise_bins.py RELEASE/fragments.csv OUT.json
"""
import json
import sys

import pandas as pd

SPHERES = {"kizzuwatna_hurrian": {"Kizzuwatna rituals", "Kizzuwatna–Lower Land (Hurrian)", "Syro-Mesopotamian (Hurrian)",
                                  "Mixed (Hurrian, Syrian, Luwian)"},
           "anatolian_festivals": {"Hattian cult layer", "Luwian festivals (Ištanuwa, Lallupiya)", "Ḫuwaššanna festivals",
                                   "Palaic festivals"},
           "western_luwian_rituals": {"Arzawa / western rituals", "Luwian rituals (Puriyanni, Kuwattalla)"}}


def main(src, out):
    f = pd.read_csv(src)
    f["placed_tradition"] = f.placed_tradition.str.replace(r"Syro-Mesopotamia\b(?!n)", "Syro-Mesopotamian", regex=True)
    res = {}
    for b, g in f.groupby("laroche_bin", sort=False):
        p = g[g.status == "placed"]
        to = p.placed_tradition.value_counts()
        res[b] = {"texts": int(len(g)), **{s: int((g.status == s).sum()) for s in ("too_small", "below_margin", "placed")},
                  "median_words": float(g.n_words_legible.median()),
                  **{f"to_{k}": int(p.placed_tradition.isin(v).sum()) for k, v in SPHERES.items()},
                  "top_tradition": to.index[0] if len(to) else "", "top_tradition_n": int(to.iloc[0]) if len(to) else 0,
                  "with_match_candidates": int(g.match_candidates.notna().sum()),
                  "match_pairs": int(g.match_candidates.dropna().str.count(";").add(1).sum()),
                  "by_tradition": {k: int(v) for k, v in to.items()}}
    # the orphans (CTH 470 and every EBo text): leads for the philologist
    o = f[(f.filed_under_cth.astype(str) == "470") | f.is_ebo]
    scored = o[o.status != "too_small"]
    res["orphans"] = {"texts": int(len(o)), "scored": int(len(scored)), "placed": int((o.status == "placed").sum()),
                      "with_match_candidates": int(o.match_candidates.notna().sum()),
                      "match_pairs": int(o.match_candidates.dropna().str.count(";").add(1).sum())}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({b: {k: v for k, v in r.items() if k != "by_tradition"} for b, r in res.items() if b != "orphans"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
