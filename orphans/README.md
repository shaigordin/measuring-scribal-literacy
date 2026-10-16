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

The one input that is not public is the **CTH 701 subgroup sheet** (Salvini–Wegner a–f plus
script date, from the StBoT 73 working data `early_hurrian_nicer_tsne_final_for_280424_only_cth701_with_zeit.csv`).
Point `LABELS701` at it; without it E3, E7c and the CTH 701 part of E8 are skipped.

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
(`--groups literature`, see `qtm/groups.py`).

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
