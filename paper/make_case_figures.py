"""Data for the worked-example figure (one fragment from its text to its placement).

Reads the worked-example output of orphans/run_case.py (case_*.json: text, similarity to every
tradition, margin, the decision split per word, the tf-idf weight of each feature in the fragment
and in the two nearest centroids, word classes per token), and writes generated/case_data.tex: macros and ready-made LaTeX snippets that figures/case_*.tex
typeset. Standard library only.

Usage: python3 make_case_figures.py [CASE.json [OUT.tex]]
"""
import json
import os
import re
import sys

CASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "orphans", "results",
                    "tlhdig03_literature", "case", "case_KBo_41_22.json")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated", "case_data.tex")
# word class -> category colour (the palette of the playground and of decision_shares.png)
CATCOLOR = {"function": "catF", "verb": "catV", "realia": "catN", "agent": "catA", "deity": "catA",
            "place": "catP", "animal": "catB", "body": "catB", "nature": "catB", "abstract": "catT",
            "adjective": "catJ", "foreign": "catX"}
LINES = {"KBo 41.22": (3, 15)}   # lines shown, where the edges are broken (r. Kol. 3'-15'); all lines otherwise


def esc(s):
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"), ("~", "–")):
        s = s.replace(a, b)
    return s


AKK = set()        # sign values written as Akkadograms in the case text (from figures/data/marks_*.csv)
_SEP = re.compile(r"([-.\s{}+˽]+)")


def _italic(sign, layer=None):
    """Hittite (phonetic) signs and Akkadograms in italics, Sumerograms and determinatives upright."""
    if layer is not None:
        return layer in ("H", "A")
    return sign in AKK or (sign == sign.lower() and any(c.isalpha() for c in sign))


def translit(t, layer=None):
    """TLHdig transliteration to LaTeX: determinatives {X} as upright superscripts, phonetic signs
    and Akkadograms in italics, Sumerograms upright. `layer` (one letter per sign, H/A/S/d) comes
    from the text's marks file; without it, lower-case signs are set in italics."""
    out, i, det = [], 0, False
    for part in _SEP.split(t):
        if not part:
            continue
        if _SEP.fullmatch(part):
            for ch in part:
                if ch == "{":
                    out.append("\\textsuperscript{"); det = True
                elif ch == "}":
                    out.append("}"); det = False
                elif not ch.isspace():
                    out.append(esc(ch))
            continue
        n = 0 if part == "x" or part.isdigit() else 1      # ∅ keeps the place of the sign it replaces
        lay = layer[i] if layer and n and i < len(layer) else None
        i += n
        e = esc(part)
        if n and not det and _italic(part, lay):
            e = "\\textit{" + e + "}"
        out.append(e)
    return "".join(out)


def feature(f):
    """A feature name as typeset: §kar·pí·in -> kar-pí-in (signs, in a box of their own), EMEan -> EMEan
    (word form, bold); italics as in translit()."""
    if f.startswith("§"):
        return "\\sgx{" + "-".join(("\\textit{" + esc(x) + "}") if _italic(x) else esc(x) for x in f[1:].split("·")) + "}"
    parts = f.split("-")
    return "\\wf{" + "-".join(("\\textit{" + esc(x) + "}") if _italic(x) else esc(x) for x in parts) + "}"


def line_no(lnr):
    m = re.search(r"(\d+)′", lnr)
    return int(m.group(1)) if m else None


def short(t):
    return {"Luwian rituals (Puriyanni, Kuwattalla)": "Luwian rituals",
            "Kizzuwatna–Lower Land (Hurrian)": "Kizzuwatna–Lower Land",
            "Luwian festivals (Ištanuwa, Lallupiya)": "Luwian festivals",
            "Mixed (Hurrian, Syrian, Luwian)": "Mixed Hurrian",
            "Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamia",
            "Arzawa / western rituals": "Arzawa"}.get(t, t)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else CASE
    out = sys.argv[2] if len(sys.argv) > 2 else OUT
    case = json.load(open(path, encoding="utf-8"))
    mpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures", "data",
                         "marks_" + case["txtid"].replace(" ", "_").replace(".", "_") + ".csv")
    layers = {}
    if os.path.exists(mpath):
        import csv
        for r in csv.DictReader(open(mpath, encoding="utf-8")):
            layers[(r["lnr"], int(r["pos"]))] = r["layer"]
            for sign, lay in zip([x for x in _SEP.split(r["translit_ed"]) if x and not _SEP.fullmatch(x) and x != "x"], r["layer"]):
                if lay == "A":
                    AKK.add(sign)
        for r in csv.DictReader(open(mpath, encoding="utf-8")):
            for sign, lay in zip([x for x in _SEP.split(r["translit_ed"]) if x and not _SEP.fullmatch(x) and x != "x"], r["layer"]):
                if lay == "S":
                    AKK.discard(sign)
    pos, cur, tok_layer = 0, None, []
    for t in case["tokens"]:
        pos = pos + 1 if t["lnr"] == cur else 0
        cur = t["lnr"]
        tok_layer.append(layers.get((t["lnr"], pos)))
    extra = {"n_features": case["n_features"], "dim": case["dim"], "ref_counts": case["ref_counts"],
             "rows": [[f["name"], f["x"], f["c_top"], f["c_second"], f["contribution"]] for f in case["features"]],
             "idf": {f["name"]: f["idf"] for f in case["features"]},
             "tokens": [[t["lnr"], t["translit"], t["word"] or "", t["wclass"] or "", t["wc_rule"] or "", t["wc_conf"] or ""]
                        for t in case["tokens"]]}
    L = ["% generated by make_case_figures.py; do not edit"]
    d = lambda k, v: L.append(f"\\expandafter\\def\\csname case@{k}\\endcsname{{{v}}}")

    sims = case["similarity"]
    top, second = case["nearest"], case["runner_up"]
    d("txtid", esc(case["txtid"]))
    d("filed", esc(case["filed_under"]))
    d("words", case["legible_words"])
    d("top", esc(top)); d("topshort", esc(short(top)))
    d("second", esc(second)); d("secondshort", esc(short(second)))
    d("s1", f"{sims[top]:.2f}"); d("s2", f"{sims[second]:.2f}")
    d("margin", f"{case['margin']:.2f}"); d("tau", f"{case['rule_margin']:.3f}")
    d("nfeat", extra["n_features"]); d("dim", f"{extra['dim']:,}".replace(",", "{,}"))
    d("ntop", extra["ref_counts"][top]); d("nsecond", extra["ref_counts"][second])
    d("common", f"{100 * case['decision_share_common_features']:.0f}\\%".replace("-", "−"))
    idf = extra["idf"]
    d("idf.rare", f"{idf.get('pankauaš', 0):.1f}"); d("idf.common", f"{idf.get('§na', 0):.1f}")
    nn = case["nearest_manuscripts"]
    d("nn1", esc(nn[0][0])); d("nn1cth", esc(nn[0][1]))
    d("nn.409", sum(1 for r in nn[:5] if r[1] == "409"))
    # generic: the CTH number most frequent among the five nearest manuscripts
    cths = [r[1] for r in nn[:5]]
    mode = max(cths, key=cths.count)
    d("nn.modecth", esc(mode)); d("nn.mode", cths.count(mode))

    # 1. the text, each word tinted by its word class (dashed frame: low-confidence class)
    cls = {}
    for lnr, tl, word, wc, rule, conf in extra["tokens"]:
        cls.setdefault((lnr, tl), (wc, conf))
    rows, shaded = [], []
    shares = {}
    for lnr, tl, word, share in case["word_shares"]:
        shares.setdefault((lnr, tl), share)
    cur, a, b = None, [], []
    for k, (lnr, tl, word, wc, rule, conf) in enumerate(extra["tokens"]):
        n = line_no(lnr)
        first, last = LINES.get(case["txtid"], (0, 10 ** 6))
        if n is None or not first <= n <= last:
            continue
        if lnr != cur and a:
            rows.append((cur, a)); shaded.append((cur, b)); a, b = [], []
        cur = lnr
        t = translit(tl, tok_layer[k])
        if not word:
            a.append(f"\\broken{{{t}}}"); b.append(f"\\broken{{{t}}}")
            continue
        col = CATCOLOR.get(wc, "catO")
        a.append(f"\\wc{{{col}}}{{{'low' if conf == 'low' or col == 'catO' else 'ok'}}}{{{t}}}")
        s = shares.get((lnr, tl), 0.0)
        b.append(f"\\ws{{{max(0, min(100, round(s * 300)))}}}{{{t}}}")
    rows.append((cur, a)); shaded.append((cur, b))
    fmt = lambda rr: "".join(f"\\tline{{{line_no(l)}′}}{{{' '.join(ws)}}}" for l, ws in rr)
    L.append("\\def\\CaseText{" + fmt(rows) + "}")
    L.append("\\def\\CaseShaded{" + fmt(shaded) + "}")

    # the word followed from text to features in step 2, tinted by its class
    key = next((t for t in extra["tokens"] if t[1] == "pa-an-ga-u-wa-aš"), None)
    if key:
        L.append(f"\\def\\CaseKeyWord{{\\wc{{{CATCOLOR.get(key[3], 'catO')}}}{{{'low' if key[5] == 'low' or key[3] not in CATCOLOR else 'ok'}}}{{pa-an-ga-u-wa-aš}}}}")
    # generic: the syllabically written word of three or more signs with the largest share of the
    # lead, its word-form feature and its two-to-three-sign features
    contrib = {r[0]: r for r in extra["rows"]}
    best = None
    for lnr, tl, word, wc, rule, conf in extra["tokens"]:
        if not word or word not in contrib or "∅" in tl or len(tl.split("-")) < 3 or not tl.islower():
            continue
        if best is None or contrib[word][4] > contrib[best[2]][4]:
            best = (lnr, tl, word, wc, rule, conf)
    if best:
        lnr, tl, word, wc, rule, conf = best
        L.append(f"\\def\\GenKeyWord{{\\wc{{{CATCOLOR.get(wc, 'catO')}}}{{{'low' if conf == 'low' or wc not in CATCOLOR else 'ok'}}}{{{translit(tl, dict(zip([(x[0], x[1]) for x in extra["tokens"]], tok_layer)).get((lnr, tl)))}}}}}")
        d("gen.word", esc(word)); d("gen.x.w", f"{contrib[word][1]:.2f}")
        d("gen.idf.word", f"{extra['idf'].get(word, 0):.1f}")
        sg = tl.split("-")
        grams = ["§" + "·".join(sg[i:i + n]) for n in (3, 2) for i in range(len(sg) - n + 1)]
        grams = [g for g in grams if g in contrib][:3]
        L.append("\\def\\GenGrams{" + "".join(
            f"\\hspace*{{1mm}}$\\to$ signs {feature(g)} \\hfill {contrib[g][1]:.2f}\\\\" for g in grams) + "}")
    singles = [(v, f) for f, v in extra["idf"].items() if f.startswith("§") and "·" not in f]
    if singles:
        v, f = min(singles)
        d("gen.idf.common", f"{v:.1f}"); L.append(f"\\def\\GenCommonSign{{{feature(f)}}}")
    # the features with the largest shares of the lead, as words for the last panel
    top3 = [r[0] for r in extra["rows"] if r[4] > 0 and not r[0].startswith("§")][:3]
    L.append("\\def\\GenTopWords{" + ", ".join(feature(f) for f in top3) + "}")

    # 2. similarity to each tradition (bar chart rows: name, value, is-top)
    bars = [f"\\simbar{{{i}}}{{{esc(short(t))}}}{{{v:.3f}}}{{{'top' if t == top else ('second' if t == second else 'other')}}}"
            for i, (t, v) in enumerate(sims.items())]
    L.append("\\def\\CaseBars{" + "".join(bars) + "}")

    # 3. features that decide: weight in the fragment, in the two centroids, contribution
    feats = extra["rows"]
    pos = [r for r in feats if r[4] > 0][:6]
    neg = sorted([r for r in feats if r[4] < 0], key=lambda r: r[4])[:2]
    sgn = lambda v: f"{v:+.1f}".replace("-", "−")
    trow = lambda r: f"{feature(r[0])} & {r[1]:.2f} & {r[2]:.2f} & {r[3]:.2f} & {sgn(r[4] * 1000)} \\\\"
    L.append("\\def\\CaseFeatRows{" + "".join(trow(r) for r in pos) + "\\midrule " + "".join(trow(r) for r in neg) + "}")
    # contribution bars for the tug-of-war version (top 8 for, 3 against)
    tug = [f"\\tug{{{i}}}{{{feature(r[0])}}}{{{r[4] * 1000:.1f}}}" for i, r in enumerate(pos[:8] + neg[:3])]
    L.append("\\def\\CaseTug{" + "".join(tug) + "}")
    # one word's features, for the 'from word to features' step
    for k, f in (("w", "pankauaš"), ("n1", "§pa·an·ga"), ("n2", "§an·ga·u"), ("n3", "§ga·u·wa")):
        r = next((r for r in feats if r[0] == f), None)
        if r:
            d(f"x.{k}", f"{r[1]:.2f}")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
