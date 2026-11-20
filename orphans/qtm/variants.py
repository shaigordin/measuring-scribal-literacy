"""Damage-aware versions of the token table (decided with ShG, 2026-11-11).

  A  as published so far: every word and sign as the editors print it, restorations included.
  C  (main) only what is on the tablet, plus restorations the same text supports:
     - a sign counts if it is preserved or damaged (half brackets, or partly in [ ]), also when
       its reading is marked uncertain (?); restored ([ ]), omitted (〈 〉) and lost (…) signs
       do not count, and become ∅ in `translit`, so no sign n-gram spans them;
     - a word counts if at least half its signs count (MIN_PRESENT), or if the same word form
       is attested at least half-preserved elsewhere in the same text (`support` = "same_text");
       restorations supported only by duplicates or parallels are not used (no tautology);
     - words with no signs to judge (bare numbers) count as written;
     - `lang` is the word's own language tag where TLHdig gives one (`lang_line` keeps the line's).
  B  (diagnostic) like C without the same-text support.

`translit_ed` keeps the editors' transliteration for display. Rows of words that do not count
get an empty `word`, so qtm.corpus.load drops them, as it drops illegible words.

    python -m qtm.variants data/tokens.csv data/tokens_C.csv --variant C
"""
import argparse
import re

import pandas as pd

from .corpus import signs

_SPLIT = re.compile(r"([-.\s{}+˽]+)")
MIN_PRESENT = 0.5
GAP = "∅"
PRESENT = set("PD")
MARK_COLS_A = ["txtid", "cth_number", "source", "lnr", "lang", "word", "translit", "wclass", "wc_rule", "wc_conf"]


def model_translit(translit, status):
    """Editors' translit with every sign not on the tablet replaced by ∅, formatting kept
    (signs as qtm.corpus.signs; falls back to the editors' translit if they don't align)."""
    if not status or len(status) != len(signs(translit)):
        return translit
    out, i = [], 0
    for part in _SPLIT.split(translit):
        if _SPLIT.fullmatch(part) or not part:
            out.append(part)
            continue
        n = len(signs(part))
        if n and i + n <= len(status) and any(st not in PRESENT for st in status[i:i + n]):
            out.append(GAP if all(st not in PRESENT for st in status[i:i + n]) else part)
        else:
            out.append(part)
        i += n
    return "".join(out) if i == len(status) else translit


def present_share(df):
    n = df.n_signs.astype(float)
    p = (df.n_preserved + df.n_damaged).astype(float)
    return (p / n.where(n > 0)).fillna(1.0)  # no signs to judge (numbers, unaligned): as written


def make(df, variant="C"):
    if variant == "A":
        return df[MARK_COLS_A].copy()
    df = df.copy()
    if "lang_word" in df.columns:  # a word's own language tag (lg on <w>) overrides its line's
        df["lang_line"] = df.lang
        df["lang"] = df.lang_word.where(df.lang_word.fillna("") != "", df.lang)
    df["present_share"] = present_share(df).round(3)
    ok = df.present_share >= MIN_PRESENT
    has_word = df.word.fillna("") != ""
    df["support"] = ""
    df.loc[ok & has_word, "support"] = "on_tablet"
    if variant == "C":
        good = df[ok & has_word].groupby("txtid").word.agg(set)
        inside = pd.Series([w in good.get(t, ()) for t, w in zip(df.txtid, df.word.fillna(""))], index=df.index)
        rescue = has_word & ~ok & inside
        df.loc[rescue, "support"] = "same_text"
    df["translit_ed"] = df.translit
    df["translit"] = [model_translit(t, s) for t, s in zip(df.translit.fillna(""), df.status.fillna(""))]
    df.loc[has_word & (df.support == ""), "word"] = ""
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tokens")
    ap.add_argument("out")
    ap.add_argument("--variant", choices="ABC", default="C")
    a = ap.parse_args()
    df = pd.read_csv(a.tokens, low_memory=False, dtype={"cth_number": str, "status": str, "layer": str, "flags": str},
                     keep_default_na=False, na_values={"word": [""], "translit": [""]})
    out = make(df, a.variant)
    out.to_csv(a.out, index=False)
    w = df.word.notna() & (df.word != "")
    kept = out.word.notna() & (out.word != "")
    print(f"variant {a.variant}: {int(kept.sum())} of {int(w.sum())} analysed words count"
          + (f"; same-text support {int((out.support == 'same_text').sum())}" if a.variant == "C" else ""))


if __name__ == "__main__":
    main()
