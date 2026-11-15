"""Before/after the bracket fix of 2026-11-15 (qtm.tlhdig.line_start_states): key numbers of versions C and
filled, and sign counts of the token table.

    python3 compare_bracketfix.py [--before-ref 35ff293] [--old-tokens data/old/tokens_marks.csv --new-tokens data/tokens_marks.csv]

The "before" results are read from git at --before-ref (the last commit with the carry-over parser), the
"after" results from the working tree. Writes results/bracketfix_comparison.json and .md.
"""
import argparse
import io
import json
import subprocess
from pathlib import Path

import pandas as pd

RUNS = {"C": "results/tlhdig03_literature_C", "filled": "results/tlhdig03_literature_C_filled"}
CASES = ["KBo 44.52", "EBo 133", "KBo 41.22"]
LUWIAN_WEST = ["Arzawa / western rituals", "Luwian rituals (Puriyanni, Kuwattalla)",
               "Luwian festivals (Ištanuwa, Lallupiya)"]
LABEL = {"Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamian (Hurrian)"}  # published spelling


def lab(t):
    return LABEL.get(t, t)


def reader(ref):
    def read(path):
        if ref is None:
            return Path(path).read_text(encoding="utf-8")
        return subprocess.run(["git", "show", f"{ref}:orphans/{path}"], capture_output=True, check=True,
                              text=True).stdout
    return read


def key_numbers(read, run):
    J = lambda p: json.loads(read(f"{run}/{p}"))
    r, e10 = J("report.json"), J("E10_report.json")
    tun = J("tunnawiya/E10_report.json")
    out = {"accuracy": r["E1_historical"]["both"]["acc"], "margin": r["E2_abstention"]["margin"],
           "orphans_scored": r["corpus"]["orphans_used"], "orphans_placed": r["E5_orphans"]["assigned"],
           "orphans_by_tradition": {lab(k): v for k, v in r["E5_orphans"]["by_tradition"].items()},
           "compositions_recovered": f"{e10['E10a']['compositions_correct']}/{e10['E10a']['compositions']}"}
    pt = json.loads(read(f"{run}/R1_spellings_only.json"))["runs"]["A_analysed_only"]["per_tradition"]
    out["loo_by_tradition"] = {lab(t): {"n": v["n"], "loo_acc": v["loo_acc"]} for t, v in pt.items()}
    out["luwian_western_orphans"] = {lab(t): r["E5_orphans"]["by_tradition"].get(t, 0) for t in LUWIAN_WEST}
    b = e10["E10b"]
    out["ambazzi"] = {"best_fit": lab(b["table"][0]["tradition"]), "lead": b["table"][0]["lead_over_best_other"],
                      "p_vs_random": b["table"][0]["p_fits_better_than_random_rituals"],
                      "arzawa_rank": [lab(x["tradition"]) for x in b["table"]].index("Arzawa / western rituals") + 1,
                      "per_text_nearest": {lab(k): v for k, v in b["per_text_nearest"].items()},
                      "arzawa_signature_coverage": e10["E10c"]["signature_coverage"].get("Arzawa / western rituals")}
    out["cth409_best_fit"] = lab(tun["E10b"]["table"][0]["tradition"])
    out["cases"] = {}
    for t in CASES:
        c = J(f"case/case_{t.replace(' ', '_').replace('.', '_')}.json")
        out["cases"][t] = {"assigned": lab(c["assigned"]) if c["assigned"] else None, "nearest": lab(c["nearest"]),
                           "runner_up": lab(c["runner_up"]), "margin": c["margin"], "words": c["legible_words"]}
    out["_placements"] = pd.read_csv(io.StringIO(read(f"{run}/E5_orphan_placement.csv"))).set_index("txtid").assigned
    return out


def token_counts(old, new):
    cols = ["txtid", "status", "n_signs", "n_preserved", "n_damaged", "n_restored", "n_erasure", "n_added"]
    o, n = (pd.read_csv(p, usecols=cols, dtype={"status": str}, low_memory=False) for p in (old, new))
    ch = o.status.fillna("") != n.status.fillna("")
    out = {k: {"before": int(o[k].sum()), "after": int(n[k].sum())}
           for k in ["n_signs", "n_preserved", "n_damaged", "n_restored", "n_erasure", "n_added"]}
    out["words_changed"] = int(ch.sum())
    out["words"] = len(o)
    out["texts_changed"] = int(o.txtid[ch].nunique())
    out["cases"] = {t: {k: [int(o[o.txtid == t][k].sum()), int(n[n.txtid == t][k].sum())]
                        for k in ["n_preserved", "n_damaged", "n_restored"]} for t in CASES + ["KBo 27.135"]}
    return out


def md(res):
    L = ["# Bracket fix: before and after", ""]
    if "tokens" in res:
        t = res["tokens"]
        L += ["## Sign status in the token table (all TLHdig 0.3)", "", "| | before | after |", "|---|---:|---:|"]
        for k in ["n_preserved", "n_damaged", "n_restored", "n_erasure", "n_added"]:
            L.append(f"| {k[2:]} | {t[k]['before']:,} | {t[k]['after']:,} |")
        L += ["", f"Words whose sign status changed: {t['words_changed']:,} of {t['words']:,} in {t['texts_changed']:,} texts.", ""]
        L += ["| text | preserved | damaged | restored |", "|---|---|---|---|"]
        for c, v in t["cases"].items():
            L.append(f"| {c} | " + " | ".join(f"{a} → {b}" for a, b in v.values()) + " |")
        L.append("")
    for v in RUNS:
        b, a = res[v]["before"], res[v]["after"]
        L += [f"## Version {v}", "", "| | before | after |", "|---|---|---|"]
        for k in ["accuracy", "margin", "orphans_scored", "orphans_placed", "compositions_recovered", "cth409_best_fit"]:
            L.append(f"| {k.replace('_', ' ')} | {b[k]} | {a[k]} |")
        for k in ["best_fit", "lead", "p_vs_random", "arzawa_rank", "arzawa_signature_coverage"]:
            L.append(f"| Ambazzi {k.replace('_', ' ')} | {b['ambazzi'][k]} | {a['ambazzi'][k]} |")
        L.append(f"| Ambazzi per-text nearest | {b['ambazzi']['per_text_nearest']} | {a['ambazzi']['per_text_nearest']} |")
        for c in CASES:
            f = lambda x: f"{x['assigned'] or 'unplaced'} (nearest {x['nearest']}, runner-up {x['runner_up']}, margin {x['margin']}, {x['words']} words)"
            L.append(f"| {c} | {f(b['cases'][c])} | {f(a['cases'][c])} |")
        L += ["", "| tradition | orphans before | orphans after | reference n before | after | LOO before | after |",
              "|---|---:|---:|---:|---:|---:|---:|"]
        for t in sorted(set(b["loo_by_tradition"]) | set(a["loo_by_tradition"])):
            g = lambda d, k: d["loo_by_tradition"].get(t, {}).get(k)
            L.append(f"| {t} | {b['orphans_by_tradition'].get(t, 0)} | {a['orphans_by_tradition'].get(t, 0)} | "
                     f"{g(b, 'n')} | {g(a, 'n')} | {g(b, 'loo_acc')} | {g(a, 'loo_acc')} |")
        m = res[v]["placements"]
        L += ["", f"Orphans placed before and after: {m['placed_both']}, same tradition in {m['same_tradition']}; "
              f"placed only before: {m['only_before']}; only after: {m['only_after']}.", ""]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--before-ref", default="35ff293")
    ap.add_argument("--old-tokens")
    ap.add_argument("--new-tokens")
    ap.add_argument("--out", default="results/bracketfix_comparison")
    a = ap.parse_args()
    res = {}
    if a.old_tokens and a.new_tokens:
        res["tokens"] = token_counts(a.old_tokens, a.new_tokens)
    for v, run in RUNS.items():
        b, n = key_numbers(reader(a.before_ref), run), key_numbers(reader(None), run)
        pb, pa = b.pop("_placements"), n.pop("_placements")
        both = pb.dropna().index.intersection(pa.dropna().index)
        res[v] = {"before": b, "after": n, "placements": {
            "placed_both": int(len(both)), "same_tradition": int((pb[both] == pa[both]).sum()),
            "only_before": int(len(pb.dropna().index.difference(pa.dropna().index))),
            "only_after": int(len(pa.dropna().index.difference(pb.dropna().index)))}}
    json.dump(res, open(a.out + ".json", "w"), indent=1, ensure_ascii=False)
    Path(a.out + ".md").write_text(md(res), encoding="utf-8")
    print(md(res))


if __name__ == "__main__":
    main()
