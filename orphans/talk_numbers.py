"""Every number of the Mainz deck and talk script, read from the results (no number typed by hand).

Main results: without restorations (version C, missing analyses filled: run_filled.sh C);
comparison: with restorations (version A, same fills: run_filled.sh A).

    python3 talk_numbers.py [--main results/tlhdig03_literature_C_filled] [--compare results/tlhdig03_literature_A_filled]

Writes results/talk_numbers.json and results/talk_numbers.md (slide by slide, each number with its source).
"""
import argparse
import json
from pathlib import Path

import pandas as pd

LAB = {"Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamian (Hurrian)"}   # published spelling


def lab(t):
    return LAB.get(t, t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", default="results/tlhdig03_literature_C_filled")
    ap.add_argument("--compare", default="results/tlhdig03_literature_A_filled")
    ap.add_argument("--out", default="results/talk_numbers")
    ap.add_argument("--tokens", default="data/tokens_marks_filled.csv", help="token table with sign status (for the restored ŠU.GI count)")
    a = ap.parse_args()
    M, A = Path(a.main), Path(a.compare)
    J = lambda d, p: json.loads((d / p).read_text(encoding="utf-8"))
    case = lambda d, t: J(d, f"case/case_{t.replace(' ', '_').replace('.', '_')}.json")
    rows = []

    def put(slide, key, value, source):
        rows.append({"slide": slide, "key": key, "value": value, "source": source})

    rep, repA = J(M, "report.json"), J(A, "report.json")
    tau = rep["E2_abstention"]["margin"]
    cs = J(M, "corpus_stats.json")
    for b, v in cs["laroche_bins"].items():
        put("bins", f"{b}: texts / median words", f"{v['texts']:,} / {v['median_words']:g}", "corpus_stats.json laroche_bins")
    o = cs["orphans"]
    put("bins", "EBo texts / median words", f"{o['ebo_texts']:,} / {o['ebo_median_words']:g}", "corpus_stats.json orphans")
    put("bins", "EBo filed under 832 / 670 / 470", " / ".join(str(o["ebo_filed_under"].get(c, 0)) for c in ("832", "670", "470")), "corpus_stats.json orphans.ebo_filed_under")
    put("bins", "CTH 470 + EBo manuscripts", f"{o['orphans_total']:,}", "corpus_stats.json orphans.orphans_total")
    put("theory", "orphans with 5+ words", f"{rep['corpus']['orphans_used']:,}", "report.json corpus.orphans_used")

    c44 = case(M, "KBo 44.52")
    sims = sorted(c44["similarity"].items(), key=lambda x: -x[1])
    put("frag44", "KBo 44.52 words that count", c44["legible_words"], "case_KBo_44_52.json legible_words")
    idf = {f["name"]: f["idf"] for f in c44["features"]}
    put("formula", "idf of tai / sign an", f"{idf.get('tai', float('nan')):.1f} / {idf.get('§an', float('nan')):.1f}", "case_KBo_44_52.json features.idf")
    put("formula", "similarity nearest / runner-up", f"{sims[0][1]:.2f} ({lab(sims[0][0])}) / {sims[1][1]:.2f} ({lab(sims[1][0])})", "case_KBo_44_52.json similarity")
    put("formula", "lead / threshold", f"{c44['margin']:.3f} / {tau:.3f}", "case_KBo_44_52.json margin; report.json E2_abstention.margin")
    put("formula", "threshold 90% interval", f"{rep['E2_abstention']['margin_90ci']}", "report.json E2_abstention.margin_90ci")
    put("formula", "features (non-zero) / dimensions", f"{c44['n_features']} / {c44['dim']:,}", "case_KBo_44_52.json")
    put("formula", "top decision features", ", ".join(f"{n} {v:+.3f}" for n, v in c44["decision_features"][:6]), "case_KBo_44_52.json decision_features")

    t1 = pd.read_csv(M / "case/test1_loo_placements.csv")
    n_by = t1.true.value_counts()
    e1, e1a = rep["E1_historical"]["both"], repA["E1_historical"]["both"]
    for t, n in n_by.items():
        put("traditions / test1", f"{lab(t)}: reference MSS / held-out accuracy", f"{n} / {e1['recall_by_class'][t]:.0%}", "test1_loo_placements.csv; report.json E1_historical.both.recall_by_class")
    put("test1", "accuracy / manuscripts", f"{e1['acc']:.1%} / {e1['n']:,}", "report.json E1_historical.both")
    put("test1", "largest-tradition baseline / shuffled labels", f"{e1['majority']:.0%} / {e1['null_mean']:.0%}", "report.json E1_historical.both")
    put("test1", "with restorations: accuracy / manuscripts", f"{e1a['acc']:.1%} / {e1a['n']:,}", f"{A.name}/report.json E1_historical.both")

    e10 = J(M, "E10_report.json")["E10a"]
    put("test2", "compositions recovered", f"{e10['compositions_correct']} / {e10['compositions']}", "E10_report.json E10a")
    put("test2", "by tradition", "; ".join(f"{lab(t)} {v['correct']}/{v['compositions']}" for t, v in e10["by_tradition"].items()), "E10_report.json E10a.by_tradition")
    lco = pd.read_csv(M / "E10a_leave_composition_out.csv", dtype={"cth": str})
    for c in ("404", "752", "701"):
        r = lco[lco.cth == c]
        if len(r):
            put("test2", f"CTH {c}", "; ".join(f"{k}={v}" for k, v in r.iloc[0].items()), "E10a_leave_composition_out.csv")

    sz = J(M, "case/size_example_KUB_29.4.json")
    ex = next(e for e in sz["examples"] if e["start"] == 200)
    for k, w in ex["windows"].items():
        put("size", f"KUB 29.4+ from word 200, {k} words", f"{lab(w['nearest'])}, lead {w['gap']:.4f}, placed {w['placed']}, right {w['right']}", "size_example_KUB_29.4.json")
    e2 = pd.read_csv(M / "E2_coverage_curve.csv")
    e2 = e2[e2.space == "both"].set_index("k").acc
    put("size", "all traditions: right at 3 / 10 / 40 words", " / ".join(f"{e2[k]:.0%}" for k in (3, 10, 40)), "E2_coverage_curve.csv (both)")
    put("size", "share of held-out windows placed / precision", f"{rep['E2_abstention']['share_assigned']:.0%} / {rep['E2_abstention']['precision_above_margin']:.0%}", "report.json E2_abstention")

    e7 = J(M, "E7_report.json")
    L = e7["E7a_layers"]
    put("scribes", "vocabulary alone / logograms / foreign words", f"{L['lexicon']['acc']:.0%} / {L['logograms']['acc']:.0%} / {L['foreign']['acc']:.0%} (on {L['foreign']['n']} MSS)", "E7_report.json E7a_layers")
    put("scribes", "spelling habits (seven rates) / baseline", f"{L['orthographic_indices']['acc']:.0%} / {L['orthographic_indices']['majority']:.0%}", "E7_report.json E7a_layers.orthographic_indices")
    put("scribes", "words with 2+ spellings: kept / collapsed", f"{e7['corpus']['variable_words']} words: {L['spelling']['acc']:.0%} / {L['collapsed']['acc']:.0%}", "E7_report.json corpus, E7a_layers.spelling/collapsed")
    sc = pd.read_csv(M / "E7_spelling_contrasts.csv")
    mm = sc[sc.word == "memai"].set_index("tradition")["mean"]
    put("scribes", "memai written plene", "; ".join(f"{lab(t)} {v:.1%}" for t, v in mm.items()), "E7_spelling_contrasts.csv")
    dist = pd.read_csv(M / "E7_distinctive_features.csv")
    for t, f in (("Kizzuwatna rituals", "ZA.GÌN"), ("Ḫuwaššanna festivals", "BE-EL"), ("Hattian cult layer", "GIŠ.INANNA"), ("Syro-Mesopotamia (Hurrian)", "AZU")):
        r = dist[(dist.tradition == t) & (dist.feature == f)]
        put("scribes", f"distinctive {f} ({lab(t)}) z", f"{r.z.iloc[0]:.1f}" if len(r) else "not in list", "E7_distinctive_features.csv")
    z = e7["E7b_index_profile_z"]
    for t, v in z.items():
        put("scribal", f"profile z {lab(t)}", ", ".join(f"{k} {x:+.2f}" for k, x in v.items()), "E7_report.json E7b_index_profile_z")

    ws = {}
    for _, _, w, s in c44["word_shares"]:
        ws[w] = ws.get(w, 0) + s
    put("tug44", "similarity / lead", f"{sims[0][1]:.3f} vs {sims[1][1]:.3f}, lead {c44['margin']:.3f}, {c44['margin'] / tau:.1f} x threshold", "case_KBo_44_52.json")
    put("tug44", "word shares of the lead", ", ".join(f"{w} {v:+.0%}" for w, v in sorted(ws.items(), key=lambda x: -abs(x[1]))[:8]), "case_KBo_44_52.json word_shares")
    put("decide44", "common features' share of the decision", f"{c44['decision_share_common_features']:.0%}", "case_KBo_44_52.json decision_share_common_features")
    e11 = J(M, "E11_report.json")
    b11 = e11["E11b"]
    dec = b11["common_features_share"]
    dec = dec.get("all_correct", dec.get("all")) if isinstance(dec, dict) else dec
    put("decide44", "corpus: common features share of similarity / decision", f"{b11['similarity_common_features_share']:.0%} / {dec:.0%}", "E11_report.json E11b")
    bc = J(M, "case/barcode_KBo_44_52.json")
    put("barcode", "distinctive matches per tradition", "; ".join(f"{lab(r['tradition'])} {r['distinctive']}" for r in bc["rows"]), "barcode_KBo_44_52.json")
    nm = c44["nearest_manuscripts"][:10]
    put("nearest44", "10 nearest manuscripts", "; ".join(f"{m[0]} (CTH {m[1]}, {lab(m[2])}, {m[4]:.2f})" for m in nm), "case_KBo_44_52.json nearest_manuscripts")
    put("nearest44", "CTH 701 among the 10 nearest", sum(m[1] == "701" for m in nm), "case_KBo_44_52.json nearest_manuscripts")

    for t in ("KBo 57.54", "KBo 41.22"):
        cm, ca = case(M, t), case(A, t)
        for nm_, c in (("without restorations", cm), ("with restorations", ca)):
            s = sorted(c["similarity"].items(), key=lambda x: -x[1])
            put("caution", f"{t} {nm_}", f"{lab(c['assigned']) if c['assigned'] else 'unplaced'}; nearest {lab(s[0][0])} {s[0][1]:.3f}, runner-up {lab(s[1][0])} {s[1][1]:.3f}; lead {c['margin']:.4f}; {c['legible_words']} words; top features {', '.join(n for n, _ in c['decision_features'][:4])}", f"case_{t.replace(' ', '_').replace('.', '_')}.json")
    put("caution", "threshold with restorations", f"{repA['E2_abstention']['margin']:.3f}", f"{A.name}/report.json E2_abstention.margin")
    E5m = pd.read_csv(M / "E5_orphan_placement.csv").set_index("txtid")
    E5a = pd.read_csv(A / "E5_orphan_placement.csv").set_index("txtid")
    tr = [c for c in E5m.columns if c not in ("filed_under", "n_words", "assigned", "top_sim", "gap")]
    nearest_m, nearest_a = E5m[tr].idxmax(axis=1), E5a.reindex(E5m.index)[tr].idxmax(axis=1)
    put("caution / takeaways", "orphans keeping their nearest tradition without restorations", f"{(nearest_m == nearest_a).mean():.0%} of {len(E5m):,}", "E5_orphan_placement.csv, both runs")
    only_a = E5a.index[E5a.assigned.notna()].difference(E5m.index[E5m.assigned.notna()])
    lw = [t for t in only_a if str(E5a.assigned[t]).startswith("Luwian rituals")]
    put("caution", "placed only with restorations / of them Luwian rituals", f"{len(only_a)} / {len(lw)}", "E5_orphan_placement.csv, both runs")
    if Path(a.tokens).exists():
        T = pd.read_csv(a.tokens, dtype=str, keep_default_na=False, usecols=["txtid", "translit", "status"])
        sg = T[T.txtid.isin(lw) & T.translit.str.contains(r"ŠU ?\.GI") & T.status.str.contains("R")]
        put("caution", "of these, with a restored sign in MUNUS ŠU.GI (the Old Woman)", f"{sg.txtid.nunique()} of {len(lw)}", f"{a.tokens} (status R in a ŠU.GI word)")
    unf = Path("results/tlhdig03_literature_C/case/test1_loo_placements.csv")
    if unf.exists():
        u = pd.read_csv(unf).true.value_counts()
        put("test1 / fills", "Luwian rituals reference MSS before / after filling", f"{u.get('Luwian rituals (Puriyanni, Kuwattalla)', 0)} / {n_by.get('Luwian rituals (Puriyanni, Kuwattalla)', 0)}", "results/tlhdig03_literature_C (no fills) vs main, test1_loo_placements.csv")

    ce, cea = case(M, "EBo 133"), case(A, "EBo 133")
    s = sorted(ce["similarity"].items(), key=lambda x: -x[1])
    sa = sorted(cea["similarity"].items(), key=lambda x: -x[1])
    put("ebo / tie", "EBo 133 words; without restorations", f"{ce['legible_words']} words; {lab(s[0][0])} {s[0][1]:.4f} vs {lab(s[1][0])} {s[1][1]:.4f}, lead {ce['margin']:.4f}", "case_EBo_133.json")
    put("tie", "EBo 133 with restorations", f"{lab(sa[0][0])} {sa[0][1]:.4f} vs {lab(sa[1][0])} {sa[1][1]:.4f}, lead {cea['margin']:.4f}", f"{A.name}/case/case_EBo_133.json")
    put("tie", "pulling to nearest / against", f"{', '.join(n for n, _ in ce['decision_features'][:5])} / {', '.join(n for n, _ in ce['against_features'][:4])}", "case_EBo_133.json")
    sp = J(M, "case/spread_takarmun.json")
    bt = sp["by_tradition"]
    ref_n = sum(v for k, v in bt.items() if k not in ("other", "CTH 670 (festival fragments)"))
    put("bread", "takarmun: other MSS / reference MSS / Ḫuwaššanna / Palaic / CTH 670", f"{sp['manuscripts']} / {ref_n} / {bt.get('Ḫuwaššanna festivals', 0)} / {bt.get('Palaic festivals', 0)} / {bt.get('CTH 670 (festival fragments)', 0)}", "spread_takarmun.json")
    jn = J(M, "case/joins_EBo_133.json")
    fl = [f"{c['txtid']} (rank {c['rank']}, CTH {c['cth']}, {c['n_words']} words, {c['barcode']})" for c in jn["candidates"] if c["flagged"]]
    put("join", "pool / passing all three checks", f"{jn['pool_size']:,} / {'; '.join(fl)}", "joins_EBo_133.json")
    put("suggest", "EBo 133 nearest manuscripts", "; ".join(f"{m[0]} ({lab(m[2])})" for m in ce["nearest_manuscripts"][:8]), "case_EBo_133.json nearest_manuscripts")

    put("takeaways", "orphans placed / scored", f"{rep['E5_orphans']['assigned']:,} / {rep['corpus']['orphans_used']:,}", "report.json E5_orphans, corpus")
    put("takeaways", "with restorations: placed / scored", f"{repA['E5_orphans']['assigned']:,} / {repA['corpus']['orphans_used']:,}", f"{A.name}/report.json")
    put("takeaways", "orphans placed by tradition", "; ".join(f"{lab(t)} {n}" for t, n in rep["E5_orphans"]["by_tradition"].items()), "report.json E5_orphans.by_tradition")
    fill = (M / "fill.log").read_text().strip().splitlines()
    put("clay / fills", "fill step", " | ".join(fill[-3:]), "fill.log")
    put("clay", "words that count", (M / "variant.log").read_text().strip(), "variant.log")

    Path(a.out + ".json").write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
    md = ["# Numbers for the Mainz deck and script", "", f"Main: `{M}` · comparison (with restorations): `{A}`", "",
          "| slide | number | value | source |", "|---|---|---|---|"]
    md += [f"| {r['slide']} | {r['key']} | {r['value']} | {r['source']} |" for r in rows]
    Path(a.out + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
