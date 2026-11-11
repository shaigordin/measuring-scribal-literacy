"""Parse the TLHdig XML release (Zenodo 10.5281/zenodo.20328284) into a token table.

One row per word: txtid, cth_number, source (HFR/TLH/...), lnr, lang, word, translit, wclass,
wc_rule, wc_conf. A <w> that holds an Akkadographic preposition and its noun (A-NA {GIŠ}BANŠUR)
becomes two rows, the preposition and the noun (see qtm.wordclass).
`word` is the normalised form from the `trans` attribute; `translit` is the sign
sequence with determinatives as {DET}. `wclass` is the word class from qtm.wordclass, `wc_rule` the
rule that set it and `wc_conf` its confidence; manual corrections from a CSV (word, translit,
wclass, note, reviewer; translit empty = every occurrence of the word) override them. Words that are wholly or partly illegible
(`%` in trans, only `x` signs, or only `…`) keep their translit but get an empty `word`.

Sign status and editorial marks (added 2026-11-11; they do not change `word` or `translit`):
`lang_word` is the word's own language tag where TLHdig gives one (lg on <w>), else its line's.
`status` has one letter per sign of qtm.corpus.signs(translit), in order: P preserved, D damaged
(half brackets, or partly inside square brackets), R restored by the editor (wholly inside [ ]),
L lost and not restored (…), O omitted by the scribe and supplied by the editor (〈x〉).
`layer` is aligned the same way: H phonetic (Hittite or other language), A Akkadogram (<aGr>),
S Sumerogram (<sGr>), d determinative. `flags` holds the marks a sign carries, one group per
sign joined by '.': u uncertain reading (?), e emended (!, sic), r written over an erasure,
a added by the scribe, s superfluous: written in error (〈〈x〉〉) or followed by a <surpl> sign. Both strings are empty when the XML signs could not be
aligned with translit (counted in parse.log). n_* columns count the signs of each kind.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from lxml import etree

from .corpus import signs as split_signs
from .wordclass import RULES, is_preposition, word_class_rule

FOLDER = re.compile(r"CTH (\d+)[^_]*_XML_(\w+)")
SKIP = {"space", "del_in", "del_fin", "laes_in", "laes_fin", "corr", "note", "gap"}


def _text(node):
    """Sign text of an element; determinatives become {DET}, sign groups are space-separated."""
    tag = etree.QName(node).localname if isinstance(node.tag, str) else ""
    if tag in SKIP:
        return ""
    inner = (node.text or "") + "".join(_text(c) + (c.tail or "") for c in node)
    if tag == "d":
        return "{" + inner + "}"
    if tag in ("aGr", "sGr"):
        return " " + inner + " "
    return inner


MARKS = {"?": "u", "(?)": "u", "??": "u", "!": "e", "sic": "e", "!?": "eu", "?!": "eu",
         "(over erasure)": "r"}
OPEN, CLOSE = "〈⟨", "〉⟩"
_SEP = re.compile(r"[-.\s{}+˽]+")
_DROP = re.compile(r"[\[\]⸢⸣()?!~′'<>«»#*]")


class _State:
    def __init__(self):
        self.restored = self.damaged = self.erased = self.added = False


def _local(node):
    return node.tag.split("}")[-1] if isinstance(node.tag, str) else ""


def _chars(node, st, out, layer="H", top=True):
    """(char, status, layer, flags) for every character of a word's sign text, in order; updates
    the bracket state `st`, which runs across words and lines as the milestones do."""
    tag = "" if top else _local(node)
    if tag in ("del_in", "del_fin"):
        st.restored = tag == "del_in"
    elif tag in ("laes_in", "laes_fin"):
        st.damaged = tag == "laes_in"
    elif tag in ("ras_in", "ras_fin"):
        st.erased = tag == "ras_in"
    elif tag in ("add_in", "add_fin"):
        st.added = tag == "add_in"
    elif tag in ("corr", "surpl"):
        # surpl: a superfluous sign the editor deletes (its value is in @c, not in the text)
        f = "s" if tag == "surpl" else MARKS.get((node.get("c") or "").strip(), "")
        for i in range(len(out) - 1, -1, -1):  # the mark belongs to the sign just before it
            if not _SEP.fullmatch(out[i][0]):
                out[i] = out[i][:3] + (out[i][3] + f,)
                break
    elif tag in ("space", "note", "gap"):
        pass
    else:
        lay = {"aGr": "A", "sGr": "S", "d": "d"}.get(tag, layer)
        if tag == "d":
            out.append(("{", "P", "d", ""))
        if tag in ("aGr", "sGr"):
            out.append((" ", "P", lay, ""))

        def add(t):
            for ch in t or "":
                stt = "R" if st.restored else ("D" if st.damaged else "P")
                fl = ("r" if st.erased else "") + ("a" if st.added else "")
                out.append((ch, stt, lay, fl))
        add(node.text)
        for c in node:
            _chars(c, st, out, lay, False)
            add(c.tail)
        if tag == "d":
            out.append(("}", "P", "d", ""))
        if tag in ("aGr", "sGr"):
            out.append((" ", "P", lay, ""))
    return out


def sign_marks(chars, translit):
    """Status, layer and flags per sign of split_signs(translit), or None if they don't align."""
    depth, marked = 0, []
    for c in chars:  # angle-bracket depth of every character
        if c[0] in OPEN:
            depth += 1
        elif c[0] in CLOSE:
            depth = max(depth - 1, 0)
        marked.append(c + (depth,))
    segs, cur = [], []
    for c in marked + [(" ", "P", "H", "", 0)]:
        if _SEP.fullmatch(c[0]):
            if cur:
                segs.append(cur)
            cur = []
        elif not _DROP.fullmatch(c[0]):
            cur.append(c)
    segs = [g for g in segs if "".join(c[0] for c in g) not in ("x", "")
            and not "".join(c[0] for c in g).isdigit()]
    if ["".join(c[0] for c in g) for g in segs] != split_signs(translit):
        return None
    status, layer, flags = [], [], []
    for g in segs:
        st = {c[1] for c in g}
        lost = "".join(c[0] for c in g) == "…"
        # 〈x〉: sign the scribe omitted, supplied by the editor (not on the tablet);
        # 〈〈x〉〉: sign the scribe wrote in error (on the tablet, deleted by the editor)
        body = [c for c in g if c[0] not in OPEN + CLOSE]
        omitted = bool(body) and all(c[4] == 1 for c in body)
        status.append("L" if lost else "O" if omitted else "R" if st == {"R"} else "P" if st == {"P"} else "D")
        layer.append(g[0][2])
        fl = set("".join(c[3] for c in g)) | ({"s"} if any(c[4] >= 2 for c in body) else set())
        flags.append("".join(sorted(fl)))
    return "".join(status), "".join(layer), ".".join(flags)


def mark_words(tree):
    """Sign marks for every <w>, walking the document in order so brackets carry across words."""
    st, marks = _State(), {}

    def visit(node):
        tag = _local(node)
        if tag == "w":
            marks[node] = _chars(node, st, [])
            return
        if tag in ("del_in", "del_fin", "laes_in", "laes_fin", "ras_in", "ras_fin", "add_in", "add_fin"):
            _chars(node, st, [], top=False)
        for c in node:
            visit(c)
    if tree.getroot() is not None:
        visit(tree.getroot())
    return marks


EMPTY = ("", "", "")
MARK_COLS = ["lang_word", "status", "layer", "flags", "n_signs", "n_preserved", "n_damaged", "n_restored", "n_lost", "n_omitted",
             "n_akkadogram", "n_sumerogram", "n_uncertain", "n_emended", "n_erasure", "n_added",
             "n_superfluous"]


def mark_cols(m, lang_word=""):
    status, layer, flags = m or EMPTY
    f = flags.split(".") if flags else []
    return (lang_word, status, layer, flags, len(status), status.count("P"), status.count("D"), status.count("R"), status.count("L"), status.count("O"),
            layer.count("A"), layer.count("S"), sum("u" in x for x in f), sum("e" in x for x in f),
            sum("r" in x for x in f), sum("a" in x for x in f), sum("s" in x for x in f))


def _split_marks(m, k):
    """Marks of the first k signs and of the rest (for a preposition split off its noun)."""
    if not m:
        return None, None
    s, l, f = m
    fl = f.split(".")
    return (s[:k], l[:k], ".".join(fl[:k])), (s[k:], l[k:], ".".join(fl[k:]))


def _translit(w):
    t = (w.text or "") + "".join(_text(c) + (c.tail or "") for c in w)
    t = re.sub(r"\s*-\s*", "-", t)
    return re.sub(r"\s+", " ", t).strip()


def parse_file(path, cth, source, stats=None):
    stats = {} if stats is None else stats
    tree = etree.parse(str(path), etree.XMLParser(recover=True, huge_tree=True))
    rows, lnr, lang, txtid = [], None, None, None
    doc = tree.find(".//docID")
    txtid = doc.text.strip() if doc is not None and doc.text else Path(path).stem
    marks = mark_words(tree)
    stats["words"] = stats.get("words", 0)
    for el in tree.iter("lb", "w"):
        if el.tag == "lb":
            lnr, lang = el.get("lnr"), el.get("lg")
            continue
        tl = _translit(el)
        if not tl:
            continue
        m = sign_marks(marks.get(el, []), tl)
        wl = el.get("lg") or lang  # TLHdig tags single words in another language (@hu ...) on <w>
        stats["words"] += 1
        stats["unaligned"] = stats.get("unaligned", 0) + (m is None)
        trans = el.get("trans") or ""
        # illegible: '%' in trans, only x signs, or only '…' (TLHdig's mark for a lost word)
        word = "" if ("%" in trans or not re.search(r"[^x\s\-.…]", tl.replace("x", ""))
                      or not trans.strip(" …")) else trans
        if not word:
            rows.append((txtid, cth, source, lnr, lang, word, tl, "", "") + mark_cols(m, wl))
            continue
        head, _, rest = word.partition(" ")
        if is_preposition(head):
            # the preposition, then (if any) the noun with its own analysis
            rtl = tl[len(head):].strip() if tl.startswith(head + " ") else tl
            mh, mr = _split_marks(m, len(split_signs(head))) if rest and rtl != tl else (m, None)
            rows.append((txtid, cth, source, lnr, lang, head, head, "function", "preposition_split") + mark_cols(mh, wl))
            if rest:
                wc, rule = word_class_rule({**el.attrib, "trans": rest}, rtl, lang)
                rows.append((txtid, cth, source, lnr, lang, rest, rtl, wc, rule) + mark_cols(mr if rtl != tl else m, wl))
            continue
        wc, rule = word_class_rule(el.attrib, tl, lang)
        rows.append((txtid, cth, source, lnr, lang, word, tl, wc, rule) + mark_cols(m, wl))
    return rows


def apply_corrections(df, path):
    """Manual word-class corrections; a row with a translit applies only to that spelling."""
    if not path or not Path(path).exists():
        return df
    cor = pd.read_csv(path, dtype=str).fillna("")
    for _, c in cor.iterrows():
        hit = df.word == c.word
        if c.translit:
            hit &= df.translit == c.translit
        df.loc[hit, ["wclass", "wc_rule"]] = [c.wclass, "manual"]
    return df


def parse_release(root, cths=None):
    out, stats = [], {}
    for d in sorted(Path(root).iterdir()):
        m = FOLDER.match(d.name)
        if not m or (cths and m.group(1) not in cths):
            continue
        for f in sorted(d.rglob("*.xml")):  # sorted: same row order on every filesystem
            try:
                out += parse_file(f, m.group(1), m.group(2), stats)
            except Exception as e:  # malformed files are logged, not fatal
                print(f"skip {f}: {e}", file=sys.stderr)
    print(f"sign marks: {stats.get('unaligned', 0)} of {stats.get('words', 0)} words not aligned", file=sys.stderr)
    df = pd.DataFrame(out, columns=["txtid", "cth_number", "source", "lnr", "lang", "word", "translit", "wclass",
                                    "wc_rule"] + MARK_COLS)
    # the same manuscript can appear in an HFR and a TLH folder: keep the HFR copy
    rank = df.source.map({"HFR": 0}).fillna(1)
    keep = df.assign(r=rank).groupby("txtid").r.transform("min") == rank
    return df[keep].reset_index(drop=True)


BACKOFF_MIN, BACKOFF_AGREE = 5, 0.9


def backoff(df):
    """Words the editors left unselected (ambiguous, or only unselected candidates) take the class
    the editors selected for the same word form elsewhere, when that choice is clear."""
    sel = df[df.wc_rule == "analysis_selected"]
    share = sel.groupby("word").wclass.value_counts(normalize=True)
    n = sel.groupby("word").size()
    top = share[share.groupby(level=0).transform("max") == share].reset_index()
    top = top[top.proportion >= BACKOFF_AGREE].drop_duplicates("word").set_index("word").wclass
    top = top[n.reindex(top.index) >= BACKOFF_MIN]
    hit = df.wc_rule.isin(["analysis_ambiguous", "analysis_unanimous", "no_analysis"]) & df.word.isin(top.index)
    new = df.loc[hit, "word"].map(top)
    change = hit & (new.reindex(df.index) != df.wclass)
    df.loc[change, "wclass"] = new[change[hit].values].values
    df.loc[change, "wc_rule"] = "selected_elsewhere"
    return df


def finish(df, corrections=None):
    df = backoff(df)
    df = apply_corrections(df, corrections)
    df["wc_conf"] = df.wc_rule.map(RULES).fillna("")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("out")
    ap.add_argument("cths", nargs="?")
    ap.add_argument("--corrections", default=str(Path(__file__).parent.parent / "labels" / "wordclass_corrections.csv"))
    a = ap.parse_args()
    df = finish(parse_release(a.root, a.cths.split(",") if a.cths else None), a.corrections)
    df.to_csv(a.out, index=False)
    print(df.groupby("cth_number").txtid.nunique().to_string())
