"""Placements per residual bin, from the release table (make_release.py): for each of Laroche's
residual bins (and the unclaimed rituals of CTH 390-469 and the EBo texts filed elsewhere) the
number of manuscripts, how many are too small, below the margin or placed, and where the placed
ones go, by tradition and by cultural sphere: Kizzuwatna and the Hurrian groups, the Anatolian
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
                  "by_tradition": {k: int(v) for k, v in to.items()}}
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps({b: {k: v for k, v in r.items() if k != "by_tradition"} for b, r in res.items()}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
