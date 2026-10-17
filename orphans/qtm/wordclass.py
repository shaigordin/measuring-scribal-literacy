"""Word classes for TLHdig words, following the six categories of StBoT 73 Table 4
(Gordin, Yavasan & Romach 2025: 119): agent, deity, function word, Hurrian (here: any
foreign-language word), realia, verb. Realia are narrowed to physical things (artifacts and
buildings, ritual and cultic materials, food, plants); the other nominal words are classed by the
meaning of their German gloss as places, animals, body parts, nature, abstract nouns, adjectives or
measures (labels/gloss_lexicon.tsv, see meaning_class).

The class comes from TLHdig's own morphological analyses (`mrp1`, `mrp2` ... on each <w>,
format lemma@gloss@morphology@stem class@determinative; `mrp0sel` names the analysis the
editor selected). Deities and agents are recognised first from determinatives and a short
list of logograms, because they cut across parts of speech. Words without a usable analysis
are `unknown`; ambiguous words whose candidate analyses disagree are `ambiguous`.

TLHdig keeps an Akkadographic preposition and its noun in one <w> (A-NA {GIŠ}BANŠUR, analysed as
BANŠUR with "…:D/L.SG", the "…" standing for the preposition). qtm.tlhdig splits such words into
the preposition (a function word) and the noun, which is classed from its own analysis.

Every annotation also records the rule that produced it and a confidence level (RULES):
high    a determinative ({D}, {LÚ} ...), the language tag (a logogram in a foreign line is not
        foreign), a syllabic Akkadian preposition (ina, ana), an editor-selected analysis
        (`mrp0sel`) with one class, or a split-off preposition;
medium  an agent logogram from the list below, unselected candidate analyses that agree, or
        (for a word the editors left unselected) the class the editors chose for the same word
        form elsewhere, when at least 5 selected occurrences agree at 90% or more;
        A word without an analysis takes the class of a realia determinative ({GIŠ}, {UZU} ...) or
        of a compound logogram's head (É.DINGIR, GIŠ.{D}INANNA "harp": an object, not a god);
low     candidate analyses that disagree (`ambiguous`), or no analysis (`unknown`); for a broken
        word without an analysis, an enclitic chain (-ma-kán, -ša-an, nu-uš(-)) makes it a function
        word, and a third person plural ending (-a-an-zi) a verb. (Taking the class the editors
        selected for words with the same readable beginning, ši-pa-an-, was tried and dropped: it
        was wrong on 4 of the 5 audited cases, iš-pa-an-du- among them.)
The rules for broken words and realia determinatives come from the philologist's audit of
180 words (labels/wordclass_audit_marked.xlsx).
A manual correction (labels/wordclass_corrections.csv, applied by qtm.tlhdig) is `manual`.
"""
import csv
import re
from pathlib import Path

CLASSES = ("agent", "deity", "function", "foreign", "realia", "verb", "place", "animal", "body", "nature",
           "abstract", "adjective")

AGENT_LOGOGRAMS = {"LUGAL", "MUNUS.LUGAL", "BE-EL", "BE-LU", "SANGA", "AZU", "ŠU.GI", "DUMU.É.GAL",
                   "NAR", "GALA", "EN", "ḪAL", "GUDU₁₂", "LÚ", "DUMU", "DUMU.MEŠ", "ARAD", "GÉME", "UGULA", "ÉRIN.MEŠ"}
# (GAL "great" is not in the list: standing alone it is mostly the adjective, and its TLHdig
# analysis, a noun or adjective, decides)
_VERB = re.compile(r"\b[123](SG|PL)\b|\bIMP\b|PTCP|\bINF\b|\bSUP\b|\bIMPF\b")
_CASE = re.compile(r"\b(NOM|ACC|GEN|D/L|ABL|INS|ALL|VOC|STF)\b")
_FUNC = re.compile(r"\b(CONN\w*|ADV|POSP|PREV|CNJ|PPRO|DEM\w*|REL|INT\w*|NEG|PTCL|OBP\w*|REFL|POSS\w*|INDF\w*)\b")
_ROMAN = re.compile(r"^(I|II|III|IV|V)\.")
FOREIGN = {"Hur", "Hat", "Luw", "Pal"}


_ALT = re.compile(r"\{\s*([a-z])\s*→\s*([^}]*)\}")
_HEAD_FUNC = re.compile(r"^(?:LUW\.|PAL\.|HAT\.)?(CONN\w*|ADV|POSP|PREV|PRP|CNJ\w*|PPRO|DEM\w*|REL|INT\w*|NEG|PTCL|OBP\w*|REFL|INDF\w*)\b")


def alternatives(morph: str, letters: str = "") -> list[str]:
    """The morphological readings of one analysis: '{ a → NOM.SG} { b → ACC.SG}' gives two; with
    `letters` (the editor's choice, e.g. 'a' from mrp0sel '1a') only those are kept."""
    alts = _ALT.findall(morph)
    if not alts:
        return [morph]
    keep = [m for l, m in alts if l in letters] if letters and letters != "all" else []
    return keep or [m for _, m in alts]


def reading_pos(m: str) -> str:
    """Part of speech of one reading. Only its head counts: what follows '_' or '=' is a suffix
    (a possessive or enclitic pronoun on a noun, 'BE-LÍ-IA' NOM.SG_PPRO.1SG.GEN) or the position
    after a preposition ('…:D/L.SG_vor:POSP'), and '…:' stands for the preposition itself."""
    head = re.split(r"[_=]", m.strip(), maxsplit=1)[0].replace("…:", "").strip()
    if _HEAD_FUNC.match(head):
        return "function"
    if _VERB.search(head):
        return "verb"
    if _CASE.search(head):
        return "realia"
    if "QUAN" in head:
        return "number"
    return "unknown"


def candidate_pos(mrp: str, letters: str = "") -> str:
    """Part of speech of one TLHdig analysis (lemma@gloss@morphology@stem class@determinative):
    a verbal stem class (I., II. ...) makes a verb; otherwise the readings decide, and readings
    that disagree (aššu 'good': NOM.SG.N or ADV) make the analysis ambiguous."""
    f = [x.strip() for x in mrp.replace("①", "").split("@")]
    if len(f) < 3 or not f[0]:
        return "unknown"
    morph, cls = f[2], f[3] if len(f) > 3 else ""
    if _ROMAN.match(cls):                        # verbal stem classes are I., II., III. ...
        return "verb"
    # uninflected words carry their tag in the stem-class field: 'peran@vor@@ ADV@', '1@ein@@ QUANcar@'
    readings = alternatives(morph, letters) if morph else [cls]
    pos = {reading_pos(m) for m in readings} - {"unknown"}
    if len(pos) == 1:
        return pos.pop()
    return "ambiguous" if pos else "unknown"


RULES = {"determinative_deity": "high", "determinative_agent": "high", "language": "high",
         "akkadian_function": "high",
         "analysis_selected": "high", "preposition_split": "high", "manual": "manual",
         "agent_logogram": "medium", "analysis_unanimous": "medium", "selected_elsewhere": "medium",
         "determinative_noun": "medium",
         "analysis_ambiguous": "low", "no_analysis": "low",
         "broken_clitic": "low", "broken_ending": "low"}

# determinatives and compound-logogram heads that mark an object, a material, a place or food
REALIA_DET = r"GIŠ|UZU|DUG|NA₄|TÚG|KUŠ|URUDU|SÍG|GI|Ú|NINDA|URU|ḪUR\.SAG|ÍD|KUR|É|GAD|MUŠEN|KU₆|SAR|ZABAR|GIŠ\.ḪI\.A"
_REALIA_DET = re.compile(r"\{(" + REALIA_DET + r")\}")
_PLACE_DET = re.compile(r"\{(URU|KUR|ḪUR\.SAG|ÍD)\}")       # cities, lands, mountains, rivers
_ANIMAL_DET = re.compile(r"\{(MUŠEN|KU₆)\}")               # birds, fish
_REALIA_HEAD = re.compile(r"^(É|GIŠ|UZU|DUG|NA₄|TÚG|KUŠ|URUDU|NINDA)\.")
# the local and sentence particles that close a Hittite enclitic chain after a lost beginning
# (-ma-kán, but not the verb piš-kán-), and the words that open one
_CLITIC_END = re.compile(r"(^|-)(kán|ša-an|aš-ta|pát)-?$")
_CHAIN_START = re.compile(r"^(nu|EGIR-pa)-\S")   # nu-uš(-), EGIR-pa-ma-aš-; a bare nu- decides nothing

# Akkadographic (and Sumerographic) prepositions that TLHdig writes in one <w> with their noun
PREPOSITIONS = {"A-NA", "ANA", "A+NA", "I-NA", "INA", "I+NA", "ŠA", "ŠÀ", "ŠÁ", "IŠ-TU", "PA-NI", "PA-AN",
                "IT-TI", "QA-DU", "QA-DU₄", "TA", "AŠ-ŠUM", "ŠA-PAL", "A-DI"}


# syllabically written Akkadian prepositions (i-na, a-na); TLHdig tags them AKK, mostly without an
# analysis, and the rare noun analyses of the same form must not decide their class
AKK_FUNCTION = {"ina", "ana", "ištu", "itti", "aššum"}


def is_preposition(token: str) -> bool:
    """A preposition or a compound of prepositions joined by ˽ (A-NA˽PA-NI, IŠ-TU˽ŠA)."""
    return bool(token) and all(p in PREPOSITIONS for p in token.split("˽"))


def word_class_rule(attrs: dict, translit: str, lang: str) -> tuple[str, str]:
    """(word class, rule); the rule's confidence level is RULES[rule]."""
    tl = translit or ""
    word = attrs.get("trans") or ""
    if re.match(r"\{(m|f|M|F)\}", tl):                      # personal names, theophoric ones included
        return "agent", "determinative_agent"           # ({m}SUM-{D}KAL is a man, not a god)
    if _REALIA_HEAD.match(tl):                          # GIŠ.{D}INANNA "harp", É.DINGIR "temple"
        return "realia", "determinative_noun"
    if "{D}" in tl or word.startswith("DINGIR"):
        return "deity", "determinative_deity"
    if re.search(r"\{(LÚ|MUNUS)(\.〈?MEŠ〉?)?\}|\{(m|f)\}", tl) or re.match(r"(LÚ|MUNUS)\b", word):
        return "agent", "determinative_agent"
    if re.split(r"[-\s]", word)[0] in AGENT_LOGOGRAMS:
        return "agent", "agent_logogram"
    sel = (attrs.get("mrp0sel") or "").strip()
    if word in AKK_FUNCTION:
        return "function", "akkadian_function"
    own_lang = attrs.get("lg")
    lang = own_lang or lang                     # a word's own language tag overrides its line's
    mrps = {int(k[3:]): v for k, v in attrs.items() if re.fullmatch(r"mrp[1-9]\d*", k)}
    chosen = {}
    for n, l in re.findall(r"(\d+)([a-z]*)", sel):      # '1a', '3c 3d', '1all'
        chosen[int(n)] = "all" if l == "all" or chosen.get(int(n)) == "all" else chosen.get(int(n), "") + l
    picked = {n: mrps[n] for n in chosen if n in mrps}
    # a logogram (no lower-case sign: KI.MIN, DINGIR) in a foreign-language line is not a word of
    # that language, unless the word itself is tagged
    logogram = bool(word) and not re.search(r"[a-zšḫṣṭṯâêîûàèìùáéíú]", word) and not own_lang
    if (lang in FOREIGN or sel == "HURR") and not logogram:
        # a Hittite word inside a foreign-language line (nu=za, tai in a Hurrian line) keeps its
        # Hittite analysis when the editor selected one with no language marker
        if not (picked and all(not re.search(r"\b(LUW|PAL|HAT|HURR)\b", m) for m in picked.values())):
            return "foreign", "language"
    if not mrps:
        return no_analysis_rule(tl)
    pool = [(m, chosen[n]) for n, m in picked.items()] or [(m, "") for m in mrps.values()]
    pos = {candidate_pos(m, l) for m, l in pool} - {"unknown"}
    if len(pos) == 1:
        p = pos.pop()
        if p == "ambiguous":
            return "ambiguous", "analysis_ambiguous"
        rule = "analysis_selected" if picked else "analysis_unanimous"
        if p == "realia":
            return meaning_class(pool, tl), rule
        return ("other" if p == "number" else p), rule
    return ("ambiguous", "analysis_ambiguous") if pos else ("unknown", "no_analysis")


# A nominal word's class by meaning (decision of the philologist, 2026-10-17): realia are physical
# artifacts and buildings, ritual and cultic materials, food, plants and things; the other nouns are
# catalogued by the meaning of TLHdig's German gloss. labels/gloss_lexicon.tsv gives each gloss one
# label. It was drafted by Claude from the German glosses (not by a rule), committed as a fixed file,
# and can be corrected by hand; the names of gods, persons and places come from TLHdig's stem class.
LEXICON_FILE = Path(__file__).parent.parent / "labels" / "gloss_lexicon.tsv"
GLOSS_CLASS = {"realia": "realia", "person": "agent", "deity": "deity", "abstract": "abstract",
               "adjective": "adjective", "animal": "animal", "body": "body", "nature": "nature",
               "place": "place", "measure": "measure", "function": "function", "unknown": "other"}
_NAME_CLASS = (("35", "deity"), ("36", "deity"), ("37", "agent"), ("38", "agent"), ("39", "place"))


def _load_lexicon() -> dict:
    if not LEXICON_FILE.exists():
        return {}
    with open(LEXICON_FILE, encoding="utf-8") as f:
        return {r["gloss"]: GLOSS_CLASS[r["label"]] for r in csv.DictReader(f, delimiter="\t")}


LEXICON = _load_lexicon()


# a concrete gloss outranks the name stem class: stem class 36 also holds GUNNI "Herd" (hearth) and
# GÌR "Fuß aus Holz", deified things that are realia when written without {D}
_CONCRETE = {"realia", "animal", "body"}


def gloss_class(mrp: str) -> str:
    """Meaning class of one nominal analysis: a concrete gloss by its label, a name by its stem
    class, else its gloss's label."""
    f = [x.strip() for x in mrp.replace("①", "").split("@")]
    stem = f[3] if len(f) > 3 else ""
    label = LEXICON.get(f[1] if len(f) > 1 else "", "realia")
    if label in _CONCRETE:
        return label
    for prefix, cls in _NAME_CLASS:
        if stem == prefix or stem.startswith(prefix + "."):
            return cls
    return label


def meaning_class(pool, tl: str) -> str:
    """Class of a nominal word from the glosses of its analyses: one class if they agree; when they
    disagree and one reading is a thing (ZA.GÌN "blau" / "Lapislazuli", IM "Wind" / "Lehm"), realia;
    else `ambiguous`. A body part with the meat determinative ({UZU} NÍG.GIG) is ritual material."""
    classes = {gloss_class(m) for m, l in pool if candidate_pos(m, l) == "realia"} or {"realia"}
    if len(classes) > 1:
        return "realia" if "realia" in classes else "ambiguous"
    c = classes.pop()
    return "realia" if c == "body" and "{UZU}" in tl else c


def no_analysis_rule(tl: str) -> tuple[str, str]:
    """A word TLHdig gives no analysis: a realia determinative, then, for a broken word (a
    transliteration that begins or ends with a hyphen), an enclitic chain or a verbal ending."""
    if _PLACE_DET.search(tl):
        return "place", "determinative_noun"
    if _ANIMAL_DET.search(tl):
        return "animal", "determinative_noun"
    if _REALIA_DET.search(tl):
        return "realia", "determinative_noun"
    t = tl.strip().replace("(-)", "-")
    if t.startswith("-") or t.endswith("-"):
        core = t.strip("-")
        if (t.startswith("-") and _CLITIC_END.search(t)) or _CHAIN_START.match(core):
            return "function", "broken_clitic"
        if t.startswith("-") and core.endswith("an-zi"):
            return "verb", "broken_ending"
    return "unknown", "no_analysis"


def word_class(attrs: dict, translit: str, lang: str) -> str:
    return word_class_rule(attrs, translit, lang)[0]

# Display grouping shared by E11 (run_attribution.py) and the workshop playground: the six
# categories of StBoT 73 Table 4 with agents and deities together, and the rest as "Other words";
# and the three layers a feature belongs to (sign n-grams with any upper-case sign, i.e. a
# logogram or determinative, count as logographic writing).
CATEGORY = {"function": "Function words", "verb": "Verbs", "realia": "Realia",
            "agent": "Agents and deities", "deity": "Agents and deities", "place": "Places",
            "animal": "Animals, body, nature", "body": "Animals, body, nature", "nature": "Animals, body, nature",
            "abstract": "Abstract nouns", "adjective": "Adjectives", "foreign": "Foreign words"}
CATEGORIES = ["Function words", "Verbs", "Realia", "Agents and deities", "Places", "Animals, body, nature",
              "Abstract nouns", "Adjectives", "Foreign words", "Other words"]
LAYERS = ["Word form", "Syllabic spelling", "Logographic writing"]


def category(wclass: str) -> str:
    return CATEGORY.get(wclass, "Other words")


def layer(feature: str) -> str:
    """Layer of a 'both'-space feature: a word form, or a §-prefixed sign n-gram."""
    if not feature.startswith("§"):
        return "Word form"
    return "Logographic writing" if any(s[:1].isupper() for s in feature[1:].split("·")) else "Syllabic spelling"
