"""Flag glosses whose word class may need a sense decision, write their concordances, and report what the
context rules in labels/sense_rules.csv decided (see qtm.senses).

1. Flags (per gloss of labels/gloss_lexicon.tsv, counted over the tokens whose analyses carry it and that
   have a nominal class):
     multi_lemma     two or more lemmas share the gloss, each with 10% of its tokens or more (a lemma written
                     several ways counts once, see norm_lemma)
     wn_disagree     the WordNet check (results/wordnet_check/gloss_wordnet.csv) gives another class
     wn_multiclass   the gloss's WordNet senses fall in more than one of our classes
     unvalidated     half or more of its tokens were analysed automatically only: no editor-selected analysis
                     (no mrp0sel) and a file whose header names no annotator
   A gloss is flagged when two or more signals hold (any one signal holds for nearly every gloss, because
   most TLHdig tokens carry no selected analysis); flagged glosses are ranked by tokens.
2. For the TOP flagged glosses (by tokens): a concordance (KWIC: text, line, 4 words either side,
   determinatives, logograms next to it, verbs in the line, lemma, selection, the rule that fired) and the
   counts of the words in the ±4 window (collocates).
   The rules file is applied to the tokens first (as qtm.tlhdig.finish does), so edits take effect.
3. Decisions: per gloss that has rules, the tokens per rule and sense, and the tokens no rule matched.
   With --fill-evidence, rules with an empty evidence column get the first three passages they match
   (editor-selected analyses first, one per text), written back to the rules file.

Usage: python run_senses.py data/tokens_marks_new.csv [--top 30] [--out results/senses] [--fill-evidence]
           [--also 'gloss;gloss']  (concordances for more glosses, e.g. those ShG asked about)
Writes OUT/flagged_glosses.csv, OUT/concordance/<gloss>.csv and <gloss>_collocates.csv, OUT/decisions.csv,
OUT/senses.json (counts for make_numbers.py), OUT/horn_kara_candidates.csv (the tokens TLHdig's automatic
analysis offers kara= 'Horn' for; reported in the paper as a misanalysis that pre-validation does not catch).
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from qtm.senses import NOMINAL, OPEN, RULES_FILE, _UNBRACKET, apply_senses, contexts, gloss_hits, line_index, load_rules

LEXICON = Path(__file__).parent / "labels" / "gloss_lexicon.tsv"
WORDNET = Path(__file__).parent / "results" / "wordnet_check" / "gloss_wordnet.csv"
_DET = re.compile(r"\{([^}]+)\}")
_LOGO = re.compile(r"^[^a-zšḫṣṭṯâêîûàèìùáéíú]*[A-ZŠḪṢṬ][^a-zšḫṣṭṯâêîûàèìùáéíú]*$")


def slug(g):
    return re.sub(r"[^\w]+", "_", g).strip("_")[:60] or "gloss"


def explode_glosses(df):
    t = df[df.wclass.isin(NOMINAL) & (df.gloss.fillna("") != "")][["gloss", "lemma", "sel", "annotated"]].copy()
    t["g"] = t.gloss.str.split("|")
    return t.explode("g")


def norm_lemma(l):
    """One lemma written several ways counts once: circled markers and °determinatives° dropped, a
    logogram cut before its complement or suffix (SI°ḪI.A°-ŠU, GU₄u -> SI, GU₄), '=' and a final '-' removed (kara=š- -> karaš)."""
    l = re.sub(r"[①-⓿]", "", l)
    l = re.sub(r"°[^°]*°", "", l).strip()
    m = re.match(r"^([^a-zšḫṣṭ(]*?[A-ZŠḪṢṬ][^a-zšḫṣṭ(]*?)(?=[a-zšḫṣṭ(]|-|$)", l)
    if m and m.group(1).strip():          # a logogram with a phonetic complement or suffix: GU₄u, URU(e)
        l = m.group(1)
    return l.replace("=", "").rstrip("-").strip()


def flags(df, lex, wnet):
    t = explode_glosses(df)
    t["auto"] = (t.sel != "1") & (t.annotated != "1")
    lem = t.assign(l=t.lemma.str.split("|")).explode("l")
    lem["n"] = lem.l.map(norm_lemma)
    share = lem.groupby(["g", "n"]).size() / lem.groupby("g").size()
    big = share[share >= 0.1]
    per = pd.DataFrame({"tokens": t.groupby("g").size(), "automatic_share": t.groupby("g").auto.mean().round(3),
                        "lemmas": big.groupby(level=0).size(),
                        "lemma_list": big.groupby(level=0).apply(lambda s: "|".join(f"{n} {v:.0%}" for (_, n), v in s.sort_values(ascending=False).items()))})
    f = lex.set_index("gloss")[["label"]].join(per, how="left").fillna({"tokens": 0, "lemmas": 0})
    w = wnet.set_index("gloss")
    f["wordnet_class"] = w.wordnet_class.reindex(f.index).fillna("")
    f["wordnet_all"] = w.all_classes.reindex(f.index).fillna("")
    cc = w.claude_class.reindex(f.index).fillna("")
    f["multi_lemma"] = f.lemmas >= 2
    f["wn_disagree"] = (f.wordnet_class != "") & (cc != "") & (f.wordnet_class != cc)
    f["wn_multiclass"] = f.wordnet_all.str.contains(r"\|")
    f["unvalidated"] = f.automatic_share.fillna(0) >= 0.5
    sig = ["multi_lemma", "wn_disagree", "wn_multiclass", "unvalidated"]
    f["signals"] = f[sig].sum(axis=1)
    f["any_signal"] = (f.signals >= 1) & (f.tokens > 0)
    f["flagged"] = (f.signals >= 2) & (f.tokens > 0)
    f = f[f.label.isin(["realia", "abstract", "body", "nature", "animal", "place", "measure", "adjective"])]
    return f.sort_values("tokens", ascending=False)


def concordance(df, li, gloss, verbs):
    idx = df.index[gloss_hits(df, gloss)]
    ctx = contexts(li, idx)
    sub = df.loc[idx]
    win = ctx.window.str.split()
    return pd.DataFrame({
        "txtid": sub.txtid, "lnr": sub.lnr.str.strip(), "cth": sub.cth_number, "left": ctx.left, "keyword": ctx["self"],
        "right": ctx.right, "determinatives": ctx["self"].map(lambda s: " ".join(_DET.findall(s))),
        "logograms_near": [" ".join(w for w in ws if _LOGO.match(w)) for ws in win],
        "verbs_in_line": [verbs.get(k, "") for k in sub.txtid.astype(str) + "|" + sub.lnr.fillna("").astype(str)],
        "lemma": sub.lemma, "selected": sub.sel, "annotated": sub.annotated, "wclass": sub.wclass,
        "sense": sub.get("sense", ""), "sense_rule": sub.get("sense_rule", "")}), win


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--out", default="results/senses")
    ap.add_argument("--rules", default=str(RULES_FILE))
    ap.add_argument("--fill-evidence", action="store_true")
    ap.add_argument("--also", default="", help="more glosses to write concordances for, ';'-separated")
    a = ap.parse_args()
    out = Path(a.out); (out / "concordance").mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(a.tokens, dtype=str, keep_default_na=False)
    # the rules as they stand now (qtm.tlhdig.finish applies the same at parse time)
    if "sense_rule" in df:  # undo the rules applied at parse time, then apply the current file
        fired = df.sense_rule != ""
        df.loc[fired, "wclass"] = df.loc[fired, "wclass_before_sense"]
    df = apply_senses(df.drop(columns=["sense", "sense_rule", "wclass_before_sense"], errors="ignore"), a.rules)
    lex = pd.read_csv(LEXICON, sep="\t", dtype=str, keep_default_na=False)
    wnet = pd.read_csv(WORDNET, dtype=str, keep_default_na=False)
    li = line_index(df)
    key = df.txtid.astype(str) + "|" + df.lnr.astype(str)
    v = df.wclass == "verb"
    verbs = df[v].assign(k=key[v]).groupby("k").translit.agg(lambda s: " ".join(_UNBRACKET.sub("", x) for x in s)).to_dict()

    f = flags(df, lex, wnet)
    f.to_csv(out / "flagged_glosses.csv")
    fl = f[f.flagged]
    rep = {"tokens_file": a.tokens, "glosses_nominal": int(len(f)), "glosses_with_tokens": int((f.tokens > 0).sum()),
           "any_signal": int(f.any_signal.sum()), "any_signal_tokens": int(f[f.any_signal].tokens.sum()),
           "flagged": int(len(fl)), "flagged_tokens": int(fl.tokens.sum()),
           "flagged_token_share": round(float(fl.tokens.sum() / max(1, f.tokens.sum())), 3),
           "signals": {s: int(f[s].sum()) for s in ("multi_lemma", "wn_disagree", "wn_multiclass", "unvalidated")},
           "by_number_of_signals": {int(k): int(v) for k, v in f[f.tokens > 0].signals.value_counts().sort_index().items()},
           "concordances_for_top": a.top}

    extra = [g for g in a.also.split(";") if g]
    rep["concordances_also"] = extra
    for g in list(fl.index[:a.top]) + [g for g in extra if g not in fl.index[:a.top]]:
        c, win = concordance(df, li, g, verbs)
        c.to_csv(out / "concordance" / f"{slug(g)}.csv", index=False)
        n = len(c)
        cnt = Counter(w for ws in win for w in set(ws))
        pd.DataFrame([(w, k, round(k / n, 3)) for w, k in cnt.most_common(200)],
                     columns=["collocate", "tokens_with_it", "share"]).to_csv(out / "concordance" / f"{slug(g)}_collocates.csv", index=False)

    rules = load_rules(a.rules)
    dec = []
    if not rules.empty:
        for g, rs in rules.groupby("gloss", sort=False):
            hit = gloss_hits(df, g) & (df.wclass.isin(OPEN) | (df.sense_rule != ""))
            d = df[hit]
            for _, r in rs.iterrows():
                dec.append({"gloss": g, "rule_id": r.rule_id, "sense": r.sense, "wclass": r.wclass,
                            "tokens": int((d.sense_rule == r.rule_id).sum()), "decided_by": r.decided_by})
            dec.append({"gloss": g, "rule_id": "", "sense": "(no rule matched)", "wclass": "unchanged",
                        "tokens": int((d.sense_rule == "").sum()), "decided_by": ""})
        if a.fill_evidence:
            for i, r in rules.iterrows():
                if r.evidence.strip():
                    continue
                d = df[df.sense_rule == r.rule_id].copy()
                d["o"] = d.sel != "1"
                d = d.sort_values(["o", "txtid", "lnr"]).drop_duplicates("txtid").head(3)
                rules.loc[i, "evidence"] = "; ".join(f"{t} {l.strip()}" for t, l in zip(d.txtid, d.lnr))
            rules.to_csv(a.rules, index=False)
    pd.DataFrame(dec).to_csv(out / "decisions.csv", index=False)
    rep["rules"] = int(len(rules)) if not rules.empty else 0
    rep["rules_by_decider"] = rules.decided_by.value_counts().to_dict() if not rules.empty else {}
    rep["glosses_with_rules"] = int(rules.gloss.nunique()) if not rules.empty else 0
    if "sense_rule" in df:
        fired = df.sense_rule != ""
        rep["tokens_with_sense_rule"] = int(fired.sum())
        rep["tokens_class_changed"] = int((fired & (df.wclass != df.wclass_before_sense)).sum())
    # the automatic candidate kara= 'Horn' (paper example): tokens whose analyses include it, by spelling and class
    kh = gloss_hits(df, "Horn", r"(^|\|)kara=($|\|)")
    k = df[kh]
    ctx = contexts(li, k.index)
    pd.DataFrame({"txtid": k.txtid, "lnr": k.lnr.str.strip(), "translit": k.translit, "lemma": k.lemma, "gloss": k.gloss,
                  "selected": k.sel, "wclass": k.wclass, "line": ctx.line}).to_csv(out / "horn_kara_candidates.csv", index=False)
    rep["horn_kara_candidates"] = {"tokens": int(len(k)), "editor_selected": int((k.sel == "1").sum()),
                                   "by_spelling": k.translit.str.replace(r"[\[\]⸢⸣〈〉]", "", regex=True).value_counts().to_dict(),
                                   "by_class": k.wclass.value_counts().to_dict()}
    json.dump(rep, open(out / "senses.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
