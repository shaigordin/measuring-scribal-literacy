"""Fill TLHdig's missing word analyses (a side check; the main results do not use it).

TLHdig 0.3 gives no lemma for about a fifth of the preserved words (all of the Luwian rituals,
CTH 758–763, and many other rituals), and the main model reads only words with a lemma. This script
fills the gaps in the sign-marked token table (python3 -m qtm.tlhdig) in two steps, and records for
every filled word where its analysis comes from:

1. TLHdig itself: a word without a lemma gets the lemma that TLHdig gives the same spelling elsewhere,
   if every analysed occurrence of that spelling has one and the same lemma. Its word class is the
   one most often given to that spelling. `fill_source` names one example: "TLHdig: KUB 31.79 Vs. 7′
   (384×)". Spellings with more than one lemma stay unfilled.
2. eDiAna, for the Luwian words: a word still without a lemma, written phonetically (no logogram or
   determinative) in a Luwian line or a Luwian ritual (CTH 758–763), gets the eDiAna lemma of the same
   spelling in eDiAna's Cuneiform Luwian corpus (ediana_cluwian.py), if eDiAna gives that spelling one
   lemma only. Word class "foreign", as for other Luwian words. `fill_source` cites eDiAna, the lemma
   and one example line: "eDiAna, s.v. zawi(n); KBo 008.074+ Vs.II 22". eDiAna: Digital
   Philological-Etymological Dictionary of the Minor Ancient Anatolian Corpus Languages, LMU München,
   https://www.ediana.gwi.uni-muenchen.de/ (CC BY-SA 4.0).

Spellings are compared as edited (restored signs included); qtm.variants then decides, as for every
other word, whether a filled word counts in version C.

Usage: python3 fill_lemmas.py data/tokens_marks.csv data/tokens_marks_filled.csv [--ediana data/ediana_cluwian_forms.csv]
"""
import argparse
import re

import pandas as pd

EDIANA = "eDiAna"


def legible(t):
    t = str(t)
    return t not in ("", "nan", "…") and "x" not in t.replace("×", "") and re.search(r"[A-Za-zÀ-ž]", t) is not None


LUWIAN_CTH = {str(c) for c in range(758, 764)}   # Luwian rituals: TLHdig tags their lines as Hittite


def phonetic(k):
    """A whole phonetically written word of 2+ signs: no logograms, determinatives or clitic fragments."""
    return (bool(k) and not k[0] in "-=" and not k.endswith("-") and "{" not in k and "-" in k
            and re.fullmatch(r"[a-zà-žḫ₀-₉\-=]+", k) is not None)


def key(t):
    """Spelling for matching TLHdig with eDiAna: no editorial marks, ḫ = h, determinatives without spaces."""
    t = re.sub(r"[\[\]⸢⸣<>?!()˹˺]", "", str(t)).lower().replace("ḫ", "h")
    t = re.sub(r"\{\s*([^}]*?)\s*\}\s*", r"{\1}", t)
    return re.sub(r"-y([aeiu])", r"-i\1", t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("marks")
    ap.add_argument("out")
    ap.add_argument("--ediana", default="data/ediana_cluwian_forms.csv")
    a = ap.parse_args()
    df = pd.read_csv(a.marks, dtype=str, keep_default_na=False)
    df["fill_source"] = ""
    empty = (df.word == "") & df.translit.map(legible)
    print(f"words without a lemma, legible: {int(empty.sum())} of {len(df)}")

    # 1. TLHdig: same spelling, one lemma everywhere
    an = df[df.word != ""]
    g = an.groupby("translit")
    lem = g.word.agg(lambda s: s.iloc[0] if s.nunique() == 1 else None).dropna()
    cls = g.wclass.agg(lambda s: s.value_counts().index[0])
    n = g.size()
    ex = g.apply(lambda d: f"{d.txtid.iloc[0]} {d.lnr.iloc[0]}".strip(), include_groups=False)
    hit = empty & df.translit.isin(lem.index)
    t = df.loc[hit, "translit"]
    df.loc[hit, "word"] = t.map(lem)
    df.loc[hit, "wclass"] = t.map(cls)
    df.loc[hit, "wc_rule"] = "filled_tlhdig"
    df.loc[hit, "wc_conf"] = "low"
    df.loc[hit, "fill_source"] = [f"TLHdig: {ex[x]} ({n[x]}×)" for x in t]
    print(f"filled from TLHdig: {int(hit.sum())}")

    # 2. eDiAna: Luwian spellings with one lemma in eDiAna's Cuneiform Luwian corpus
    E = pd.read_csv(a.ediana, dtype=str, keep_default_na=False)
    E["k"] = E.spelling.map(key)
    E = E[E.k.map(phonetic)]
    ge = E.groupby("k")
    elem = ge.lemma.agg(lambda s: s.iloc[0] if s.nunique() == 1 else None).dropna()
    eex = ge.apply(lambda d: f"{d.text.iloc[0]} {d.line.iloc[0]}", include_groups=False)
    luwian = (df.lang == "Luw") | (df.get("lang_word", "") == "Luw") | df.cth_number.isin(LUWIAN_CTH)
    still = (df.word == "") & df.translit.map(legible) & luwian & df.translit.map(key).map(phonetic)
    k = df.translit.map(key)
    hit2 = still & k.isin(elem.index)
    kk = k[hit2]
    df.loc[hit2, "word"] = kk.map(elem)
    df.loc[hit2, "wclass"] = "foreign"
    df.loc[hit2, "wc_rule"] = "filled_ediana"
    df.loc[hit2, "wc_conf"] = "low"
    df.loc[hit2, "fill_source"] = [f"{EDIANA}, s.v. {elem[x]}; {eex[x]}" for x in kk]
    print(f"filled from eDiAna: {int(hit2.sum())}; still without a lemma: {int(((df.word == '') & df.translit.map(legible)).sum())}")
    df.to_csv(a.out, index=False)


if __name__ == "__main__":
    main()
