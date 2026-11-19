"""Unicode experiments: place manuscripts from TLHdig's cuneiform Unicode line strings (<lb cu="...">)
instead of the transliteration.

U_A, no word division: every line's cu string is one unit. Features are sign 1-3-grams that never cross
    a broken sign (▒), a sign without a Unicode code point (?°?) or a line end. TLHdig's cu string does
    not mark restorations, so restored signs are part of it; there are no word categories here.
U_B, word division: the cu string of a line is cut into words with the transliteration's sign count per
    word, only where the line's sign totals match. Features are the cuneiform word forms of the aligned
    lines; a word counts as in version C (at least half its signs preserved or damaged, from the parser's
    sign marks) and only if all its signs have a code point and none is broken.

Splits and scoring are those of the spellings-only check (run_spellings_only.py): the same reference sets
(A_analysed_only: 17+ analysed words; B_all_legible: 17+ legible words), the same orphans (5+ analysed
words), tf-idf, leave-one-out centroids, and the margin of the run's report. The transliteration results
on the same splits are copied from R1_spellings_only.json for comparison.

Usage: python run_unicode.py data/tokens_F.csv --xml data/TLHbasisONLINE25_1_ZENODO_Beta_04 \
           --run results/tlhdig04_literature_C_filled
Writes RUN/U_unicode.json.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import etree
from sklearn.preprocessing import normalize

from qtm.assign import assign, centroids, loo_scores, scores
from qtm.features import sign_ngrams, vectorizer
from qtm.groups import GROUPSETS, is_orphan, label_map
from qtm.tlhdig import FOLDER, _DROP, _SEP, _translit, mark_words, sign_marks
from run_experiments import MIN_WORDS
from run_spellings_only import legible

PIECES = ["KBo 44.52", "KBo 57.54", "KBo 41.22", "EBo 133", "KBo 17.54+", "KUB 35.146"]
# one unit of a cu string: a cuneiform sign (Unicode block or TLHdig's private-use signs), a broken
# sign, a sign without a code point, or a number written in digits
UNIT = re.compile(r"(?P<sign>[\U00012000-\U0001254F\U00100000-\U0010FFFD])|(?P<broken>▒)|(?P<unknown>\?°\?)|\s*(?P<num>\d+)\s*")


def cu_units(cu):
    """List of ('s', sign) / ('b', None) / ('u', None) / ('n', digits); other characters are ignored."""
    out = []
    for m in UNIT.finditer(cu or ""):
        k = m.lastgroup
        out.append(("s", m.group(k)) if k == "sign" else ("n", "#" + m.group(k)) if k == "num" else (k[0], None))
    return out


def word_sign_count(tl):
    """Signs of a transliterated word as the cu string counts them: every sign value, x and number is one."""
    t = _DROP.sub("", tl.replace("…", " "))
    return len([s for s in _SEP.split(t) if s])


def trim_to(units, n):
    """The line's units if they number n; else the same with a broken sign dropped at the start, the end,
    or both (TLHdig often writes a break at a line edge as one ▒ that has no x in the transliteration)."""
    for lo, hi in ((0, 0), (1, 0), (0, 1), (1, 1)):
        u = units[lo:len(units) - hi]
        if len(u) == n and all(units[i][0] == "b" for i in range(lo)) and all(units[-1 - i][0] == "b" for i in range(hi)):
            return u
    return None


def runs(units):
    """Sign runs of one line, cut at broken and unknown signs."""
    out, cur = [], []
    for k, v in units:
        if k in ("s", "n"):
            cur.append(v)
        else:
            out.append(cur); cur = []
    out.append(cur)
    return [r for r in out if r]


def read_file(path):
    tree = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True))
    if tree.getroot() is None:
        return None, []
    doc = tree.find(".//docID")
    txtid = doc.text.strip() if doc is not None and doc.text else Path(path).stem
    marks = mark_words(tree)
    lines = []
    for el in tree.iter("lb", "w"):
        if el.tag == "lb":
            lines.append({"cu": cu_units(el.get("cu")), "words": []})
        elif lines:
            tl = _translit(el)
            if tl:
                m = sign_marks(marks.get(el, []), tl)
                lines[-1]["words"].append((tl, m[0] if m else None))
    return txtid, lines


def read_release(root):
    """Lines of every manuscript; a manuscript in an HFR and a TLH folder keeps the HFR copy (as qtm.tlhdig)."""
    files = {}
    for d in sorted(Path(root).iterdir()):
        m = FOLDER.match(d.name)
        if not m:
            continue
        for f in sorted(d.rglob("*.xml")):
            files.setdefault(f.stem, []).append((m.group(2) != "HFR", f))
    out = {}
    for stem, fs in files.items():
        try:
            txtid, lines = read_file(sorted(fs, key=lambda x: x[0])[0][1])
        except Exception:
            continue
        if txtid:
            out[txtid] = lines
    return out


def doc_features(lines):
    """U_A tokens, U_B tokens, and alignment counts for one manuscript."""
    a, b, n_lines, n_aligned = [], [], 0, 0
    for ln in lines:
        a += sign_ngrams(runs(ln["cu"]), n=(1, 3))
        if not ln["words"]:
            continue
        n_lines += 1
        counts = [word_sign_count(tl) for tl, _ in ln["words"]]
        cu = trim_to(ln["cu"], sum(counts))
        if cu is None:
            continue
        n_aligned += 1
        i = 0
        for (tl, st), k in zip(ln["words"], counts):
            seg, i = cu[i:i + k], i + k
            if not seg or any(kind in ("b", "u") for kind, _ in seg):
                continue
            if not st or (st.count("P") + st.count("D")) * 2 < len(st):  # version C: half the signs visible
                continue
            b.append("".join(v for _, v in seg))
    return a, b, n_lines, n_aligned


def evaluate(ref, orph, col, margin, docs):
    vec = vectorizer()
    X = vec.fit_transform(ref[col])
    y = ref.trad.to_numpy()
    S, labs = loo_scores(X, y)
    pred, _, _ = assign(S, labs)
    C, labs = centroids(X, y)
    run = {"n": int(len(ref)), "n_without_features": int((ref[col].str.len() == 0).sum()),
           "loo_acc": round(float(np.mean(pred == y)), 3),
           "per_tradition": {l: {"n": int((y == l).sum()), "loo_acc": round(float(np.mean(pred[y == l] == l)), 3)}
                             for l in labs}, "pieces": {}}
    Xo = normalize(vec.transform(orph[col]))
    p, _, _ = assign(scores(Xo, C), labs, margin)
    run["orphans"] = {"n": int(len(orph)), "placed": int(sum(v is not None for v in p)),
                      "placed_share": round(float(np.mean([v is not None for v in p])), 3),
                      "by_tradition": pd.Series([v for v in p if v is not None]).value_counts().to_dict()}
    for t in PIECES:
        row = docs[docs.txtid == t]
        if not len(row):
            continue
        s = scores(normalize(vec.transform([row.iloc[0][col]])), C)[0]
        o = np.argsort(-s)
        run["pieces"][t] = {"top3": [(labs[i], round(float(s[i]), 4)) for i in o[:3]],
                            "gap": round(float(s[o[0]] - s[o[1]]), 4), "placed": bool(s[o[0]] - s[o[1]] >= margin)}
    return run, dict(zip(orph.txtid, p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("--xml", required=True)
    ap.add_argument("--run", required=True)
    a = ap.parse_args()
    rep = json.load(open(f"{a.run}/report.json"))
    margin = rep["E2_abstention"]["margin"]
    hist = label_map(GROUPSETS[rep["groups"]])
    # the splits of run_spellings_only.py
    raw = pd.read_csv(a.tokens, low_memory=False, dtype=str)
    raw = raw[raw.translit.map(legible)]
    docs = raw.groupby("txtid").agg(cth_number=("cth_number", "first"),
                                    n_legible=("translit", "size"),
                                    n_analysed=("word", lambda s: int(s.notna().sum()))).reset_index()
    docs["orphan"] = [is_orphan(t, c) for t, c in zip(docs.txtid, docs.cth_number)]
    docs["trad"] = docs.cth_number.map(hist)
    # Unicode features
    rel = read_release(a.xml)
    feats = {t: doc_features(ls) for t, ls in rel.items()}
    docs["has_xml"] = docs.txtid.isin(feats)
    docs["U_A"] = docs.txtid.map(lambda t: feats.get(t, ([],))[0])
    docs["U_B"] = docs.txtid.map(lambda t: feats[t][1] if t in feats else [])
    docs["lines"] = docs.txtid.map(lambda t: feats[t][2] if t in feats else 0)
    docs["aligned"] = docs.txtid.map(lambda t: feats[t][3] if t in feats else 0)
    base = docs[~docs.orphan & docs.trad.notna()]
    refs = {"A_analysed_only": base[base.n_analysed >= MIN_WORDS].reset_index(drop=True),
            "B_all_legible": base[base.n_legible >= MIN_WORDS].reset_index(drop=True)}
    orph = docs[docs.orphan & (docs.n_analysed >= 5)].reset_index(drop=True)
    al_all = sum(f[3] for f in feats.values()) / max(1, sum(f[2] for f in feats.values()))
    used = pd.concat([refs["B_all_legible"], orph])
    out = {"margin": margin, "tokens": a.tokens, "xml": a.xml,
           "alignment": {"lines_with_words": int(sum(f[2] for f in feats.values())),
                         "lines_aligned": int(sum(f[3] for f in feats.values())),
                         "share_aligned_all": round(al_all, 3),
                         "share_aligned_reference_and_orphans": round(float(used.aligned.sum() / max(1, used.lines.sum())), 3),
                         "manuscripts_missing_in_xml": int((~docs.has_xml).sum())},
           "experiments": {}}
    r1 = Path(a.run) / "R1_spellings_only.json"
    r1 = json.load(open(r1))["runs"] if r1.exists() else {}
    e5 = pd.read_csv(f"{a.run}/E5_orphan_placement.csv").set_index("txtid").assigned
    for col, desc in (("U_A", "cuneiform Unicode, no word division: sign 1-3-grams within each line, cut at broken signs"),
                      ("U_B", "cuneiform Unicode, word division from the transliteration where the line's sign totals match: word forms")):
        exp = {"description": desc, "runs": {}}
        for name, ref in refs.items():
            run, pl = evaluate(ref, orph, col, margin, docs)
            pl = pd.Series(pl)
            both = e5.dropna().index.intersection(pl.dropna().index)
            run["orphans"]["vs_main"] = {"main_placed": int(e5.notna().sum()), "placed_in_both": int(len(both)),
                                         "same_tradition": int((e5[both] == pl[both]).sum())}
            if name in r1:  # transliteration (spellings) on the same split, for the comparison
                t = r1[name]
                run["transliteration_R1"] = {"loo_acc": t["loo_acc"],
                                             "per_tradition": {k: v["loo_acc"] for k, v in t["per_tradition"].items()},
                                             "orphans_placed": t["orphans_vs_main"]["placed_here"]}
            exp["runs"][name] = run
        out["experiments"][col] = exp
    out["transliteration_main"] = {"loo_acc_words": rep["E1_historical"]["words"]["acc"], "n": rep["E1_historical"]["words"]["n"],
                                   "orphans_placed": int(e5.notna().sum()), "orphans_scored": int(len(e5))}
    fn = Path(a.run) / "U_unicode.json"
    json.dump(out, open(fn, "w"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
