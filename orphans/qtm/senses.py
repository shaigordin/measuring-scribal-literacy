"""Context rules for word senses (the dictionary method, written down as data).

One German gloss can cover several senses that belong to different word classes: "Horn" is an animal's
horn (body), a vessel or a musical instrument (realia), or the horn of the moon in an omen (part of a
celestial body). TLHdig's analyses give the gloss but not the sense, so qtm.wordclass classes every
occurrence alike. labels/sense_rules.csv records, per lemma or gloss, the contexts that decide the sense,
with passage evidence and a dictionary reference, and apply_senses() applies them after the word-class
rules (qtm.tlhdig.finish). Every token records the rule that fired (`sense_rule`) and the sense
(`sense`), and the class it had before (`wclass_before_sense`); tokens no rule matches keep their class and an empty `sense_rule`.

Columns of labels/sense_rules.csv:
  rule_id       unique id, e.g. horn-01
  gloss         the German gloss the token's analysis carries (exact, one of the '|'-joined glosses)
  lemma         regular expression on the token's lemma ('' = any lemma with that gloss)
  scope         where the condition is looked for: self (the token's own transliteration), prev / next
                (the neighbouring word in the same line), window (the 4 words before and after, same
                line), line (the whole line), prev_class / next_class (the word class of the neighbouring
                word, as the word-class rules gave it), always (no condition: the default for the gloss)
  pattern       regular expression searched in that scope (brackets and half brackets removed)
  wclass        the class the token gets (qtm.wordclass classes: realia, body, nature, animal ...)
  sense         a short name of the sense (vessel, instrument, animal horn, celestial ...)
  evidence      2-3 passages (txtid line) where the rule applies, from the concordance
  dictionary    the dictionary entry checked (CHD for L-Š and P, HW² for A-Ḫ, eDiAna for Luwian, HED
                otherwise), or "none checked"
  decided_by    draft (written by Claude, not yet reviewed) or ShG
  note          free text
  unless        optional 'scope:pattern': the rule does not apply where this matches
Rules for one gloss are tried in file order; the first that matches decides. Only nominal and ambiguous
tokens are changed (a token the word-class rules made a verb, function word, foreign word, deity or agent
by a determinative keeps its class); a rule sets a class from SETTABLE.
"""
import re
import warnings
from pathlib import Path

import pandas as pd

RULES_FILE = Path(__file__).parent.parent / "labels" / "sense_rules.csv"
NOMINAL = {"realia", "abstract", "body", "nature", "animal", "place", "measure", "adjective"}
OPEN = NOMINAL | {"ambiguous"}   # classes a sense rule may change
# classes a sense rule may set: the nominal ones, persons and gods (a title head, a deified mountain),
# scribal marks (colophon formulae, left out of the profiles like function words) and numbers
SETTABLE = NOMINAL | {"agent", "deity", "scribal", "number"}
SCOPES = {"always", "self", "prev", "next", "window", "line", "prev_class", "next_class"}
_UNBRACKET = re.compile(r"[\[\]⸢⸣<>()?!〈〉]")
warnings.filterwarnings("ignore", "This pattern is interpreted as a regular expression")
_ALT = re.compile(r"\{\s*([a-z])\s*→\s*([^}]*)\}")


def analyses(attrs: dict):
    """(lemmas, glosses, selected) of one <w>: the analyses the editor selected (mrp0sel), else all
    candidate analyses, as qtm.wordclass.word_class_rule pools them. lemmas and glosses are '|'-joined
    and sorted; selected is '1' when the editor selected an analysis."""
    sel = (attrs.get("mrp0sel") or "").strip()
    mrps = {int(k[3:]): v for k, v in attrs.items() if re.fullmatch(r"mrp[1-9]\d*", k)}
    picked = {int(n) for n, _ in re.findall(r"(\d+)([a-z]*)", sel)} & set(mrps)
    pool = [mrps[n] for n in sorted(picked)] or list(mrps.values())
    lem, glo = set(), set()
    for m in pool:
        f = [x.strip() for x in m.replace("①", "").split("@")]
        if len(f) > 1 and f[0]:
            lem.add(f[0]); glo.add(f[1])
    return "|".join(sorted(lem)), "|".join(sorted(glo)), "1" if picked else ""


def named_annotator(tree) -> str:
    """'1' when the file's <annotation> names an annotator (not 'auto' or empty)."""
    eds = [a.get("editor", "").strip() for a in tree.iterfind(".//annotation/annot")]
    return "1" if any(e and e.lower() != "auto" for e in eds) else ""


def load_rules(path=RULES_FILE) -> pd.DataFrame:
    if not Path(path).exists():
        return pd.DataFrame()
    r = pd.read_csv(path, dtype=str, keep_default_na=False)
    if "unless" not in r:
        r["unless"] = ""
    bad = set(r.wclass) - SETTABLE
    if bad:
        raise ValueError(f"{path}: rules may not set the classes {bad}")
    scopes = set(r.scope) | {u.split(":", 1)[0] for u in r.unless if u}
    if scopes - SCOPES:
        raise ValueError(f"{path}: unknown scopes {scopes - SCOPES}")
    if r.rule_id.duplicated().any():
        raise ValueError(f"{path}: duplicate rule_id {sorted(r.rule_id[r.rule_id.duplicated()])}")
    return r


def line_index(df: pd.DataFrame):
    """The words of every line (brackets removed) and each row's line and position, computed once."""
    tl = df.translit.fillna("").map(lambda t: _UNBRACKET.sub("", t))
    line = df.txtid.astype(str) + "|" + df.lnr.fillna("").astype(str)
    return (tl.groupby(line, sort=False).agg(list).to_dict(), line.to_numpy(),
            df.groupby(line, sort=False).cumcount().to_numpy(), df.wclass.fillna("").groupby(line, sort=False).agg(list).to_dict())


def contexts(li, idx) -> pd.DataFrame:
    """self / prev / next / window (4 words either side) / line strings, and left / right, for rows idx;
    li is line_index(df) of a frame in text order."""
    lines, line, pos, classes = li
    out = []
    for i in idx:
        words, p, cl = lines[line[i]], pos[i], classes[line[i]]
        out.append({"self": words[p], "prev": words[p - 1] if p > 0 else "",
                    "next": words[p + 1] if p + 1 < len(words) else "",
                    "window": " ".join(words[max(0, p - 4):p] + words[p + 1:p + 5]), "line": " ".join(words),
                    "left": " ".join(words[max(0, p - 4):p]), "right": " ".join(words[p + 1:p + 5]),
                    "prev_class": cl[p - 1] if p > 0 else "", "next_class": cl[p + 1] if p + 1 < len(cl) else ""})
    return pd.DataFrame(out, index=list(idx))


def gloss_hits(df: pd.DataFrame, gloss: str, lemma: str = "") -> pd.Series:
    g = df.gloss.fillna("").str.split("|").map(lambda gs: gloss in gs)
    if lemma:
        g &= df.lemma.fillna("").str.contains(lemma, regex=True)
    return g


def match(rule, ctx: pd.DataFrame) -> pd.Series:
    m = pd.Series(True, index=ctx.index) if rule.scope == "always" else ctx[rule.scope].str.contains(rule.pattern, regex=True)
    if rule.unless:
        sc, pat = rule.unless.split(":", 1)
        m &= ~ctx[sc].str.contains(pat, regex=True)
    return m


def apply_senses(df: pd.DataFrame, path=RULES_FILE) -> pd.DataFrame:
    """Set wclass, sense and sense_rule from labels/sense_rules.csv (see the module docstring)."""
    df["sense"], df["sense_rule"], df["wclass_before_sense"] = "", "", ""
    rules = load_rules(path)
    if rules.empty or "gloss" not in df.columns:
        return df
    li = line_index(df)
    for (gloss, lemma), rs in rules.groupby(["gloss", "lemma"], sort=False):
        cand = gloss_hits(df, gloss, lemma) & df.wclass.isin(OPEN) & (df.sense_rule == "")
        idx = df.index[cand]
        if not len(idx):
            continue
        ctx = contexts(li, idx)
        open_ = pd.Series(True, index=idx)
        for _, r in rs.iterrows():
            hit = open_ & match(r, ctx)
            h = hit[hit].index
            df.loc[h, "wclass_before_sense"] = df.loc[h, "wclass"]
            df.loc[h, ["wclass", "sense", "sense_rule"]] = [r.wclass, r.sense, r.rule_id]
            open_ &= ~hit
    return df
