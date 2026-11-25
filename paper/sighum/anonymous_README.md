# Orphans and Archetypes: code and results (anonymous review copy)

Supplementary material for the submission "Orphans and Archetypes: Quantitative Tradition
Mapping for Fragmentary Hittite Texts". It holds the code that produces every number and table
of the paper, the hand-made inputs it uses, and the outputs the paper reports.

## Reproducing

```
cd orphans
python3 -m pip install -r requirements.txt     # Python 3.13, pinned versions
bash reproduce_paper.sh                        # download TLHdig 0.4, parse, run, write the numbers
```

`reproduce_paper.sh` downloads TLHdig Beta 0.4 from Zenodo (doi:10.5281/zenodo.24373727) and
checks its checksum, builds the token tables, runs every experiment and writes
`paper/generated/numbers.tex` (each number of the paper) and `paper/generated/tab_*.tex` (its
tables). `paper/generated/numbers_index.csv` names the result file and key behind each number.
The shipped `results/` and `paper/generated/` are the outputs the paper was built from, so a rerun
can be compared with them file by file.

All randomness is seeded and files are read in sorted order. Besides Zenodo, the run reads three
public sources over the network: eDiAna (Cuneiform Luwian lemmata, used to fill missing
analyses), the Konkordanz der hethitischen Keilschrifttafeln (known joins and duplicates, for the
join appendix) and the Open German WordNet and Princeton WordNet (the `wn` package, for the
check of the meaning classes).

## What each script does

Run in this order by `orphans/reproduce_paper.sh`; each can also be run alone (see its docstring).

| Script | What it does | Writes |
|---|---|---|
| `qtm/tlhdig.py` | parses the TLHdig XML into one row per word: spelling, lemma, word class, sign status (preserved, damaged, restored) | `data/tokens_marks.csv` |
| `qtm/variants.py` | makes the two versions of the token table: without restorations (C) and with them (A) | `data/tokens_*.csv` |
| `ediana_cluwian.py` | downloads the Cuneiform Luwian lemmata of eDiAna | `data/ediana_cluwian_forms.csv` |
| `fill_lemmas.py` | fills missing analyses from the same spelling elsewhere in TLHdig, or from eDiAna | `data/tokens_marks_filled.csv` |
| `run_experiments.py` | the placement method: validation on held-out manuscripts, fragment size, margin, orphan placement (E1–E6) | `report.json`, `E2_*`, `E3_*`, `E5_orphan_placement.csv` |
| `run_openset.py` | manuscripts from no reference tradition: how often they are wrongly placed (E9) | `E9_report.json` |
| `run_hypotheses.py` | scholarly groupings as hypotheses: compositions left out whole, contested texts (E10) | `E10_*` |
| `run_attribution.py` | splits each decision by word category and writing layer (E11) | `E11_report.json` |
| `run_profiles.py` | spelling profiles and distinctive words per tradition (E7) | `E7_*` |
| `run_wordclass.py` | each word category alone and the text without it (E8) | `E8_report.json` |
| `run_spellings_only.py` | the method with spellings only, without word classes | `R1_spellings_only.json` |
| `run_dating.py` | script date (Old, Middle, New Script, from the Konkordanz) as a rival explanation: labels shuffled within period, one period at a time, across periods (E12) | `E12_report.json` |
| `stats_corpus.py` | corpus counts | `corpus_stats.json` |
| `run_case.py` | one manuscript in detail: similarities, margin, decisive words (worked examples) | `case/case_*.json` |
| `run_known_joins.py`, `run_join_model.py` | joins and duplicates named in the Konkordanz: where they rank; a re-ranking model (appendix) | `known_joins/`, `joins/` |
| `compare_filled.py` | results before and after filling missing analyses | `comparison.json` |
| `run_unicode.py` | the method on cuneiform signs instead of transliteration (appendix) | `U_unicode.json` |
| `check_hfr_conventions.py` | how far TLHdig follows the HFR transliteration and annotation guides | `hfr_conventions.json` |
| `check_gloss_wordnet.py` | the meaning classes against the German and English WordNets | `wordnet_check/` |
| `run_senses.py` | context rules for words with more than one meaning | `senses/` |
| `review_wordclass.py` | examples per word-class rule and the score of the expert-marked audit | `wordclass_*.json`, `.csv` |
| `make_release.py` | places every manuscript of the residual bins, with nearest compositions and manuscripts | `data/release_C/` (the `dataset/` files) |
| `summarise_bins.py` | placements per residual bin and sphere of traditions | `bin_placements.json` |
| `../paper/make_numbers.py` | reads `results/` and writes every number and table of the paper | `paper/generated/` |
| `../paper/make_case_marks.py`, `make_case_figures.py` | data for the worked-example figure | `paper/figures/data/`, `paper/generated/case_data_c.tex` |
| `../paper/figures/*.py` | Figure 1: the archive map and the transliteration with estimated lost signs | `paper/generated/` |

`qtm/` holds the shared code: `assign.py` (centroids, similarity, margin), `features.py`
(tf-idf features), `groups.py` (the reference traditions), `wordclass.py` and `senses.py`
(word categories and meaning rules), `layers.py` (writing layers), `corpus.py`, `pieces.py`,
`konkordanz.py` (reading the Konkordanz). `tests/` checks the bracket parser.

## What each dataset is

Hand-made inputs in `orphans/labels/`:

| File | Content |
|---|---|
| `gloss_lexicon.tsv` | dictionary gloss to meaning class (realia, place, abstract noun ...) |
| `sense_rules.csv` | context rules for glosses with several meanings, each with evidence, dictionary reference and who decided it |
| `word_fixes.csv`, `title_pairs.csv`, `wordclass_corrections.csv` | corrections to the word-class rules: titles and divine names read as one agent or deity, single words |
| `wordclass_audit.csv` | a random sample of words with the expert's verdict on their class |
| `cth701_labels.csv`, `konkordanz_meta.csv`, `konkordanz_joins_duplicates.csv`, `known_joins_pages.json` | Konkordanz snapshots (CTH 701 subgroups, find data and script dates, joins and duplicates), with access dates in the `.source.txt` files |

Results in `orphans/results/`:

| Folder | Content |
|---|---|
| `tlhdig04_literature_C_filled/` | main results: literature-defined traditions, without restorations, missing analyses filled |
| `tlhdig04_literature_A_filled/` | the same with restorations |
| `tlhdig04_literature_C/` | without restorations, before filling |
| `tlhdig04/` | baseline: the four spheres of the earlier festival study, plus CTH-range controls |
| `wordclass_rule_changes*.csv` | how revisions of the word-class rules moved words between classes; they compare successive rule versions and are not rebuilt |

`paper/traditions.csv` lists the reference traditions with their defining studies;
`paper/data/wordnet_audit_expert.csv` is the expert's judgement of the cases where the meaning
classes and WordNet disagree.

## The dataset

`dataset/without_restorations/` (main) and `dataset/with_restorations/` hold the placements for
every manuscript of Laroche's residual bins (CTH 470, 500, 670, 832), the unclaimed rituals of
CTH 390–469 and the EBo fragments, built by the main and the comparison run.

| File | Content |
|---|---|
| `fragments.csv` | one row per manuscript: bin, legible words, status (placed, below margin, too small), the three nearest traditions with their similarity, the margin, the placed tradition, the five nearest compositions, the five and twenty nearest manuscripts, and the words of each category that count |
| `compositions.csv`, `traditions.csv` | the compositions and traditions the fragments are compared with |
| `summary.json` | counts per bin and status |

The paper reports the orphans (CTH 470 and EBo); their rows in `fragments.csv` agree with
`orphans/results/*/E5_orphan_placement.csv`.

The TLHdig corpus itself is not included; it is openly licensed and downloaded by the script.
The photograph and hand copy in Figure 1 are not included; they are published by the
Hethitologie-Portal Mainz.
