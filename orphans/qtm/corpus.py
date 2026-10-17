"""Load a token-level Hittite corpus (Zenodo 14266302 schema) into per-text documents.

Expected columns: txtid, lnr, cth_number, word, translit. An optional
`subgroup` column (e.g. CTH 701 a, a1, b ...) is carried through when present.
"""
import re
import pandas as pd

# editorial marks to drop before splitting into signs
_EDIT = re.compile(r"[\[\]⸢⸣()?!~′'<>«»#*]|\bx\b")
_SIGN_SPLIT = re.compile(r"[-.\s{}+˽]+")


def signs(translit: str) -> list[str]:
    """Split one transliterated word into sign values (case kept: logograms stay upper-case)."""
    t = _EDIT.sub("", str(translit))
    return [s for s in _SIGN_SPLIT.split(t) if s and s != "x" and not s.isdigit()]


def load(path: str, cths=None, min_words: int = 0) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    df = df.dropna(subset=["txtid", "word"])
    df["cth_number"] = df["cth_number"].astype(str)
    if cths is not None:
        df = df[df.cth_number.isin([str(c) for c in cths])]
    agg = {"cth_number": "first", "word": list, "translit": list}
    if "subgroup" in df.columns:
        agg["subgroup"] = "first"
    for col in ("lang", "wclass"):
        if col in df.columns:
            agg[col] = list
    docs = df.groupby("txtid", sort=False).agg(agg).reset_index()
    docs = docs.rename(columns={"word": "words", "translit": "translits", "lang": "langs", "wclass": "wclasses"})
    docs["words"] = docs.words.apply(lambda ws: [str(w) for w in ws])
    docs["signs"] = docs.translits.apply(lambda ts: [signs(t) for t in ts])
    docs["n_words"] = docs.words.str.len()
    return docs[docs.n_words >= min_words].reset_index(drop=True)
