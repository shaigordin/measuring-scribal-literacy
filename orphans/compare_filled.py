"""Compare the main version C results with the side check on filled analyses (run_filled.sh)."""
import argparse
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default="results/tlhdig03_literature_C")
    ap.add_argument("--filled", default="results/tlhdig03_literature_C_filled")
    ap.add_argument("--fill", default="data/tokens_marks_filled.csv")
    a = ap.parse_args()
    M, F = Path(a.main), Path(a.filled)
    out = {}
    T = pd.read_csv(a.fill, dtype=str, keep_default_na=False, usecols=["wc_rule"])
    out["filled_words"] = {"tlhdig_same_spelling": int((T.wc_rule == "filled_tlhdig").sum()),
                           "ediana": int((T.wc_rule == "filled_ediana").sum())}
    rm, rf = (json.load(open(d / "report.json")) for d in (M, F))
    out["accuracy"] = {"main": rm["E1_historical"]["both"]["acc"], "filled": rf["E1_historical"]["both"]["acc"]}
    out["margin"] = {"main": rm["E2_abstention"]["margin"], "filled": rf["E2_abstention"]["margin"]}
    out["orphans_scored"] = {"main": rm["corpus"]["orphans_used"], "filled": rf["corpus"]["orphans_used"]}
    out["orphans_placed"] = {"main": rm["E5_orphans"]["assigned"], "filled": rf["E5_orphans"]["assigned"]}
    pm, pf = (json.load(open(d / "R1_spellings_only.json"))["runs"]["A_analysed_only"]["per_tradition"] for d in (M, F))
    bm, bf = rm["E5_orphans"]["by_tradition"], rf["E5_orphans"]["by_tradition"]
    out["by_tradition"] = {t: {"reference_main": pm[t]["n"], "reference_filled": pf.get(t, {}).get("n"),
                               "loo_main": pm[t]["loo_acc"], "loo_filled": pf.get(t, {}).get("loo_acc"),
                               "orphans_main": bm.get(t, 0), "orphans_filled": bf.get(t, 0)} for t in pm}
    em, ef = (json.load(open(d / "E10_report.json"))["E10a"] for d in (M, F))
    out["compositions_recovered"] = {"main": f"{em['compositions_correct']}/{em['compositions']}",
                                     "filled": f"{ef['compositions_correct']}/{ef['compositions']}"}
    Em, Ef = (pd.read_csv(d / "E5_orphan_placement.csv").set_index("txtid").assigned for d in (M, F))
    both = Em.dropna().index.intersection(Ef.dropna().index)
    out["orphans_placed_in_both"] = int(len(both))
    out["same_tradition_when_both"] = int((Em[both] == Ef[both]).sum())
    moved = pd.DataFrame({"main": Em[both], "filled": Ef[both]})
    out["moved"] = moved[moved.main != moved.filled].value_counts().reset_index().astype(str).values.tolist()
    out["cases"] = {}
    for t in ["KBo 44.52", "EBo 133", "KBo 41.22"]:
        f = f"case_{t.replace(' ', '_').replace('.', '_')}.json"
        cm, cf = (json.load(open(d / "case" / f)) for d in (M, F))
        out["cases"][t] = {k: {"assigned": c["assigned"], "nearest": c["nearest"], "runner_up": c["runner_up"],
                               "margin": c["margin"], "words": c["legible_words"]} for k, c in (("main", cm), ("filled", cf))}
    print(json.dumps(out, indent=1, ensure_ascii=False))
    json.dump(out, open(F / "comparison.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
