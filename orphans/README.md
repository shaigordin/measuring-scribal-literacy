# Orphans and Archetypes: experiments

Code for the Mainz Hittite & AI workshop talk (November 2026) on assigning unidentified
Hittite ritual fragments (CTH 470, EBo) to textual traditions. The slides are
`../orphans_archetypes.qmd`, and `TALK_OUTLINE.md` has the talk structure.

## Reproducing everything

```
python3 -m pip install -r requirements.txt     # pinned versions, Python 3.13
bash reproduce.sh                              # data download, parse, E1-E8, figures, slides
```

`reproduce.sh` downloads TLHdig Beta 0.3 from Zenodo ([10.5281/zenodo.20328284](https://doi.org/10.5281/zenodo.20328284)),
checks its MD5, parses it to `data/tokens.csv` (one row per word: `txtid, cth_number, source, lnr,
lang, word, translit, wclass`), runs every experiment for both reference setups, redraws the
figures and re-renders the deck. All randomness (permutations, fragment sampling, bootstraps)
is seeded, and files are read in sorted order, so a rerun gives the same numbers.

The **CTH 701 subgroup and date labels** (Salvini–Wegner a–f; mh./jh.) come from the Mainz
Konkordanz ([hethport.net/hetkonk, c=701](https://hethport.net/hetkonk/hetkonk_abfrage.php?c=701)),
parsed by `qtm/konkordanz.py`. `labels/cth701_labels.csv` is the snapshot used for the results
(access date in `labels/cth701_labels.source.txt`); `REFRESH_KONKORDANZ=1 bash reproduce.sh`
rebuilds it from the live page. Checked against the StBoT 73 working sheet (121 shared
fragments): the groups agree for 120 and the dates for all 120 the sheet dates. The one group
difference is KBo 64.168, listed as "701.₂.I" in the Konkordanz: the group letter is missing, an
error in the Konkordanz. It is corrected to b₂ (as in the sheet) by the `CORRECTIONS` table in
`qtm/konkordanz.py`, and the label file says so in its `note` column. Uncertain Konkordanz groups ("701.?", "701.Tf7.D") are unclassified too. The Konkordanz
labels cover 155 of TLHdig's 167 CTH 701 texts, against 126 for the sheet.

## Where each number on the slides comes from

The talk's main reference is the literature-defined set (`--groups literature`): its results are in
`results/tlhdig03_literature/`. `results/tlhdig03/` holds the StBoT 73 groups with CTH-range
controls (`--groups historical`), shown once as the published baseline.

| Slide | Numbers | File | Script |
|---|---|---|---|
| Orphans: fragments without a tradition | CTH 470 and EBo counts, median words, filing | `tlhdig03/corpus_stats.json` → `orphans` | `stats_corpus.py` |
| Validation: the StBoT 73 groups | leave-one-out accuracy, baselines | `tlhdig03/report.json` → `E1_*` | `run_experiments.py` |
| Validation with literature-defined traditions | accuracy, recall per tradition; CTH 500 and residue placement (notes) | `tlhdig03_literature/report.json` → `E1_historical`, `E5b_residue` | `run_experiments.py` |
| How small can an orphan be? | accuracy by fragment size | `tlhdig03_literature/E2_coverage_curve.csv` | `run_experiments.py` |
| Vocabulary, orthography or date? | logograms removed; MS vs NS | `tlhdig03_literature/report.json` → `E4_*`, `E3_cth701_script_date` | `run_experiments.py` |
| What identifies a tradition | accuracy per layer | `tlhdig03_literature/E7_report.json` → `E7a_layers` | `run_profiles.py` |
| Cultural profiles | distinctive features | `tlhdig03_literature/E7_distinctive_features.csv` | `run_profiles.py` |
| Scribal profiles | index z-scores; plene clusters; date check | `tlhdig03_literature/E7_report.json`, `tlhdig03_literature/corpus_stats.json` → `plene_clusters` | `run_profiles.py`, `stats_corpus.py` |
| Word classes | each class alone / removed | `tlhdig03_literature/E8_report.json` | `run_wordclass.py` |
| Recovering Salvini and Wegner's groups | CTH 701 subgroups | `tlhdig03_literature/report.json` → `E3_cth701_subgroups` | `run_experiments.py` |
| Where do CTH 470 and EBo go? | orphans per tradition, margin and its interval | `tlhdig03_literature/report.json` → `E2_abstention`, `E5_orphans` | `run_experiments.py` |
| Does a fragment fit any known tradition? | outside genres placed / recognised; orphans nearer an outside genre | `tlhdig03_literature/E9_report.json`, `E9_orphan_fit.csv` | `run_openset.py` |
| QTM | archetype coverage (notes) | `tlhdig03_literature/report.json` → `E6_archetype_coverage` | `run_experiments.py` |

The literature-defined groups split StBoT 73's Luwian group as the HFR edition modules split it
(Hethitische Festrituale, hethport.net/HFR) and add HFR's Palaic festivals; see `qtm/groups.py`.

CTH 500 ("Fragmente von Fest- und Beschwörungsritualen aus Kizzuwatna") is not used as a
reference: the Konkordanz numbers its fragments 500.1–500.600 as a running list, not by
composition, and HFR counts CTH 500 among its festival texts. Its manuscripts are placed like
orphans (`E5b_residue` → "CTH 500 Kizzuwatna fragments").

## Why each reference tradition is defined as it is

Every group is defined by a study that argued for it; Laroche's CTH numbers (as on the Portal
CTH, hethport.net/CTH, titles checked 2026-10-17) are only its address. `qtm/groups.py` repeats
these sources next to each list. Texts = TLHdig 0.3 manuscripts of 17+ words.

| Tradition | CTH | Defining study | Evidence | Texts |
|---|---|---|---|---|
| Kizzuwatna–Lower Land (Hurrian) | 628, 699, 700, 711–713, 719, 722 | StBoT 73 Table 3; Wegner–Salvini 1991 (ChS I/4) | cult geography of the Hurrian festivals | 311 |
| Syro-Mesopotamia (Hurrian) | 698, 701, 714, 715, 721 | StBoT 73 Table 3; Salvini–Wegner 1986 (ChS I/2) | cult geography; the AZU priest | 164 |
| Mixed (Hurrian, Syrian, Luwian) | 704–706, 720 | StBoT 73 Table 3 | mixed pantheon | 198 |
| Luwian festivals (Ištanuwa, Lallupiya) | 665, 771–773 | HFR edition module "Luwian festivals" | CTH list published by HFR | 50 |
| Ḫuwaššanna festivals | 690–694 | HFR module "Ḫuwaššanna"; Laroche titles "Feste für Ḫuwaššanna" | the goddess named in every title | 180 |
| Palaic festivals | 750–754 | HFR module "Palaic festivals" | CTH list published by HFR; Palaic language | 34 |
| Kizzuwatna rituals | 471–499, 404 | Miller 2004 (StBoT 46); Strauß 2006; Görke 2010 | practitioners "from Kizzuwatna" in colophons and CTH titles (e.g. 404 Maštigga, 471 Ammiḫatna) | 164 |
| Western (Arzawa) rituals | 394, 402, 406, 410, 425, 433 | Bawanypeck 2005 (THeth 25); Archi 2015 (BiOr 72); Mouton 2010 | colophons "from Arzawa / Ḫapalla" (394, 402, 406, 410); augur rituals, one naming an augur from Arzawa | 11 |
| Luwian rituals (Puriyanni, Kuwattalla) | 758–763 | Yakubovich and Mouton 2023 (StBoT 72); Mouton and Yakubovich 2021 | practitioners named in colophons; placed in the Lower Land, not Kizzuwatna | 10 |
| Hattian cult layer | 591, 627, 725–746 (not 730), 820, 821 | Klinger 1996 (StBoT 37) | Hattian deities and language; list taken from the Konkordanz citations of StBoT 37 | 478 |

Left out on purpose, and placed like orphans instead: CTH 500 (a running list of Kizzuwatna
fragments, not a composition); the Ambazzi rituals CTH 391, 429, 463 (Christiansen 2006 shows Luwian
influence but no stated link to Arzawa); and the rest of CTH 390–469, which no study claims as one
tradition.

## Design

- **Reference traditions** (`qtm/groups.py`): `LITERATURE`, each tradition defined by the study
  that argued for it (Miller 2004, Christiansen 2006, Bawanypeck 2005, Klinger 1996, StBoT 73 and
  the HFR modules). `HISTORICAL` (StBoT 73 Table 3, plus Kizzuwatna rituals CTH 471–500 and Old
  Anatolian rituals CTH 390–469 as controls) and the abstract's CTH 670 / 701 / 832 setup are run
  for comparison.
- **Open set (E9, `run_openset.py`):** texts of genres outside the reference (myths, prayers,
  oracles, historical texts and treaties, instructions, cult inventories, festivals of other
  traditions, the Luwian rituals of Puriyanni and Kuwattalla) are cut into windows and scored
  in 5 folds. It measures how often the margin rule still places them in a tradition, and how
  well a similarity floor or a genre gate (outside genres as classes of their own) catches them.
- **Orphans:** every CTH 470 text and every EBo text, wherever TLHdig files it. Orphans are
  never part of the reference.
- **Features:** word tf-idf (normalised `trans` forms) and sign 1–3-grams within words.
- **Assignment:** cosine similarity to tradition centroids. Leave-one-out is computed in
  closed form, with 200 label permutations. The tf-idf weights are fitted on the whole
  reference set (transductive idf).

`results/zenodo_pilot/` is the first run on the glossed-only Zenodo CSV (10.5281/zenodo.14266302),
and it is superseded by `results/tlhdig03/`.
