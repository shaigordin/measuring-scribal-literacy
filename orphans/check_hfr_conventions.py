"""Check TLHdig 0.3 against the conventions of the HFR guides (Rieken, Schwemer et al., hethport.net/HFR/material):
  Basiscorpus  "Handreichung für die Erstellung der Transliterationen des Basiscorpus" (last change 02.11.2026)
  Annotation   "Annotation" (last change 15.04.2024)
  kritEd       "Handreichung: HFR kritische Texteditionen" (Steitler, Herdt, Müller, Görke; 05.11.2026)

Every number the paper takes from the guides' comparison with the release comes from here:
  annotation   files whose header names a human annotator (<annot editor="CS" .../>, not "auto"), and words
               whose analysis is selected (mrp0sel with a number), HFR folders against the others
               (Basiscorpus p. 14: automatic annotation, manual pre-validation, full validation only in the
               critical editions)
  trans        TLHdig's normalised word form (`trans`) is HFR's search form: voicing, vowel length and plene
               levelled (Annotation p. 8): counts forms that still contain d, g, b, a macron or a doubled vowel
  breaks       <space> widths (the editor's estimate of a gap, Basiscorpus p. 4, 9) against x's inside
               restoration brackets (kritEd p. 7: a probable sign count, [x x x])
  boundary     words marked "(-)": the word may continue into the break (Basiscorpus p. 9)
  determinatives  words whose determinatives are only plural or date markers (MEŠ, ḪI.A, KAM ..., Basiscorpus
               p. 12-13)
  undertie     words joined by ˽ (fixed compounds, Basiscorpus p. 13 and list p. 15 ff.)
  selection_language  words in a Hittite line with mrp0sel HURR/HAT/LUW/PAL and no language tag

    python3 check_hfr_conventions.py data/TLHbasisONLINE25_1_ZENODO_Beta_03 results/hfr_conventions.json
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PLURAL = {"MEŠ", "ME.EŠ", "ḪI.A", "DIDLI", "DIDLI.ḪI.A", "KAM", "KAM.ḪI.A", "ḪI.A.MEŠ", "MEŠ.ḪI.A"}
W = re.compile(r'<lb [^>]*?lg="([^"]*)"|<w\b([^>]*)>(.*?)</w>', re.S)


def main(root, out):
    by = defaultdict(Counter)
    for f in sorted(Path(root).glob("*/**/*.xml")):
        m = re.search(r"_XML_(\w+)", str(f))
        if not m:
            continue
        g = "HFR" if m.group(1) == "HFR" else "other"
        s = f.read_text(encoding="utf-8", errors="replace")
        c = by[g]
        c["files"] += 1
        head = s[:s.find("<body")]
        c["files_human_annotator"] += any(e and e != "auto" for e in re.findall(r'<annot editor="([^"]*)"', head))
        c["space"] += s.count("<space ")
        c["x_in_brackets"] += len(re.findall(r"<del_in/>[^<]*?\bx\b", s))
        line_lang = "Hit"
        for lg, attrs, inner in W.findall(s):
            if lg or not (attrs or inner):
                line_lang = lg or line_lang
                continue
            text = re.sub(r"<[^>]+>", "", inner)
            if not text.strip():
                continue
            c["words"] += 1
            a = dict(re.findall(r'([\w]+)="([^"]*)"', attrs))
            sel = a.get("mrp0sel", "").strip()
            if "mrp1" in a:
                c["words_analysed"] += 1
                c["words_selected"] += bool(re.match(r"\d", sel))
                c["words_several_selected"] += len(re.findall(r"\d+[a-z]*", sel)) > 1
            tr = a.get("trans", "")
            if tr[:1].islower():
                c["trans_phonetic"] += 1
                c["trans_with_d_g"] += bool(re.search(r"[dg]", tr))
                c["trans_with_b"] += "b" in tr
                c["trans_with_macron"] += bool(re.search(r"[āēīū]", tr))
                c["trans_with_doubled_vowel"] += bool(re.search(r"([aeiu])\1", tr))
            c["uncertain_boundary"] += "(-)" in text
            c["undertie"] += "˽" in text
            ds = [re.sub(r"<[^>]+>", "", d) for d in re.findall(r"<d>(.*?)</d>", inner)]
            if ds:
                c["words_with_determinative"] += 1
                c["only_plural_or_date_markers"] += all(d in PLURAL for d in ds)
            if sel.split()[:1] and sel.split()[0] in ("HURR", "HAT", "LUW", "PAL") and "lg" not in a and line_lang == "Hit":
                c[f"selection_{sel.split()[0]}_untagged_in_hittite_line"] += 1
    res = {g: dict(c) for g, c in by.items()}
    for g, c in res.items():
        c["share_files_human_annotator"] = round(c["files_human_annotator"] / c["files"], 4)
        c["share_analysed_words_selected"] = round(c["words_selected"] / c["words_analysed"], 4)
        c["share_words_undertie"] = round(c["undertie"] / c["words"], 4)
    tot = Counter()
    for c in by.values():
        tot.update(c)
    res["all"] = {"share_determinative_words_only_plural_or_date": round(
        tot["only_plural_or_date_markers"] / tot["words_with_determinative"], 4),
        "space": tot["space"], "x_in_brackets": tot["x_in_brackets"], "uncertain_boundary": tot["uncertain_boundary"],
        "trans_phonetic": tot["trans_phonetic"], "trans_with_d_g": tot["trans_with_d_g"],
        "trans_with_macron": tot["trans_with_macron"], "trans_with_doubled_vowel": tot["trans_with_doubled_vowel"]}
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:3])
