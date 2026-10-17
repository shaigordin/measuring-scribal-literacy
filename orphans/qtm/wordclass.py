"""Word classes for TLHdig words, following the six categories of StBoT 73 Table 4
(Gordin, Yavasan & Romach 2025: 119): agent, deity, function word, Hurrian (here: any
foreign-language word), realia (here: all other nominal forms), verb.

The class comes from TLHdig's own morphological analyses (`mrp1`, `mrp2` ... on each <w>,
format lemma@gloss@morphology@stem class@determinative; `mrp0sel` names the analysis the
editor selected). Deities and agents are recognised first from determinatives and a short
list of logograms, because they cut across parts of speech. Words without a usable analysis
are `unknown`; ambiguous words whose candidate analyses disagree are `ambiguous`.

TLHdig keeps an Akkadographic preposition and its noun in one <w> (A-NA {GIŠ}BANŠUR, analysed as
BANŠUR with "…:D/L.SG", the "…" standing for the preposition). qtm.tlhdig splits such words into
the preposition (a function word) and the noun, which is classed from its own analysis.

Every annotation also records the rule that produced it and a confidence level (RULES):
high    a determinative ({D}, {LÚ} ...), the line's language, an editor-selected analysis
        (`mrp0sel`) with one class, or a split-off preposition;
medium  an agent logogram from the list below, or unselected candidate analyses that agree;
low     candidate analyses that disagree (`ambiguous`), or no analysis (`unknown`).
A manual correction (labels/wordclass_corrections.csv, applied by qtm.tlhdig) is `manual`.
"""
import re

CLASSES = ("agent", "deity", "function", "foreign", "realia", "verb")

AGENT_LOGOGRAMS = {"LUGAL", "MUNUS.LUGAL", "BE-EL", "BE-LU", "SANGA", "AZU", "ŠU.GI", "DUMU.É.GAL",
                   "NAR", "GALA", "EN", "ḪAL", "GUDU₁₂", "LÚ", "DUMU", "DUMU.MEŠ", "ARAD", "GÉME", "UGULA", "GAL", "ÉRIN.MEŠ"}
_VERB = re.compile(r"\b[123](SG|PL)\b|\bIMP\b|PTCP|\bINF\b|\bSUP\b|\bIMPF\b")
_CASE = re.compile(r"\b(NOM|ACC|GEN|D/L|ABL|INS|ALL|VOC|STF)\b")
_FUNC = re.compile(r"\b(CONN\w*|ADV|POSP|PREV|CNJ|PPRO|DEM\w*|REL|INT\w*|NEG|PTCL|OBP\w*|REFL|POSS\w*|INDF\w*)\b")
_ROMAN = re.compile(r"^(I|II|III|IV|V)\.")
FOREIGN = {"Hur", "Hat", "Luw", "Pal"}


def candidate_pos(mrp: str) -> str:
    f = [x.strip() for x in mrp.replace("①", "").split("@")]
    if len(f) < 3 or not f[0]:
        return "unknown"
    morph, cls = f[2], f[3] if len(f) > 3 else ""
    both = f"{morph} {cls}"
    if _ROMAN.match(cls):                        # verbal stem classes are I., II., III. ...
        return "verb"
    if _FUNC.search(both):                       # before person markers: PPRO.3SG is a pronoun
        return "function"                        # ("…:D/L.SG" is a noun after a preposition: realia)
    if _VERB.search(morph):
        return "verb"
    if _CASE.search(morph):
        return "realia"
    if "QUAN" in both:
        return "number"
    return "unknown"


RULES = {"determinative_deity": "high", "determinative_agent": "high", "language": "high",
         "analysis_selected": "high", "preposition_split": "high", "manual": "manual",
         "agent_logogram": "medium", "analysis_unanimous": "medium",
         "analysis_ambiguous": "low", "no_analysis": "low"}

# Akkadographic (and Sumerographic) prepositions that TLHdig writes in one <w> with their noun
PREPOSITIONS = {"A-NA", "ANA", "A+NA", "I-NA", "INA", "I+NA", "ŠA", "ŠÀ", "ŠÁ", "IŠ-TU", "PA-NI", "PA-AN",
                "IT-TI", "QA-DU", "QA-DU₄", "TA", "AŠ-ŠUM", "ŠA-PAL", "A-DI"}


def is_preposition(token: str) -> bool:
    """A preposition or a compound of prepositions joined by ˽ (A-NA˽PA-NI, IŠ-TU˽ŠA)."""
    return bool(token) and all(p in PREPOSITIONS for p in token.split("˽"))


def word_class_rule(attrs: dict, translit: str, lang: str) -> tuple[str, str]:
    """(word class, rule); the rule's confidence level is RULES[rule]."""
    tl = translit or ""
    word = attrs.get("trans") or ""
    if "{D}" in tl or word.startswith("DINGIR"):
        return "deity", "determinative_deity"
    if re.search(r"\{(LÚ|MUNUS|m|f)\}", tl) or re.match(r"(LÚ|MUNUS)\b", word):
        return "agent", "determinative_agent"
    if re.split(r"[-\s]", word)[0] in AGENT_LOGOGRAMS:
        return "agent", "agent_logogram"
    sel = (attrs.get("mrp0sel") or "").strip()
    if lang in FOREIGN or sel == "HURR":
        return "foreign", "language"
    mrps = {int(k[3:]): v for k, v in attrs.items() if re.fullmatch(r"mrp[1-9]\d*", k)}
    if not mrps:
        return "unknown", "no_analysis"
    chosen = [int(n) for n in re.findall(r"(\d+)", sel)]
    picked = [mrps[n] for n in chosen if n in mrps]
    pool = picked or list(mrps.values())
    pos = {candidate_pos(m) for m in pool} - {"unknown"}
    if len(pos) == 1:
        p = pos.pop()
        return ("other" if p == "number" else p), ("analysis_selected" if picked else "analysis_unanimous")
    return ("ambiguous", "analysis_ambiguous") if pos else ("unknown", "no_analysis")


def word_class(attrs: dict, translit: str, lang: str) -> str:
    return word_class_rule(attrs, translit, lang)[0]

# Display grouping shared by E11 (run_attribution.py) and the workshop playground: the six
# categories of StBoT 73 Table 4 with agents and deities together, and the rest as "Other words";
# and the three layers a feature belongs to (sign n-grams with any upper-case sign, i.e. a
# logogram or determinative, count as logographic writing).
CATEGORY = {"function": "Function words", "verb": "Verbs", "realia": "Nouns and realia",
            "agent": "Agents and deities", "deity": "Agents and deities", "foreign": "Foreign words"}
CATEGORIES = ["Function words", "Verbs", "Nouns and realia", "Agents and deities", "Foreign words", "Other words"]
LAYERS = ["Word form", "Syllabic spelling", "Logographic writing"]


def category(wclass: str) -> str:
    return CATEGORY.get(wclass, "Other words")


def layer(feature: str) -> str:
    """Layer of a 'both'-space feature: a word form, or a §-prefixed sign n-gram."""
    if not feature.startswith("§"):
        return "Word form"
    return "Logographic writing" if any(s[:1].isupper() for s in feature[1:].split("·")) else "Syllabic spelling"
