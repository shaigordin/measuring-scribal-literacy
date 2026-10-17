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

| Slide | Numbers | File (in `results/tlhdig03/`) | Script |
|---|---|---|---|
| Orphans: fragments without a tradition | CTH 470 and EBo counts, median words, filing | `corpus_stats.json` → `orphans` | `stats_corpus.py` |
| Validation | leave-one-out accuracy, baselines | `report.json` → `E1_*`, `E3_cth701_subgroups` | `run_experiments.py` |
| How small can an orphan be? | accuracy by fragment size | `E2_coverage_curve.csv` | `run_experiments.py` |
| Vocabulary, orthography or date? | logograms removed; MS vs NS | `report.json` → `E4_*`, `E3_cth701_script_date` | `run_experiments.py` |
| What identifies a tradition | accuracy per layer | `E7_report.json` → `E7a_layers` | `run_profiles.py` |
| Cultural profiles | distinctive features | `E7_distinctive_features.csv` | `run_profiles.py` |
| Scribal profiles | index z-scores; plene clusters; date check | `E7_report.json`, `corpus_stats.json` → `plene_clusters` | `run_profiles.py`, `stats_corpus.py` |
| Word classes | each class alone / removed | `E8_report.json` | `run_wordclass.py` |
| Where do CTH 470 and EBo go? | orphans per tradition, margin and its interval | `report.json` → `E2_abstention`, `E5_orphans` | `run_experiments.py` |
| QTM | archetype coverage (notes) | `report.json` → `E6_archetype_coverage` | `run_experiments.py` |

`results/tlhdig03_literature/` holds the same experiments with the literature-defined groups
(`--groups literature`, see `qtm/groups.py`); the slides "Validation with literature-defined
traditions" and its notes read `report.json` → `E1_historical`, `E5b_residue` there.
`results/tlhdig03_hfr/` (`--groups hfr`) splits the Luwian group into the HFR festival modules
and adds the Palaic festivals (slide "Test against the HFR festival modules").

CTH 500 ("Fragmente von Fest- und Beschwörungsritualen aus Kizzuwatna") is not used as a
reference: the Konkordanz numbers its fragments 500.1–500.600 as a running list, not by
composition, and HFR counts CTH 500 among its festival texts. Its manuscripts are placed like
orphans (`E5b_residue` → "CTH 500 Kizzuwatna fragments").

## Design

- **Reference traditions** (`qtm/groups.py`): the historical groups of StBoT 73 Table 3, plus
  Kizzuwatna rituals (CTH 471–500) and Old Anatolian rituals (CTH 390–469) as controls. The
  abstract's CTH 670 / 701 / 832 setup is run as well, for comparison.
- **Orphans:** every CTH 470 text and every EBo text, wherever TLHdig files it. Orphans are
  never part of the reference.
- **Features:** word tf-idf (normalised `trans` forms) and sign 1–3-grams within words.
- **Assignment:** cosine similarity to tradition centroids. Leave-one-out is computed in
  closed form, with 200 label permutations. The tf-idf weights are fitted on the whole
  reference set (transductive idf).

`results/zenodo_pilot/` is the first run on the glossed-only Zenodo CSV (10.5281/zenodo.14266302),
and it is superseded by `results/tlhdig03/`.
