"""Review, correct and audit the word-class annotation (qtm/wordclass.py on TLHdig's analyses).

The classes are set by rules from TLHdig's morphological analyses, so they inherit both the
editors' choices and the rules' mistakes. Each token carries the rule that set it and a
confidence level (high / medium / low, see qtm.wordclass.RULES). Three steps keep the errors in
view:

  sheet   labels/wordclass_review.csv: one row per word form and class, low and medium confidence
          and forms with more than one class first, then by frequency. Fill `corrected_class`
          (one of the classes below) for wrong rows; leave the rest empty.
  apply   copies the filled rows into labels/wordclass_corrections.csv, which qtm.tlhdig applies
          when it builds the token table (`bash reproduce.sh` reruns everything).
  audit   labels/wordclass_audit.csv: a fixed random sample of tokens per confidence level, with
          the line they stand in. Mark `verdict` y (right) or n (wrong, and give `correct_class`).
  score   accuracy per confidence level with a 95% Wilson interval, and the corpus-wide estimate
          weighted by the share of tokens at each level -> results/wordclass_audit.json.

Usage: python review_wordclass.py {sheet,apply,audit,score} [--tokens data/tokens.csv]
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from qtm.groups import ABSTRACT, GROUPSETS, HISTORICAL, RESIDUE
from qtm.wordclass import CLASSES

HERE = Path(__file__).parent
SHEET = HERE / "labels" / "wordclass_review.csv"
CORR = HERE / "labels" / "wordclass_corrections.csv"
AUDIT = HERE / "labels" / "wordclass_audit.csv"
SCORE = HERE / "results" / "wordclass_audit.json"
VALID = set(CLASSES) | {"other", "ambiguous", "unknown"}
LEVELS = ("high", "medium", "low", "manual")
PER_LEVEL = 60
SEED = 0


def tokens(path):
    """Legible words of the texts the experiments use (reference traditions, residue, orphan pools)."""
    t = pd.read_csv(path, low_memory=False, dtype={"cth_number": str})
    used = {str(c) for g in (HISTORICAL, ABSTRACT, *GROUPSETS.values(), RESIDUE) for cs in g.values() for c in cs} | {"470"}
    return t[t.word.notna() & (t.word != "") & t.cth_number.isin(used)]


def sheet(t, top):
    g = t.groupby(["word", "wclass"]).agg(
        translit=("translit", lambda s: s.value_counts().index[0]), rule=("wc_rule", lambda s: s.value_counts().index[0]),
        confidence=("wc_conf", lambda s: s.value_counts().index[0]), tokens=("txtid", "size"),
        texts=("txtid", "nunique")).reset_index()
    n_cls = t.groupby("word").wclass.nunique()
    g["classes_of_this_form"] = g.word.map(n_cls)
    rank = {"low": 0, "medium": 1, "high": 2, "manual": 3}
    g = g.assign(_r=g.confidence.map(rank).fillna(0) - (g.classes_of_this_form > 1)).sort_values(
        ["_r", "tokens"], ascending=[True, False]).drop(columns="_r")
    unsure = g.confidence.isin(["low", "medium"])
    cover = {n: round(float(g.tokens.iloc[:n][unsure.iloc[:n]].sum() / g.tokens[unsure].sum()), 3) for n in (100, 500, top)}
    g = g.iloc[:top].copy()
    g["corrected_class"], g["note"] = "", ""
    if SHEET.exists():  # keep what was already filled in
        old = pd.read_csv(SHEET, dtype=str).fillna("")
        old = old[old.corrected_class != ""].set_index(["word", "wclass"])
        key = list(zip(g.word, g.wclass))
        g["corrected_class"] = [old.corrected_class.get(k, "") for k in key]
        g["note"] = [old.note.get(k, "") for k in key]
    g.to_csv(SHEET, index=False)
    print(f"{SHEET}: {len(g)} rows; share of the low/medium-confidence tokens covered by the first n rows: {cover}")


def apply():
    s = pd.read_csv(SHEET, dtype=str).fillna("")
    s = s[s.corrected_class != ""]
    bad = set(s.corrected_class) - VALID
    if bad:
        raise SystemExit(f"unknown classes {bad}; use one of {sorted(VALID)}")
    cor = pd.read_csv(CORR, dtype=str).fillna("") if CORR.exists() else pd.DataFrame(
        columns=["word", "translit", "wclass", "note", "reviewer"])
    new = pd.DataFrame({"word": s.word, "translit": "", "wclass": s.corrected_class, "note": s.note, "reviewer": ""})
    out = pd.concat([cor, new]).drop_duplicates(["word", "translit"], keep="last")
    out.to_csv(CORR, index=False)
    print(f"{CORR}: {len(out)} corrections ({len(new)} from the review sheet); rerun reproduce.sh")


def audit(t):
    rng = np.random.default_rng(SEED)
    rows = []
    for lev in ("high", "medium", "low"):
        g = t[t.wc_conf == lev]
        rows.append(g.iloc[np.sort(rng.choice(len(g), min(PER_LEVEL, len(g)), replace=False))])
    a = pd.concat(rows)
    line = t.groupby(["txtid", "lnr"]).translit.agg(lambda s: " ".join(map(str, s)))
    a = a.assign(line=[line.get((x, l), "") for x, l in zip(a.txtid, a.lnr)], verdict="", correct_class="")
    a = a[["txtid", "lnr", "line", "word", "translit", "wclass", "wc_rule", "wc_conf", "verdict", "correct_class"]]
    if AUDIT.exists():
        raise SystemExit(f"{AUDIT} exists; delete it to draw a new sample")
    a.to_csv(AUDIT, index=False)
    print(f"{AUDIT}: {len(a)} tokens ({PER_LEVEL} per confidence level) to mark y/n")


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(c - h, 3), round(c + h, 3)]


def score(t):
    a = pd.read_csv(AUDIT, dtype=str).fillna("")
    done = a[a.verdict.str.lower().isin(["y", "n"])]
    share = t.wc_conf.value_counts(normalize=True)
    out = {"reviewed": int(len(done)), "of": int(len(a)), "levels": {}}
    est = 0.0
    for lev, g in done.groupby("wc_conf"):
        k, n = int((g.verdict.str.lower() == "y").sum()), len(g)
        out["levels"][lev] = {"reviewed": n, "right": k, "accuracy": round(k / n, 3), "ci95": wilson(k, n),
                              "share_of_tokens": round(float(share.get(lev, 0)), 3),
                              "errors_by_class": g[g.verdict.str.lower() == "n"].wclass.value_counts().to_dict()}
        est += k / n * share.get(lev, 0)
    if set(out["levels"]) >= {"high", "medium", "low"}:
        out["corpus_accuracy_estimate"] = round(float(est / share[["high", "medium", "low"]].sum()), 3)
    SCORE.parent.mkdir(exist_ok=True)
    SCORE.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["sheet", "apply", "audit", "score"])
    ap.add_argument("--tokens", default=str(HERE / "data" / "tokens.csv"))
    ap.add_argument("--top", type=int, default=2000, help="rows in the review sheet")
    a = ap.parse_args()
    if a.step == "apply":
        return apply()
    t = tokens(a.tokens)
    sheet(t, a.top) if a.step == "sheet" else {"audit": audit, "score": score}[a.step](t)


if __name__ == "__main__":
    main()
