"""Independent check of the noun meaning classes in labels/gloss_lexicon.tsv (drafted by Claude) against
WordNet supersenses.

Each German gloss is looked up in Open German WordNet (OdeNet 1.4, CC BY-SA 4.0). Through the synset's
Interlingual Index (ILI) link we take the Princeton WordNet 3.0 synset (OMW English Wordnet 1.4) and its
lexicographer file, the supersense (noun.person, noun.artifact, adj.all ...). The FIRST OdeNet sense
gives the WordNet class; a gloss is
  matched    if all its senses give the same class,
  ambiguous  if its senses give more than one class (the first sense is still used),
  missing    if OdeNet has no sense with an ILI link to Princeton WordNet.
Glosses are normalised before lookup: "(?)", parenthesised notes and quotation marks are dropped,
alternatives ("/" between whole words, ",", ";", " oder ") are tried in order, forms under three letters are skipped, and for a phrase the last word, then the
first word, is tried (never a function word from STOP) ("warmes Brot" -> "Brot"). How each gloss matched is recorded in match_level.

The comparison uses the display grouping of qtm.wordclass.CATEGORY: person and deity -> agent, body and
nature -> body/nature. Claude's function and unknown labels have no WordNet counterpart and are left out.
SUPERSENSE below is the fixed supersense -> class table. Agreement is reported over the glosses WordNet
covers (matched or ambiguous), type-weighted (each gloss once) and token-weighted (by its token count),
with Cohen's kappa for both, and the confusion matrices.

A stratified sample of disagreements is drawn for the philologist's audit: the sample size is shared
among the (Claude class, WordNet class) pairs in proportion to their tokens (largest remainder, at least
one per pair while the size allows), and within a pair glosses are drawn with probability proportional
to their tokens (seed 0).

Usage: python check_gloss_wordnet.py [--lexicon labels/gloss_lexicon.tsv] [--wn-data data/wn]
           [--out results/wordnet_check] [--sample 50]
Writes OUT/gloss_wordnet.csv (every gloss), OUT/wordnet_check.json, OUT/wordnet_audit_sample.csv.
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

ODENET, PWN = "odenet:1.4", "omw-en:1.4"

# Claude's labels, grouped as in qtm.wordclass.CATEGORY
GROUP = {"person": "agent", "deity": "agent", "realia": "realia", "abstract": "abstract", "place": "place",
         "animal": "animal", "body": "body/nature", "nature": "body/nature", "measure": "measure",
         "adjective": "adjective"}  # function, unknown: no WordNet counterpart

# Princeton WordNet lexicographer file -> our class. Realia (philologist's decision 2026-10-17) are
# physical artifacts, buildings, ritual and cultic materials, food, plants and things.
SUPERSENSE = {
    "noun.person": "agent", "noun.group": "agent",
    "noun.artifact": "realia", "noun.food": "realia", "noun.plant": "realia", "noun.substance": "realia",
    "noun.possession": "realia",
    "noun.animal": "animal",
    "noun.body": "body/nature", "noun.object": "body/nature", "noun.phenomenon": "body/nature",
    "noun.location": "place",
    "noun.quantity": "measure",
    "noun.act": "abstract", "noun.attribute": "abstract", "noun.cognition": "abstract",
    "noun.communication": "abstract", "noun.event": "abstract", "noun.feeling": "abstract",
    "noun.motive": "abstract", "noun.process": "abstract", "noun.relation": "abstract",
    "noun.shape": "abstract", "noun.state": "abstract", "noun.time": "abstract", "noun.Tops": "abstract",
    "adj.all": "adjective", "adj.pert": "adjective", "adj.ppl": "adjective",
}  # verb.* and adv.all -> "other" (no noun or adjective class)
CLASSES = ["agent", "realia", "abstract", "place", "animal", "body/nature", "measure", "adjective", "other"]


# function words never stand for a phrase ("ein Körperteil", "mit ašuša- versehen", "Plural von TUR")
STOP = {"ein", "eine", "einer", "eines", "der", "die", "das", "des", "dem", "den", "mit", "von", "zum", "zur",
        "für", "aus", "auf", "als", "und", "so", "plural", "art", "sorte"}


def candidates(gloss):
    g = gloss.replace("(?)", "").replace("?", "")
    g = re.sub(r"(?<=\w)\([^)]*\)", "", g)  # inside a word: "Sonne(ngottheit)" -> "Sonne"
    g = re.sub(r"\([^)]*\)", " ", g)
    g = re.sub(r"[‘’'\"“”„°\[\]]", "", g)
    # "/" separates alternatives ("schwer/Würdenträger"), not spelling variants ("Tele/ipinu", "Mi/era")
    if not re.search(r"\w/[a-zäöü]", g) or g == g.lower():
        g = g.replace("/", ";")
    alts = [a.strip() for a in re.split(r"[,;]| oder ", g) if a.strip()]
    out = []
    for a in alts:
        out.append((a, "exact" if a == gloss.strip() else "alternative"))
    for a in alts:
        w = a.split()
        if len(w) > 1:
            out += [(w[-1], "head_last_word"), (w[0], "head_first_word")]
    seen, res = set(), []
    for c, lvl in out:
        if c not in seen and len(c) >= 3 and c.lower() not in STOP:
            seen.add(c); res.append((c, lvl))
    return res


def lookup(de, en, gloss):
    for form, lvl in candidates(gloss):
        senses = []
        for s in de.synsets(form):
            e = en.synsets(ili=s.ili) if s.ili else []
            if e:
                lf = e[0].lexfile() or ""
                senses.append((lf, SUPERSENSE.get(lf, "other"), e[0].lemmas()[0] if e[0].lemmas() else ""))
        if senses:
            classes = {c for _, c, _ in senses}
            return {"form": form, "match_level": lvl, "status": "matched" if len(classes) == 1 else "ambiguous",
                    "supersense": senses[0][0], "wordnet_class": senses[0][1], "english": senses[0][2],
                    "all_classes": "|".join(sorted(classes)), "n_senses": len(senses)}
    return {"form": "", "match_level": "", "status": "missing", "supersense": "", "wordnet_class": "",
            "english": "", "all_classes": "", "n_senses": 0}


def agreement(df, w=None):
    y1, y2 = df.claude_class.to_numpy(), df.wordnet_class.to_numpy()
    wt = None if w is None else df[w].to_numpy(float)
    acc = float(np.average(y1 == y2, weights=wt)) if len(df) else None
    kap = float(cohen_kappa_score(y1, y2, labels=CLASSES, sample_weight=wt)) if len(df) else None
    cm = confusion_matrix(y1, y2, labels=CLASSES, sample_weight=wt)
    return {"agreement": round(acc, 3), "kappa": round(kap, 3),
            "confusion": {"rows_claude_cols_wordnet": CLASSES, "matrix": cm.round(0).astype(int).tolist()}}


def sample_disagreements(dis, n, seed=0):
    rng = np.random.default_rng(seed)
    dis = dis[dis.tokens > 0]
    mass = dis.groupby(["claude_class", "wordnet_class"]).tokens.sum().sort_values(ascending=False)
    k = min(n, int(len(dis)))
    quota = mass / mass.sum() * k
    alloc = np.floor(quota).astype(int)
    if k >= len(mass):  # at least one per pair
        alloc[alloc == 0] = 1
    while alloc.sum() > k:
        alloc[alloc.idxmax()] -= 1
    rem = (quota - np.floor(quota)).sort_values(ascending=False)
    for p in rem.index:
        if alloc.sum() >= k:
            break
        alloc[p] += 1
    rows = []
    for p, m in alloc.items():
        g = dis[(dis.claude_class == p[0]) & (dis.wordnet_class == p[1])]
        m = min(m, len(g))
        if m:
            idx = rng.choice(len(g), size=m, replace=False, p=(g.tokens / g.tokens.sum()).to_numpy())
            rows.append(g.iloc[np.sort(idx)])
    return pd.concat(rows) if rows else dis.iloc[:0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", default="labels/gloss_lexicon.tsv")
    ap.add_argument("--wn-data", default="data/wn")
    ap.add_argument("--out", default="results/wordnet_check")
    ap.add_argument("--sample", type=int, default=50)
    a = ap.parse_args()
    import wn
    wn.config.data_directory = a.wn_data
    have = {f"{l.id}:{l.version}" for l in wn.lexicons()}
    for lex in (ODENET, PWN):
        if lex not in have:
            wn.download(lex, progress_handler=None)
    de, en = wn.Wordnet(ODENET), wn.Wordnet(PWN)

    lex = pd.read_csv(a.lexicon, sep="\t", dtype={"gloss": str}, keep_default_na=False)
    lex["tokens"] = pd.to_numeric(lex.tokens, errors="coerce").fillna(0).astype(int)
    lex["claude_class"] = lex.label.map(GROUP)
    res = pd.DataFrame([lookup(de, en, g) for g in lex.gloss])
    df = pd.concat([lex, res], axis=1)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "gloss_wordnet.csv", index=False)

    comp = df[df.claude_class.notna()]
    cov = comp[comp.status != "missing"]
    tot = lambda d: int(d.tokens.sum())
    rep = {
        "wordnets": {"german": "Open German WordNet (OdeNet) 1.4, CC BY-SA 4.0", "english": "OMW English Wordnet 1.4 (Princeton WordNet 3.0)",
                     "link": "Interlingual Index (ILI)", "sense": "first OdeNet sense"},
        "supersense_to_class": SUPERSENSE,
        "glosses": {"all": int(len(df)), "compared": int(len(comp)), "left_out_function_unknown": int(df.claude_class.isna().sum()),
                    "status": comp.status.value_counts().to_dict(),
                    "status_tokens": comp.groupby("status").tokens.sum().astype(int).to_dict(),
                    "match_level": cov.match_level.value_counts().to_dict()},
        "coverage": {"types": round(len(cov) / len(comp), 3), "tokens": round(tot(cov) / max(1, tot(comp)), 3),
                     "by_claude_class_types": {c: round(float((g.status != "missing").mean()), 3) for c, g in comp.groupby("claude_class")},
                     "without_names_types": None},
        "type_weighted": agreement(cov),
        "token_weighted": agreement(cov, "tokens"),
        "matched_only": {"type_weighted": agreement(cov[cov.status == "matched"]),
                         "token_weighted": agreement(cov[cov.status == "matched"], "tokens")},
        "any_sense_agrees": {"types": round(float(np.mean([c in s.split("|") for c, s in zip(cov.claude_class, cov.all_classes)])), 3),
                             "tokens": round(float(np.average([c in s.split("|") for c, s in zip(cov.claude_class, cov.all_classes)], weights=cov.tokens)), 3)},
        "by_claude_class": {c: {"n": int(len(g)), "agreement_types": round(float((g.claude_class == g.wordnet_class).mean()), 3),
                                "agreement_tokens": round(float(np.average(g.claude_class == g.wordnet_class, weights=g.tokens)) if g.tokens.sum() else 0, 3)}
                            for c, g in cov.groupby("claude_class")},
    }
    names = comp[~comp.claude_class.isin(["agent", "place"])]
    rep["coverage"]["without_names_types"] = round(float((names.status != "missing").mean()), 3)

    dis = cov[cov.claude_class != cov.wordnet_class]
    rep["disagreements"] = {"n": int(len(dis)), "tokens": tot(dis),
                            "by_pair_tokens": {f"{k[0]} -> {k[1]}": int(v) for k, v in
                                               dis.groupby(["claude_class", "wordnet_class"]).tokens.sum().sort_values(ascending=False).items()}}
    s = sample_disagreements(dis, a.sample)
    aud = pd.DataFrame({"gloss": s.gloss, "lemma_example": s.lemma_example, "claude_class": s.claude_class,
                        "wordnet_class": s.wordnet_class, "wordnet_sense": s.english + " (" + s.supersense + ")",
                        "tokens": s.tokens, "correct": ""})
    aud.to_csv(out / "wordnet_audit_sample.csv", index=False)
    rep["audit_sample"] = {"n": int(len(aud)), "seed": 0, "file": str(out / "wordnet_audit_sample.csv")}
    json.dump(rep, open(out / "wordnet_check.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: rep[k] for k in ("glosses", "coverage", "type_weighted", "token_weighted", "any_sense_agrees", "by_claude_class")},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
