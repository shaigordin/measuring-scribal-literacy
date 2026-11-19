"""Documentation and packaging of the Zenodo release written by make_release.py.

Writes into the release folder: README.md (from release_template/README.md, every number read from
summary.json and the CSVs, none typed by hand), datapackage.json (Frictionless Data: every column
with its type and meaning), CITATION.cff and LICENSE.txt; then zips the folder for upload.

Usage: python release_docs.py release --version 1.0.0 [--zip]
"""
import argparse
import json
import os
import re
import zipfile
from datetime import date
from string import Template

import numpy as np
import pandas as pd

from make_release import AUTHOR_FIX, LITERATURE, cite

TLH = os.environ.get("TLH", "04")                    # TLHdig Beta release the data were built from
TLH_VERSION = {"03": "0.3", "04": "0.4"}[TLH]
TITLE = ("Orphans and Archetypes: closest traditions, compositions and duplicate or join candidates "
         f"for the unplaced fragments of the Hittite corpus (TLHdig {TLH_VERSION})")
AUTHOR = {"family-names": "Gordin", "given-names": "Shai", "affiliation": "Ariel University"}
TLHDIG_DOI = {"03": "10.5281/zenodo.20328284", "04": "10.5281/zenodo.24373727"}[TLH]
CODE_URL = "https://github.com/shaigordin/measuring-scribal-literacy"
CATS = ["function_words", "verbs", "realia", "agents_and_deities", "places", "animals_body_nature",
        "abstract_nouns", "adjectives", "foreign_words", "other_words"]

FRAGMENTS = [
    ("txtid", "string", "TLHdig text id (publication number; a trailing + marks a text TLHdig already stores as a join)."),
    ("filed_under_cth", "string", "CTH number under which TLHdig files the text (Laroche's catalogue, as on the Portal)."),
    ("laroche_bin", "string", "The residual bin the text comes from: CTH 470, 500, 670, 832, the CTH 390-469 rituals no study groups, or an EBo piece filed under another CTH."),
    ("is_ebo", "boolean", "True for the EBo pieces (fragments rediscovered at Boğazköy in 2025, transliterations only)."),
    ("n_words_analysed", "integer", "Analysed words that count in this dataset (without restorations: on the tablet, or supported by the same text; with restorations: as printed): what the model reads."),
    ("n_words_legible", "integer", "Legible words on the tablet, analysed or not (used by the spellings-only check)."),
    ("n_words_same_text", "integer", "Without restorations only. Words that count only because the same word form is at least half preserved elsewhere in the same text."),
    ("present_share", "number", "Without restorations only. Share of the text's signs that are preserved or damaged (not restored, omitted or lost)."),
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
] + [(f"words_{c}", "number", f"Share of the analysed words in the word category '{c.replace('_', ' ')}'.") for c in CATS]

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
# Full entries for the works this README cites. The most-cited study of every tradition (computed by
# make_release.py from the Konkordanz) must have one here; the first and latest studies are listed as the
# Konkordanz cites them.
HERE = os.path.dirname(os.path.abspath(__file__))
FULL = {
    "Klinger 1996 (StBoT 37)": "Klinger, Jörg. 1996. *Untersuchungen zur Rekonstruktion der hattischen Kultschicht*. StBoT 37. Wiesbaden: Harrassowitz.",
    "Miller 2004 (StBoT 46)": "Miller, Jared L. 2004. *Studies in the Origins, Development and Interpretation of the Kizzuwatna Rituals*. StBoT 46. Wiesbaden: Harrassowitz.",
    "Mouton 2010 (JCS 62)": "Mouton, Alice. 2010. Sorcellerie hittite. *Journal of Cuneiform Studies* 62: 105–125.",
    "Salvini and Wegner 1986 (ChS I/2)": "Salvini, Mirjo, and Ilse Wegner. 1986. *Die Rituale des AZU-Priesters*. ChS I/2. Roma: Multigrafica.",
    "Starke 1985 (StBoT 30)": "Starke, Frank. 1985. *Die keilschrift-luwischen Texte in Umschrift*. StBoT 30. Wiesbaden: Harrassowitz.",
    "Steitler 2017 (StBoT 62)": "Steitler, Charles W. 2017. *The Solar Deities of Bronze Age Anatolia: Studies in Texts of the Early Hittite Kingdom*. StBoT 62. Wiesbaden: Harrassowitz.",
    "Wegner 2002 (ChS I/3-2)": "Wegner, Ilse. 2002. *Hurritische Opferlisten aus hethitischen Festbeschreibungen. Teil II: Texte für Teššub, Ḫebat und weitere Gottheiten*. ChS I/3-2. Roma.",
    "Wegner and Salvini 1991 (ChS I/4)": "Wegner, Ilse, and Mirjo Salvini. 1991. *Die hethitisch-hurritischen Ritualtafeln des (ḫ)išuwa-Festes*. ChS I/4. Roma: Multigrafica.",
    "Yakubovich and Mouton 2023 (StBoT 72,1)": "Yakubovich, Ilya, and Alice Mouton. 2023. *Luwili: Hittite-Luwian Ritual Texts Attributed to Puriyanni, Kuwattalla and Šilalluḫi (CTH 758–763)*. StBoT 72. Wiesbaden: Harrassowitz.",
    "Jakob-Rost 1972 (THeth 2)": "Jakob-Rost, Liane. 1972. *Das Ritual der Malli aus Arzawa gegen Behexung (KUB XXIV 9+)*. THeth 2. Heidelberg: Winter.",
    "Yoshida 1996 (THeth 22)": "Yoshida, Daisuke. 1996. *Untersuchungen zu den Sonnengottheiten bei den Hethitern: Schwurgötterliste, helfende Gottheit, Feste*. THeth 22. Heidelberg: Winter.",
}
SOURCES = [
    "eDiAna. 2026. *eDiAna: Digital Philological-Etymological Dictionary of the Minor Ancient Anatolian Corpus Languages*. Ludwig-Maximilians-Universität München, https://www.ediana.gwi.uni-muenchen.de (accessed November 2026). CC BY-SA 4.0.",
    "Gordin, Shai, Emma Yavasan and Avital Romach. 2025. Matters of Genre, Style and Orthography: Hittite Scribal Habits through the Stylometric Lens. In Susanne Görke, Adam Kryszeń, Gerfrid G. W. Müller and Charles W. Steitler (eds), *The Tablets and Their Scribes: The Palaeography of Hittite Cuneiform and Writing Practices in Hittite Anatolia*. StBoT 73. Wiesbaden: Harrassowitz, 107–123.",
    "Rieken, Elisabeth, and Daniel Schwemer. 2026. *Corpus der hethitischen Festrituale (HFR)*. Akademie der Wissenschaften und der Literatur Mainz, hethiter.net/: HFR, https://hethport.net/HFR/.",
    "Haas, Volkert. 1994. *Geschichte der hethitischen Religion*. Handbuch der Orientalistik I/15. Leiden: Brill.",
    "Košak, Silvin. 2026. *Konkordanz der hethitischen Keilschrifttafeln*. hethiter.net/: hetkonk, https://hethport.net/hetkonk/ (pages accessed November 2026).",
    "Laroche, Emmanuel. 1971. *Catalogue des textes hittites*. Paris: Klincksieck.",
    "Mainzer Fotoarchiv. hethiter.net/: fotarch, https://hethport.net/fotarch/.",
    "Müller, Gerfrid, Doris Prechel, Elisabeth Rieken and Daniel Schwemer. 2026. *Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version " + TLH_VERSION + "*. Zenodo. doi:{doi}.",
    "Waal, Willemijn. 2015. *Hittite Diplomatics: Studies in Ancient Document Format and Record Management*. StBoT 57. Wiesbaden: Harrassowitz.",
]


def _names(s):
    """'Heinrich Otten und Vladimir Souček' -> 'Otten, Heinrich, and Vladimir Souček'."""
    people = [p.strip() for p in re.split(r"\s(?:und|and|–|-)\s", s) if p.strip()]
    first = people[0].rsplit(" ", 1)
    head = f"{first[1]}, {first[0]}" if len(first) == 2 else people[0]
    return head if len(people) == 1 else head + ", and " + ", ".join(people[1:])


def expand(c, lit, abbr):
    """A study in the short form of traditions.csv ('Kümmel 1967 (StBoT 3)') as a full reference, from the
    Konkordanz's list of abbreviations (labels/konkordanz_abbreviations.csv)."""
    if c in FULL:
        return FULL[c]
    r = lit[c]                                          # the Konkordanz citation: initials, venue, year
    venue = re.search(r"\((.*)\)$", c).group(1)
    people = [" ".join(AUTHOR_FIX.get(w, w) for w in n.split()) for n in re.split(r"\s[-/–]\s", r.author)]
    first = people[0].rsplit(" ", 1)
    who = (f"{first[1]}, {first[0]}" if len(first) == 2 else people[0]) + "".join(
        f", and {p}" for p in people[1:])
    who = who.rstrip(".")
    a = abbr.get(venue)
    if a is None or not a.full:
        return f"{who}. {r.year}. {venue} (not in the Konkordanz's list of abbreviations)."
    if a.abbreviation == venue or a.abbreviation == re.sub(r",\s?\d+$", "", venue):   # a volume of a series
        m = re.match(r"(?:(.+?),\s)?(.+?)\s[-–]\s*(\d{4})?$", a.full)
        if m and m.group(1):
            who = _names(m.group(1)).rstrip(".")
        title = m.group(2).strip() if m else a.full
        return f"{who}. {r.year}. *{title}*. {venue}."
    journal = re.split(r"\s[-–]\s|\s\(|;|\.\s", a.full)[0].strip()   # a journal: name and volume only
    return f"{who}. {r.year}. *{journal}* {venue[len(venue.split(' ')[0]):].strip()}."


def references(T):
    missing = set(T.most_cited_study) - set(FULL)
    assert not missing, f"add full entries for {missing}"
    L = pd.read_csv(os.path.join(HERE, LITERATURE))
    lit = {cite(r): r for r in L.itertuples()}
    lit["Groddek and Kloekhorst 2006 (DBH 19)"] = L[L.venue == "DBH 19"].iloc[0]
    abbr = {r.venue: r for r in pd.read_csv(os.path.join(HERE, "labels", "konkordanz_abbreviations.csv"),
                                            keep_default_na=False).itertuples()}
    works = set(T.most_cited_study) | set(T.first_study) | set(T.latest_study) | {"Groddek and Kloekhorst 2006 (DBH 19)"}
    entries = [expand(c, lit, abbr) for c in works] + [x.format(doi=TLHDIG_DOI) for x in SOURCES]
    return ("Articles are cited as in the Konkordanz (journal and volume).\n\n" + "\n".join(f"- {x}" for x in sorted(set(entries), key=lambda e: e.lower())))


TRADITIONS = [
    ("tradition", "string", "Reference tradition."),
    ("cth", "string", "Its CTH numbers (Laroche), space-separated."),
    ("reference_manuscripts", "integer", "Reference manuscripts (17+ analysed words)."),
    ("most_cited_study", "string", "The study the Konkordanz cites most often for the tradition's manuscripts, "
     "leaving out handbooks and corpus volumes (Haas, HbOr I/15; Waal, StBoT 57; Groddek and Kloekhorst, DBH 19)."),
    ("most_cited_manuscripts", "integer", "Number of the tradition's manuscripts for which the Konkordanz cites it."),
    ("first_study", "string", "The earliest other study the Konkordanz cites for these manuscripts."),
    ("latest_study", "string", "The most recent other study the Konkordanz cites for these manuscripts."),
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


FOLDERS = {"without_restorations": "Without restorations",
           "with_restorations": "With restorations"}


def folder_values(d, F_cols):
    """Numbers of one dataset folder; checks that its files and their documentation agree."""
    if not os.path.exists(f"{d}/nearest_manuscripts.csv"):          # git keeps only the compressed copy
        import gzip, shutil
        with gzip.open(f"{d}/nearest_manuscripts.csv.gz") as src, open(f"{d}/nearest_manuscripts.csv", "wb") as dst:
            shutil.copyfileobj(src, dst)
    S = json.load(open(f"{d}/summary.json"))
    for fn, (_, cols) in FILES.items():                     # documentation and data must agree
        have = list(pd.read_csv(f"{d}/{fn}", nrows=0).columns)
        doc = [c[0] for c in cols]
        assert set(have) <= set(doc) and have == [c for c in doc if c in have], f"{d}/{fn}: undocumented columns {have}"
        F_cols.setdefault(fn, []).extend(c for c in have if c not in F_cols.get(fn, []))
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", help="release folder holding without_restorations/ and with_restorations/")
    ap.add_argument("--version", default="2.1.0")
    ap.add_argument("--known-joins", default=f"results/tlhdig{TLH}_literature_C_filled/known_joins/known_joins.csv")
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    d, cols_seen = a.folder, {}
    S = {k: folder_values(f"{d}/{k}", cols_seen) for k in FOLDERS}
    T = pd.read_csv(f"{d}/without_restorations/traditions.csv", keep_default_na=False)
    Ta = pd.read_csv(f"{d}/with_restorations/traditions.csv", keep_default_na=False).set_index("tradition")
    Fw = pd.read_csv(f"{d}/without_restorations/fragments.csv", keep_default_na=False, dtype=str).set_index("txtid")
    Fa = pd.read_csv(f"{d}/with_restorations/fragments.csv", keep_default_na=False, dtype=str).set_index("txtid")

    versions = pd.DataFrame([{"Folder": f"`{k}/`", "What counts": what, "Texts scored (5+ words)": S[k]["with_results"],
                              "Placed": S[k]["status"].get("placed", 0), "Margin": f"{S[k]['margin']:.3f}",
                              "Held-out accuracy": f"{S[k]['loo_accuracy']:.0%}"}
                             for k, what in (("without_restorations", "Signs visible on the tablet, damaged ones included; a restored word only where the same word survives at least half-preserved elsewhere in the same text"),
                                             ("with_restorations", "The edition as printed: restored signs count as written"))])
    both = Fw.index[(Fw.status == "placed") & Fa.reindex(Fw.index).status.eq("placed")]
    same = int((Fw.loc[both, "placed_tradition"] == Fa.loc[both, "placed_tradition"]).sum())
    trad = T.assign(cth=T.cth.map(ranges), ref_a=T.tradition.map(Ta.reference_manuscripts)).rename(columns={
        "tradition": "Tradition", "cth": "CTH", "reference_manuscripts": "Reference manuscripts (without / with restorations)",
        "most_cited_study": "Most-cited study"})
    trad["Reference manuscripts (without / with restorations)"] = [f"{x} / {y}" for x, y in zip(
        trad["Reference manuscripts (without / with restorations)"], trad.ref_a)]
    trad = trad[["Tradition", "CTH", "Reference manuscripts (without / with restorations)", "Most-cited study"]]
    kj = pd.read_csv(a.known_joins)
    kd, kjn = kj[kj.relation == "duplicate"], kj[kj.relation == "join"]
    sw, sa = S["without_restorations"], S["with_restorations"]
    v = {"title": TITLE, "version": a.version, "date": date.today().isoformat(), "tlhdig_doi": TLHDIG_DOI, "tlhdig": TLH_VERSION,
         "code_url": CODE_URL, "texts": f"{sw['texts_in_scope']:,}", "pool": f"{sw['manuscript_pool']:,}",
         "versions_table": mdtable(versions), "traditions_table": mdtable(trad),
         "placed_both": f"{len(both):,}", "placed_same": f"{same:,}",
         "precision": f"{sw['precision_above_margin']:.0%}",
         "kd_n": len(kd), "kd_top20": int((kd['rank'] <= 20).sum()), "kd_median": f"{kd['rank'].median():g}",
         "kj_n": len(kjn), "kj_top20": int((kjn['rank'] <= 20).sum()),
         "references": references(T)}
    tpl = Template(open(os.path.join(os.path.dirname(__file__) or ".", "release_template", "README.md")).read())
    open(f"{d}/README.md", "w").write(tpl.substitute(v))

    def resources(k):
        out = []
        for fn, (desc, cols) in FILES.items():
            have = list(pd.read_csv(f"{d}/{k}/{fn}", nrows=0).columns)
            out.append({"name": f"{k}-{fn.removesuffix('.csv')}".replace("_", "-"), "path": f"{k}/{fn}",
                        "profile": "tabular-data-resource", "format": "csv", "encoding": "utf-8",
                        "description": f"{FOLDERS[k]}. {desc}",
                        "schema": {"fields": [{"name": n, "type": t, "description": dsc} for n, t, dsc in cols if n in have]}})
        return out
    pkg = {"profile": "tabular-data-package", "name": "orphans-and-archetypes-nearest-manuscripts",
           "title": TITLE, "version": a.version, "licenses": [{"name": "CC-BY-4.0",
           "path": "https://creativecommons.org/licenses/by/4.0/", "title": "Creative Commons Attribution 4.0"}],
           "sources": [{"title": f"Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version {TLH_VERSION}",
                        "path": f"https://doi.org/{TLHDIG_DOI}"}],
           "contributors": [{"title": "Shai Gordin", "role": "author"}],
           "resources": resources("without_restorations") + resources("with_restorations")}
    json.dump(pkg, open(f"{d}/datapackage.json", "w"), indent=1, ensure_ascii=False)

    cff = f"""cff-version: 1.2.0
message: "If you use this dataset, please cite it as below, together with TLHdig {TLH_VERSION}."
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
    title: "Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version {TLH_VERSION}"
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
        f"It is derived from TLHdig Beta Version {TLH_VERSION} (Müller, Prechel, Rieken, Schwemer; doi:{TLHDIG_DOI}),\n"
        "itself licensed CC BY 4.0. Cite both when you use it.\n")
    if a.zip:
        name = f"orphans_archetypes_nearest_manuscripts_v{a.version}"
        with zipfile.ZipFile(f"{d}/../{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for fn in ["README.md", "LICENSE.txt", "CITATION.cff", "datapackage.json"]:
                z.write(f"{d}/{fn}", f"{name}/{fn}")
            for k in FOLDERS:
                for fn in ["summary.json", *FILES]:
                    z.write(f"{d}/{k}/{fn}", f"{name}/{k}/{fn}")
        print("wrote", os.path.abspath(f"{d}/../{name}.zip"))


if __name__ == "__main__":
    main()
