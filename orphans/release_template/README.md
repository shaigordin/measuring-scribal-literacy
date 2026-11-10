# $title

Version $version ($date). Licence: CC BY 4.0. Data source: TLHdig Beta Version 0.3,
[doi:$tlhdig_doi](https://doi.org/$tlhdig_doi). Code: [$code_url]($code_url), folder `orphans/`.

Thousands of Hittite tablet fragments are filed in Laroche's *Catalogue des textes hittites* (CTH) under
residual numbers, such as "fragments of rituals" (CTH 470) or "fragments of festivals" (CTH 670), because
nobody could yet say which composition they belong to. This dataset gives, for each of them, the textual
traditions, compositions and manuscripts it is closest to, and the manuscripts that could be pieces of the
same tablet (join candidates). The results come from one reproducible model, described in the paper
[PAPER REFERENCE]. They are leads for philologists to check, not attributions.

## What is in the dataset

| File | Content |
|---|---|
| `fragments.csv` | One row per text: $texts texts in Laroche's residual bins and EBo pieces. For each one, its 3 closest traditions, whether it is placed, open-set and robustness checks, its 5 closest compositions, its 5 and 20 closest manuscripts, its join candidates and its word-category profile. |
| `join_candidates.csv` | One row per fragment and each of its 20 closest manuscripts (rank 1 to 20), with the word-by-word join barcode and the three join checks. |
| `traditions.csv` | The ten reference traditions, their CTH numbers and the studies that define them. |
| `compositions.csv` | The $compositions compositions (CTH numbers) that fragments are compared with. |
| `datapackage.json` | Machine-readable description of every file and column (Frictionless Data). |
| `summary.json` | The counts quoted in this README. |
| `CITATION.cff`, `LICENSE.txt` | How to cite; the licence. |

All files are UTF-8 CSV with a header row. Lists inside a cell are separated by `; ` and ordered from the
closest down. Booleans are `True`/`False`; an empty cell means "not applicable".

### Which texts

Every TLHdig 0.3 text filed under one of Laroche's residual bins, and every EBo piece (the fragments
rediscovered in the Boğazköy museum in 2025, transliterations only), wherever TLHdig files it. The model
reads analysed words, so texts with fewer than 5 analysed words are listed with status `too_small` and no
results. Of the $texts texts, $with_results have results: $placed are placed in a tradition and $below_margin
are scored but not placed. $too_small are too small.

$bins_table

## The method in brief

1. **Reference traditions.** Ten traditions of rituals and festivals, each defined by the study that argued
   for it. Laroche's CTH numbers are only the address of each text. Every text of these CTH numbers with
   17 or more analysed words is a reference manuscript ($reference in all).

$traditions_table

2. **Features.** Each text is read as its word forms (TLHdig's normalised forms) and the sign sequences of
   its spellings (sign 1- to 3-grams within a word), so both vocabulary and scribal habit count. They are
   weighted by tf-idf, fitted on the reference manuscripts.
3. **Closest traditions.** Cosine similarity between a fragment and the centroid (average) of each
   tradition. The *margin* is the lead of the closest tradition over the runner-up. A fragment is *placed*
   when its margin is at least $margin. That threshold was calibrated on reference texts cut to fragment
   size, so that $precision of the fragments placed this way are placed correctly. On complete reference
   manuscripts, leave-one-out accuracy is $loo (the largest tradition alone would give $majority).
4. **Open-set checks.** A fragment can be closer to one tradition than to the others and still belong to
   none of them. `below_fit_floor` flags fragments whose best similarity is lower than that of 95% of
   reference fragments of the same size. `nearest_is_outside_genre` flags fragments that are closer to
   another genre (myths, prayers, oracles, historical texts, instructions, cult inventories, other festivals,
   the Taurisa rituals) when these are added as classes.
5. **Robustness checks.** `spellings_only_*` repeats the placement with spellings alone, with a reference
   that includes manuscripts TLHdig has not analysed yet (all Luwian rituals and many others).
   `rests_on_common_features` flags placements whose margin comes mostly from features found in a quarter
   or more of all reference texts (such as *nu* or the sign *a*). These are weaker.
6. **Closest compositions.** Cosine similarity to the centroid of each CTH number outside the residual bins
   (all its manuscripts with 5 or more analysed words). A fragment is left out of its own CTH number.
7. **Closest manuscripts and join candidates.** The 20 most similar manuscripts among all $pool TLHdig texts
   with 5 or more analysed words. For each pair a *barcode* compares the fragment's content words one by
   one: the same spelling in the candidate (`S`), a different spelling (`W`), or absent (`.`). A candidate
   passes the **join checks**, which were fixed before looking at any result, if it has (1) at least half
   of the fragment's content words, (2) every shared word spelled exactly as in the fragment, and (3) at
   least one shared two-word phrase. $with_joins fragments have at least one candidate that passes
   ($join_pairs pairs in all).
8. **Word-category profile.** The `words_*` columns give the share of a fragment's analysed words in each
   of ten categories (function words, verbs, realia, agents and deities, places, animals/body/nature,
   abstract nouns, adjectives, foreign words, other). Categories come from rules over the TLHdig editors'
   own word analyses, checked in a blind audit of $audit_n words ($audit_acc correct, weighted by how often each confidence level occurs, before the rules were revised on the audit). Nouns are classed by the meaning of
   their German gloss. That word lexicon remains to be verified manually.

### Placed fragments by tradition

$placed_table

## How to read the files

### `fragments.csv`

$fragments_columns

### `join_candidates.csv`

$joins_columns

### `traditions.csv`

$traditions_columns

### `compositions.csv`

$compositions_columns

### Two examples

$example_ebo

EBo 133 has no photograph and no catalogue entry yet. KBo 44.140 is the only one of its 20 nearest
manuscripts that passes the three checks. Both repeat the formula "1-ŠU e-ku-zi / 1 NINDA ta-kar-mu-un
pár-ši-ia" in the same spellings. Whether the two pieces join can only be decided on the tablets.

$example_kbo

## How to use it

- **In a spreadsheet:** open `fragments.csv` and filter by `laroche_bin`, `status` or `placed_tradition`.
  Each row links to the text in TLHdig (`tlhdig_url`) and to the Konkordanz (`konkordanz_url`).
- **To look for joins:** filter `join_candidates.csv` on `passes_join_checks = True`. Start with high
  `fragment_content_words` and `shared_words`, and with candidates that are themselves fragments. Then check
  the photographs (Fotoarchiv), find spot, script and clay in the Konkordanz, and the tablets.
- **In Python:**

  ```python
  import pandas as pd
  f = pd.read_csv("fragments.csv", keep_default_na=False)
  j = pd.read_csv("join_candidates.csv", keep_default_na=False)
  placed = f[f.status == "placed"]
  strong = placed[(placed.rests_on_common_features == "False") & (placed.below_fit_floor == "False")]
  joins = j[j.passes_join_checks == "True"].sort_values("shared_words", ascending=False)
  ```

- **In R:** `f <- read.csv("fragments.csv", encoding = "UTF-8", na.strings = "")`.

## Limits

- **Leads, not attributions.** A placement says that a fragment's words and spellings are closest to a
  tradition, not that it belongs to it. Use the margin, the open-set flags and `rests_on_common_features`
  to judge how strong a placement is.
- **Join or duplicate?** The barcode cannot tell a join from another copy of the same text. A candidate that
  passes the checks may be a duplicate or a parallel text. Small fragments pass the checks more easily
  (table below), so a candidate for a fragment with few words is weak evidence.

$size_table

- **Unanalysed texts.** TLHdig 0.3 has no word analyses for some texts (all of the Luwian rituals, CTH
  758-763, and many others). The main model cannot read them, so traditions that depend on them have few
  reference manuscripts. The spellings-only columns show where this matters.
- **Word lexicon.** The meaning classes of nouns, behind the `words_*` columns, come from a lexicon of
  German glosses that remains to be verified manually.
- **TLHdig ids.** A trailing `+` marks a text TLHdig already stores as a join. A few ids occur under two
  CTH numbers in TLHdig 0.3; `filed_under_cth` gives the residual bin.
- **Release.** All results refer to TLHdig Beta 0.3. New TLHdig releases (new analyses, new joins, new
  EBo pieces) will change them. Rebuild the dataset as below.

## How to rebuild it

Everything is produced by committed code from the public TLHdig release. Nothing is edited by hand.

```
git clone $code_url
cd measuring-scribal-literacy/orphans
python3 -m pip install -r requirements.txt      # Python 3.13
bash reproduce.sh                                # downloads TLHdig 0.3 from Zenodo, runs all experiments
python3 make_release.py data/tokens.csv --run results/tlhdig03_literature --out release
python3 release_docs.py release --version $version --zip
```

`make_release.py` takes about 10 minutes on a laptop. It reproduces exactly the placements, open-set and
robustness results of the paper (files `E5_orphan_placement.csv`, `E5b_residue_placement.csv`,
`E9_orphan_fit.csv`, `E11_report.json`, `R1_spellings_only.json` in `results/tlhdig03_literature/`).

## How to cite

Please cite this dataset, the paper and TLHdig:

- Gordin, Shai. $title, version $version. Zenodo. [DOI].
- [PAPER REFERENCE]
- Müller, Gerfrid, Doris Prechel, Elisabeth Rieken and Daniel Schwemer. *Thesaurus Linguarum Hethaeorum
  digitalis (TLHdig) Beta Version 0.3*. Zenodo. doi:$tlhdig_doi.

`CITATION.cff` has the same information in machine-readable form.

## Licence

CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), like TLHdig 0.3, from which it is derived.
