"""How far the Syro-Mesopotamian (Hurrian) reference tradition rests on CTH 701 (the AZU-priest rituals).

Counts, for the version C reference set: manuscripts and words per CTH number in the tradition, how many
manuscripts per CTH mention the LÚ AZU, and in which traditions (or outside the reference) AZU appears.
Writes results/tlhdig03_literature_C/stats_syro_mesopotamia.json.
"""
import json, pandas as pd
R = "results/tlhdig03_literature_C"
ref = pd.read_csv(f"{R}/E7_indices_per_text.csv")[["txtid", "tradition"]]
tok = pd.read_csv("data/tokens_C.csv", usecols=["txtid", "cth_number", "translit"], dtype=str)
tok["azu"] = tok.translit.fillna("").str.contains(r"\bAZU\b")
sm = tok[tok.txtid.isin(ref[ref.tradition.str.startswith("Syro")].txtid)]
per_ms = sm.groupby(["cth_number", "txtid"]).azu.any().reset_index()
by_cth = {c: {"manuscripts": int(len(g)), "with_AZU": int(g.azu.sum()),
              "words": int((sm.cth_number == c).sum())} for c, g in per_ms.groupby("cth_number")}
azu_ms = tok[tok.azu].drop_duplicates("txtid").merge(ref, on="txtid", how="left")
out = {"by_cth": by_cth,
       "total_manuscripts": int(per_ms.txtid.nunique()), "total_words": int(len(sm)),
       "AZU_manuscripts_by_tradition": azu_ms.tradition.fillna("not in reference").value_counts().to_dict(),
       "AZU_outside_reference_by_cth": azu_ms[azu_ms.tradition.isna()].cth_number.value_counts().head(15).to_dict()}
json.dump(out, open(f"{R}/stats_syro_mesopotamia.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
