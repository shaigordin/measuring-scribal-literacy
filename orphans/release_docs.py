"""Documentation and packaging of the Zenodo release written by make_release.py.

Writes into the release folder: README.md (from release_template/README.md, every number read from
summary.json and the CSVs, none typed by hand), datapackage.json (Frictionless Data: every column
with its type and meaning), CITATION.cff and LICENSE.txt; then zips the folder for upload.

Usage: python release_docs.py release --version 1.0.0 [--zip]
"""
import argparse
import json
import os
import zipfile
from datetime import date
from string import Template

import numpy as np
import pandas as pd

TITLE = ("Orphans and Archetypes: closest traditions, compositions and duplicate or join candidates "
         "for the unplaced fragments of the Hittite corpus (TLHdig 0.3)")
AUTHOR = {"family-names": "Gordin", "given-names": "Shai", "affiliation": "Ariel University"}
TLHDIG_DOI = "10.5281/zenodo.20328284"
CODE_URL = "https://github.com/shaigordin/measuring-scribal-literacy"
CATS = ["function_words", "verbs", "realia", "agents_and_deities", "places", "animals_body_nature",
        "abstract_nouns", "adjectives", "foreign_words", "other_words"]

FRAGMENTS = [
    ("txtid", "string", "TLHdig text id (publication number; a trailing + marks a text TLHdig already stores as a join)."),
    ("filed_under_cth", "string", "CTH number under which TLHdig files the text (Laroche's catalogue, as on the Portal)."),
    ("laroche_bin", "string", "The residual bin the text comes from: CTH 470, 500, 670, 832, the CTH 390-469 rituals no study groups, or an EBo piece filed under another CTH."),
    ("is_ebo", "boolean", "True for the EBo pieces (fragments rediscovered at Boğazköy in 2025, transliterations only)."),
    ("n_words_analysed", "integer", "Analysed words that count in version C (on the tablet, or supported by the same text): what the model reads."),
    ("n_words_legible", "integer", "Legible words on the tablet, analysed or not (used by the spellings-only check)."),
    ("n_words_as_edited", "integer", "Analysed words as the edition prints them, restorations included (version A)."),
    ("n_words_same_text", "integer", "Words that count only because the same word form is at least half preserved elsewhere in the same text."),
    ("present_share", "number", "Share of the text's signs that are preserved or damaged (not restored, omitted or lost)."),
    ("tlhdig_url", "string", "The text in TLHdig on the Mainz Portal."),
    ("konkordanz_url", "string", "The text in the Konkordanz der hethitischen Keilschrifttafeln (first piece of a join)."),
    ("status", "string", "placed: the nearest tradition leads the runner-up by at least the margin; below_margin: scored but not placed; too_small: fewer than 5 analysed words, no results."),
    ("tradition_1", "string", "Nearest reference tradition (highest cosine similarity to its centroid)."),
    ("similarity_1", "number", "Cosine similarity to tradition_1 (0-1)."),
    ("tradition_2", "string", "Second-nearest tradition."),
    ("similarity_2", "number", "Cosine similarity to tradition_2."),
    ("tradition_3", "string", "Third-nearest tradition."),
    ("similarity_3", "number", "Cosine similarity to tradition_3."),
    ("margin", "number", "similarity_1 minus similarity_2: how clearly the nearest tradition wins."),
    ("placed_tradition", "string", "tradition_1 if margin >= the calibrated margin (see README), else empty."),
    ("fit_floor", "number", "Open-set fit floor for a fragment of this size: 5th percentile of the similarity of reference windows of the same size to their own tradition."),
    ("below_fit_floor", "boolean", "similarity_1 is below fit_floor: the fragment fits no tradition as well as 95% of genuine members do."),
    ("nearest_with_outside_genres", "string", "Nearest class when eight outside genres (myths, prayers, oracles, historical texts, instructions, cult inventories, other festivals, Taurisa rituals) are added as classes."),
    ("nearest_is_outside_genre", "boolean", "nearest_with_outside_genres is an outside genre, by at least the margin: the fragment may not be a ritual or festival of the reference traditions."),
    ("spellings_only_placed", "string", "Tradition placed by the spellings-only check (sign n-grams of every legible word, reference including manuscripts without word analyses), else empty."),
    ("spellings_only_agrees", "boolean", "Both models place the fragment and agree. Empty if either does not place it."),
    ("common_features_share", "number", "Share of the margin carried by features attested in at least 25% of reference texts (e.g. nu, the sign a). Negative: common features pull against the decision."),
    ("rests_on_common_features", "boolean", "More than half of the margin comes from common features: the placement rests on common material and is weaker."),
    ("compositions_top5", "string", "The five nearest compositions (CTH numbers outside the residual bins), '; '-separated, nearest first."),
    ("compositions_top5_similarity", "string", "Cosine similarity to each of compositions_top5."),
    ("manuscripts_top5", "string", "The five nearest manuscripts in the whole release, '; '-separated, nearest first."),
    ("manuscripts_top5_similarity", "string", "Cosine similarity to each of manuscripts_top5."),
    ("manuscripts_top20", "string", "The 20 nearest manuscripts; details for each in nearest_manuscripts.csv."),
    ("match_candidates", "string", "Those of the 20 nearest manuscripts that pass all three match checks: duplicates, parallels or joins to check (see README)."),
] + [(f"words_{c}", "number", f"Share of the analysed words in the word category '{c.replace('_', ' ')}'.") for c in CATS] + [
    ("status_A", "string", "status in version A (restored signs read as written), for comparison."),
    ("placed_tradition_A", "string", "placed_tradition in version A, for comparison."),
]

JOINS = [
    ("txtid", "string", "The fragment (as in fragments.csv)."),
    ("rank", "integer", "1 = nearest manuscript."),
    ("candidate_txtid", "string", "A manuscript of the whole release with 5+ analysed words."),
    ("candidate_cth", "string", "CTH number under which TLHdig files the candidate."),
    ("candidate_group", "string", "The candidate's reference tradition, residual pool ('CTH 390–469 residue', 'CTH 500 Kizzuwatna fragments'), 'orphan' (CTH 470 or EBo), the Laroche bin, or empty for other CTH numbers."),
    ("candidate_n_words", "integer", "Analysed words of the candidate."),
    ("similarity", "number", "Cosine similarity of fragment and candidate."),
    ("match_barcode", "string", "One character per distinct content word of the fragment, in line order: S = the candidate has the word spelled the same way, W = spelled differently, . = absent."),
    ("fragment_content_words", "integer", "Distinct content words of the fragment (numbers and broken words left out)."),
    ("shared_words", "integer", "Content words of the fragment found in the candidate (S + W)."),
    ("same_spelling", "integer", "Shared words spelled identically (S)."),
    ("different_spelling", "integer", "Shared words spelled differently (W)."),
    ("shared_phrases", "string", "Two-word phrases of the fragment (adjacent words) that also occur in the candidate, '; '-separated."),
    ("check_half_the_words", "boolean", "Match check 1: the candidate has at least half of the fragment's content words."),
    ("check_same_spellings", "boolean", "Match check 2: every shared word is spelled exactly as in the fragment (one scribal habit)."),
    ("check_shared_phrase", "boolean", "Match check 3: at least one shared two-word phrase."),
    ("passes_match_checks", "boolean", "All three checks pass: a duplicate, parallel or join candidate to check on the tablets (most known cases that pass are duplicates)."),
    ("candidate_tlhdig_url", "string", "The candidate in TLHdig."),
]
TRADITIONS = [
    ("tradition", "string", "Reference tradition."),
    ("cth", "string", "Its CTH numbers (Laroche), space-separated."),
    ("reference_manuscripts", "integer", "Reference manuscripts (17+ analysed words)."),
    ("defining_study", "string", "The study that argued for the tradition."),
]
COMPOSITIONS = [
    ("cth", "string", "CTH number."),
    ("manuscripts", "integer", "Manuscripts with 5+ analysed words that make up the composition's centroid."),
    ("tradition", "string", "Reference tradition or residual pool of the CTH number, if any."),
]
FILES = {"fragments.csv": ("One row per text in Laroche's residual bins and per EBo piece.", FRAGMENTS),
         "nearest_manuscripts.csv": ("One row per fragment and each of its 20 nearest manuscripts, with the word barcode and the match checks.", JOINS),
         "traditions.csv": ("The ten reference traditions.", TRADITIONS),
         "compositions.csv": ("The compositions (CTH numbers) used for compositions_top5.", COMPOSITIONS)}


def coltable(cols):
    return "\n".join(["| Column | Meaning |", "|---|---|"] + [f"| `{n}` | {d} |" for n, _, d in cols])


def fmt(v):
    return f"{v:,}" if isinstance(v, (int, np.integer)) and not isinstance(v, (bool, np.bool_)) else str(v)


def ranges(cths):
    """'471 472 ... 499 404' -> '404, 471–499'."""
    ns, out = sorted(int(c) for c in str(cths).split()), []
    for n in ns:
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return ", ".join(f"{a}" if a == b else f"{a}–{b}" for a, b in out)


def mdtable(df):
    cols = list(df.columns)
    return "\n".join(["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)] +
                     ["| " + " | ".join(fmt(v) for v in r) + " |" for r in df.itertuples(index=False)])


def example(F, J, txtid):
    f = F.loc[txtid]
    j = J[J.txtid == txtid]
    j = j[(j["rank"].astype(int) <= 5) | (j.passes_match_checks == "True")][["rank", "candidate_txtid", "candidate_cth", "similarity", "match_barcode", "passes_match_checks"]]
    lines = [f"**{txtid}** (filed under CTH {f.filed_under_cth}, {f.n_words_analysed} analysed words): "
             f"nearest tradition {f.tradition_1} ({f.similarity_1}), then {f.tradition_2} ({f.similarity_2}); "
             f"margin {f.margin}, status `{f.status}`. Nearest compositions: {f.compositions_top5}. "
             f"Duplicate or join candidates: {f.match_candidates or 'none'}. Its five nearest manuscripts"
             f"{' and the candidates that pass the match checks' if f.match_candidates else ''}:", "", mdtable(j)]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--version", default="1.0.0")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    d = a.folder
    if not os.path.exists(f"{d}/nearest_manuscripts.csv"):          # git keeps only the compressed copy
        import gzip, shutil
        with gzip.open(f"{d}/nearest_manuscripts.csv.gz") as src, open(f"{d}/nearest_manuscripts.csv", "wb") as dst:
            shutil.copyfileobj(src, dst)
    S = json.load(open(f"{d}/summary.json"))
    F = pd.read_csv(f"{d}/fragments.csv", keep_default_na=False, dtype=str).set_index("txtid")
    J = pd.read_csv(f"{d}/nearest_manuscripts.csv", keep_default_na=False, dtype=str)
    T = pd.read_csv(f"{d}/traditions.csv", keep_default_na=False)
    for fn, (_, cols) in FILES.items():                     # documentation and data must agree
        have = list(pd.read_csv(f"{d}/{fn}", nrows=0).columns)
        assert have == [c[0] for c in cols], f"{fn}: columns differ from the documentation: {have}"

    bins = pd.DataFrame([{"Bin": b, **v} for b, v in S["by_bin"].items()]).rename(columns={
        "texts": "Texts", "too_small": "Under 5 words", "below_margin": "Scored, not placed",
        "placed": "Placed", "with_match_candidates": "With duplicate or join candidates"})
    placed = pd.DataFrame([{"Tradition": t, "Fragments placed": n} for t, n in S["placed_by_tradition"].items()])
    size = pd.DataFrame([{"Analysed words": k, "Fragments scored": v["size"], "With duplicate or join candidates": v["sum"],
                          "Share": f"{v['sum'] / v['size']:.0%}"} for k, v in S["fragments_with_match_candidates_by_size"].items()])
    T2 = T.assign(cth=T.cth.map(ranges)).rename(columns={"tradition": "Tradition", "cth": "CTH", "reference_manuscripts": "Reference manuscripts",
                           "defining_study": "Defining study"})
    # check of the composition ranking on texts whose composition is known: the scored CTH 390-469
    # texts whose CTH number has at least one other manuscript (the text is left out of its own CTH)
    comp = pd.read_csv(f"{d}/compositions.csv", dtype=str).set_index("cth").manuscripts.astype(int)
    r = F[(F.laroche_bin == "CTH 390-469 rituals no study groups") & (F.status != "too_small")]
    r = r[r.filed_under_cth.map(comp).fillna(0) >= 2]
    ranks = [l.split("; ") for l in r.compositions_top5]
    own = ["CTH " + c for c in r.filed_under_cth]
    # check of the manuscript ranking and the join checks against the Konkordanz (run_known_joins.py)
    kj = pd.read_csv(os.path.join(os.path.dirname(__file__) or ".", "results", "tlhdig03_literature",
                                  "known_joins", "known_joins.csv"))
    kd, kjn = kj[kj.relation == "duplicate"], kj[kj.relation == "join"]
    known = {"kd_n": len(kd), "kd_median": f"{kd['rank'].median():g}", "kd_top1": int((kd['rank'] == 1).sum()),
             "kd_top5": int((kd['rank'] <= 5).sum()), "kd_top20": int((kd['rank'] <= 20).sum()),
             "kd_pass": int(kd.passes_join_checks.sum()), "kj_n": len(kjn), "kj_top20": int((kjn['rank'] <= 20).sum()),
             "kj_median": f"{kjn['rank'].median():g}", "kj_pass": int(kjn.passes_join_checks.sum())}
    audit = json.load(open(os.path.join(os.path.dirname(__file__) or ".", "results", "wordclass_audit_scores.json")))
    va = S.get("version_A", {})
    v = {"a_placed": f"{va.get('placed_A', 0):,}", "a_both": f"{va.get('placed_both', 0):,}",
         "a_same": f"{va.get('same_tradition', 0):,}", **known, "known_n": f"{len(r):,}", "known_top1": f"{sum(o == l[0] for o, l in zip(own, ranks)):,}",
         "known_top1_share": f"{sum(o == l[0] for o, l in zip(own, ranks)) / len(r):.0%}",
         "known_top5": f"{sum(o in l for o, l in zip(own, ranks)):,}",
         "known_top5_share": f"{sum(o in l for o, l in zip(own, ranks)) / len(r):.0%}",
         "audit_n": audit["sample_size"], "audit_acc": f"{audit['before_fixes']['corpus_weighted_accuracy']:.0%}",
         "title": TITLE, "version": a.version, "date": date.today().isoformat(), "tlhdig_doi": TLHDIG_DOI,
         "code_url": CODE_URL, "texts": f"{S['texts_in_scope']:,}", "with_results": f"{S['with_results']:,}",
         "too_small": f"{S['status']['too_small']:,}", "placed": f"{S['status']['placed']:,}",
         "below_margin": f"{S['status']['below_margin']:,}", "margin": f"{S['margin']:.3f}",
         "precision": f"{S['precision_above_margin']:.0%}", "loo": f"{S['loo_accuracy']:.0%}",
         "majority": f"{S['loo_majority']:.0%}", "reference": f"{S['reference_manuscripts']:,}",
         "pool": f"{S['manuscript_pool']:,}", "compositions": f"{S['compositions']:,}",
         "with_matches": f"{S['fragments_with_match_candidates']:,}", "match_pairs": f"{S['match_candidate_pairs']:,}",
         "bins_table": mdtable(bins), "placed_table": mdtable(placed), "size_table": mdtable(size),
         "traditions_table": mdtable(T2), "fragments_columns": coltable(FRAGMENTS), "nearest_columns": coltable(JOINS),
         "traditions_columns": coltable(TRADITIONS), "compositions_columns": coltable(COMPOSITIONS),
         "example_ebo": example(F, J, "EBo 133"), "example_kbo": example(F, J, "KBo 41.22")}
    tpl = Template(open(os.path.join(os.path.dirname(__file__) or ".", "release_template", "README.md")).read())
    open(f"{d}/README.md", "w").write(tpl.substitute(v))

    pkg = {"profile": "tabular-data-package", "name": "orphans-and-archetypes-nearest-manuscripts",
           "title": TITLE, "version": a.version, "licenses": [{"name": "CC-BY-4.0",
           "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0"}],
           "sources": [{"title": "Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version 0.3",
                        "path": f"https://doi.org/{TLHDIG_DOI}"}],
           "contributors": [{"title": "Shai Gordin", "role": "author"}],
           "resources": [{"name": fn.removesuffix(".csv"), "path": fn, "profile": "tabular-data-resource",
                          "format": "csv", "encoding": "utf-8", "description": desc,
                          "schema": {"fields": [{"name": n, "type": t, "description": dsc} for n, t, dsc in cols]}}
                         for fn, (desc, cols) in FILES.items()]}
    json.dump(pkg, open(f"{d}/datapackage.json", "w"), indent=1, ensure_ascii=False)

    cff = f"""cff-version: 1.2.0
message: "If you use this dataset, please cite it as below, together with TLHdig 0.3."
type: dataset
title: "{TITLE}"
version: "{a.version}"
date-released: "{v['date']}"
license: CC-BY-4.0
authors:
  - family-names: "{AUTHOR['family-names']}"
    given-names: "{AUTHOR['given-names']}"
    affiliation: "{AUTHOR['affiliation']}"
repository-code: "{CODE_URL}"
keywords: [Hittite, cuneiform, Boğazköy, fragments, joins, CTH, TLHdig, scribal traditions, stylometry]
references:
  - type: dataset
    title: "Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version 0.3"
    authors:
      - family-names: Müller
        given-names: Gerfrid
      - family-names: Prechel
        given-names: Doris
      - family-names: Rieken
        given-names: Elisabeth
      - family-names: Schwemer
        given-names: Daniel
    doi: "{TLHDIG_DOI}"
"""
    open(f"{d}/CITATION.cff", "w").write(cff)
    open(f"{d}/LICENSE.txt", "w").write(
        "This dataset is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).\n"
        "https://creativecommons.org/licenses/by/4.0/legalcode\n\n"
        "It is derived from TLHdig Beta Version 0.3 (Müller, Prechel, Rieken, Schwemer; doi:10.5281/zenodo.20328284),\n"
        "itself licensed CC BY 4.0. Cite both when you use it.\n")
    # review sample (Google Sheet): the two worked examples + 8 scored texts per bin, seeded
    Fr = F.reset_index()
    pick = Fr[Fr.txtid.isin(["EBo 133", "KBo 41.22"])]
    rest = Fr[(Fr.status != "too_small") & ~Fr.txtid.isin(pick.txtid)]
    pick = pd.concat([pick] + [g.sample(min(8, len(g)), random_state=0) for _, g in rest.groupby("laroche_bin", sort=False)])
    keep = ["txtid", "filed_under_cth", "laroche_bin", "n_words_analysed", "status", "tradition_1", "similarity_1",
            "tradition_2", "similarity_2", "margin", "placed_tradition", "below_fit_floor", "nearest_is_outside_genre",
            "spellings_only_agrees", "rests_on_common_features", "compositions_top5", "manuscripts_top5",
            "match_candidates", "tlhdig_url"]
    pick[keep].to_csv(f"{d}/review_sample.csv", index=False)
    if a.zip:
        name = f"orphans_archetypes_nearest_manuscripts_v{a.version}"
        with zipfile.ZipFile(f"{d}/../{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for fn in ["README.md", "LICENSE.txt", "CITATION.cff", "datapackage.json", "summary.json", *FILES]:
                z.write(f"{d}/{fn}", f"{name}/{fn}")
        print("wrote", os.path.abspath(f"{d}/../{name}.zip"))


if __name__ == "__main__":
    main()
