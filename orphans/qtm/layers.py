"""Split a text into layers that separate cultural/religious content from scribal habit.

Content layers (what is written):
  logograms  Sumero-/Akkadographic words (cult objects, offerings, deities, officials)
  foreign    words in Hurrian, Hattian, Luwian or Palaic (liturgical language layer)
  lexicon    Hittite words in phonetic writing, normalised (vocabulary and formulae)

Scribal layers (how it is written):
  spelling   the spelling chosen for Hittite words that are attested in more than one
             spelling, as "word=spelling"; `collapsed` is the same words without the
             spelling, so spelling vs collapsed isolates what the choice adds
  indices    seven per-text orthographic rates (plene, CVC signs, phonetic complements ...)
"""
import re
import unicodedata
from collections import Counter, defaultdict

import numpy as np

from .corpus import signs

FOREIGN = {"Hur", "Hat", "Luw", "Pal"}
VOWELS = set("aeiu")
_SUB = re.compile(r"[₀-₉0-9]")
AKKADIAN_SINGLE = {"ŠA", "Ù", "Ú", "IŠ", "INA", "ANA", "ŠU"}


def base(sign: str) -> str:
    """Sign value without index or accent: 'ú' -> 'u', 'pé' -> 'pe', 'kán' -> 'kan'."""
    s = unicodedata.normalize("NFD", _SUB.sub("", sign))
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def is_logogram(word: str) -> bool:
    return bool(word) and word[0].isupper()


def phonetic(sg):
    """Lower-case (phonetic) signs of a word; drops determinatives and logographic parts."""
    return [s for s in sg if s and not s[0].isupper()]


def spelling(sg) -> str:
    return "-".join(phonetic(sg))


def is_cvc(sign: str) -> bool:
    b = base(sign)
    return len(b) >= 3 and b[0] not in VOWELS and b[-1] not in VOWELS and sum(c in VOWELS for c in b) == 1


def has_plene(sg) -> bool:
    ph = [base(s) for s in phonetic(sg)]
    return any(ph[i] in VOWELS and ph[i - 1] and ph[i - 1][-1] == ph[i] for i in range(1, len(ph)))


INDICES = ["logogram_share", "akkadogram_share", "complement_rate", "determinative_rate",
           "plene_rate", "cvc_share", "u_acute_share"]


def indices(doc) -> dict:
    words, tr, sgs = doc["words"], doc["translits"], doc["signs"]
    n = len(words)
    logo = [i for i, w in enumerate(words) if is_logogram(w)]
    phon = [i for i, w in enumerate(words) if not is_logogram(w) and phonetic(sgs[i])]
    akk = [i for i in logo if any(s.isupper() and s in AKKADIAN_SINGLE for s in sgs[i])
           or re.search(r"[A-ZŠḪṢṬ]+-[A-ZŠḪṢṬ]", str(tr[i]))]
    comp = [i for i in logo if re.search(r"[A-ZŠḪṢṬ₀-₉]-[a-zšḫṣṭ]", str(tr[i]))]
    det = [i for i in range(n) if "{" in str(tr[i])]
    ph_signs = [s for i in phon for s in phonetic(sgs[i])]
    u = [base(s) for s in ph_signs if base(s) == "u"]
    ua = [s for s in ph_signs if base(s) == "u" and s in ("ú",)]
    rate = lambda a, b: len(a) / len(b) if b else np.nan
    return {"logogram_share": rate(logo, words), "akkadogram_share": rate(akk, logo),
            "complement_rate": rate(comp, logo), "determinative_rate": rate(det, words),
            "plene_rate": rate([i for i in phon if has_plene(sgs[i])], phon),
            "cvc_share": rate([s for s in ph_signs if is_cvc(s)], ph_signs),
            "u_acute_share": rate(ua, u)}


def variable_words(docs, min_texts=3):
    """Hittite words attested in at least two spellings, each in >= min_texts texts."""
    seen = defaultdict(Counter)
    for _, d in docs.iterrows():
        pairs = {(w, spelling(sg)) for w, sg, l in zip(d.words, d.signs, d.langs)
                 if l == "Hit" and not is_logogram(w) and phonetic(sg)}
        for w, sp in pairs:
            seen[w][sp] += 1
    return {w for w, c in seen.items() if sum(v >= min_texts for v in c.values()) >= 2}


def layer_tokens(doc, layer, variable=None):
    W, S, L = doc["words"], doc["signs"], doc["langs"]
    if layer == "logograms":
        return [w for w in W if is_logogram(w)]
    if layer == "foreign":
        return [w for w, l in zip(W, L) if l in FOREIGN]
    if layer == "lexicon":
        return [w for w, l in zip(W, L) if l == "Hit" and not is_logogram(w)]
    if layer == "spelling":
        return [f"{w}={spelling(s)}" for w, s in zip(W, S) if w in variable]
    if layer == "collapsed":
        return [w for w in W if w in variable]
    raise ValueError(layer)
