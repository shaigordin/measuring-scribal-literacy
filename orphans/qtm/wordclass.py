"""Word classes for TLHdig words, following the six categories of StBoT 73 Table 4
(Gordin, Yavasan & Romach 2025: 119): agent, deity, function word, Hurrian (here: any
foreign-language word), realia (here: all other nominal forms), verb.

The class comes from TLHdig's own morphological analyses (`mrp1`, `mrp2` ... on each <w>,
format lemma@gloss@morphology@stem class@determinative; `mrp0sel` names the analysis the
editor selected). Deities and agents are recognised first from determinatives and a short
list of logograms, because they cut across parts of speech. Words without a usable analysis
are `unknown`; ambiguous words whose candidate analyses disagree are `ambiguous`.
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
    if _FUNC.search(both) or "…:" in morph:      # Akkadographic prepositions: { a → …:D/L.SG }
        return "function"                        # (before person markers: PPRO.3SG is a pronoun)
    if _VERB.search(morph):
        return "verb"
    if _CASE.search(morph):
        return "realia"
    if "QUAN" in both:
        return "number"
    return "unknown"


def word_class(attrs: dict, translit: str, lang: str) -> str:
    tl = translit or ""
    word = attrs.get("trans") or ""
    if "{D}" in tl or word.startswith("DINGIR"):
        return "deity"
    if re.search(r"\{(LÚ|MUNUS|m|f)\}", tl) or re.match(r"(LÚ|MUNUS)\b", word) or re.split(r"[-\s]", word)[0] in AGENT_LOGOGRAMS:
        return "agent"
    sel = (attrs.get("mrp0sel") or "").strip()
    if lang in FOREIGN or sel == "HURR":
        return "foreign"
    mrps = {int(k[3:]): v for k, v in attrs.items() if re.fullmatch(r"mrp[1-9]\d*", k)}
    if not mrps:
        return "unknown"
    chosen = [int(n) for n in re.findall(r"(\d+)", sel)]
    pool = [mrps[n] for n in chosen if n in mrps] or list(mrps.values())
    pos = {candidate_pos(m) for m in pool} - {"unknown"}
    if len(pos) == 1:
        p = pos.pop()
        return "other" if p == "number" else p
    return "ambiguous" if pos else "unknown"

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
