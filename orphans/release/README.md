# Orphans and Archetypes: closest traditions, compositions and join candidates for the unplaced fragments of the Hittite corpus (TLHdig 0.3)

Version 1.0.0 (2026-11-10). Licence: CC BY 4.0. Data source: TLHdig Beta Version 0.3,
[doi:10.5281/zenodo.20328284](https://doi.org/10.5281/zenodo.20328284). Code: [https://github.com/shaigordin/measuring-scribal-literacy](https://github.com/shaigordin/measuring-scribal-literacy), folder `orphans/`.

Thousands of Hittite tablet fragments are filed in Laroche's *Catalogue des textes hittites* (CTH) under
residual numbers, such as "fragments of rituals" (CTH 470) or "fragments of festivals" (CTH 670), because
nobody could yet say which composition they belong to. This dataset gives, for each of them, the textual
traditions, compositions and manuscripts it is closest to, and the manuscripts that could be pieces of the
same tablet (join candidates). The results come from one reproducible model, described in the paper
[PAPER REFERENCE]. They are leads for philologists to check, not attributions.

## What is in the dataset

| File | Content |
|---|---|
| `fragments.csv` | One row per text: 11,368 texts in Laroche's residual bins and EBo pieces. For each one, its 3 closest traditions, whether it is placed, open-set and robustness checks, its 5 closest compositions, its 5 and 20 closest manuscripts, its join candidates and its word-category profile. |
| `join_candidates.csv` | One row per fragment and each of its 20 closest manuscripts (rank 1 to 20), with the word-by-word join barcode and the three join checks. |
| `traditions.csv` | The ten reference traditions, their CTH numbers and the studies that define them. |
| `compositions.csv` | The 607 compositions (CTH numbers) that fragments are compared with. |
| `datapackage.json` | Machine-readable description of every file and column (Frictionless Data). |
| `summary.json` | The counts quoted in this README. |
| `CITATION.cff`, `LICENSE.txt` | How to cite; the licence. |

All files are UTF-8 CSV with a header row. Lists inside a cell are separated by `; ` and ordered from the
closest down. Booleans are `True`/`False`; an empty cell means "not applicable".

### Which texts

Every TLHdig 0.3 text filed under one of Laroche's residual bins, and every EBo piece (the fragments
rediscovered in the Boğazköy museum in 2025, transliterations only), wherever TLHdig files it. The model
reads analysed words, so texts with fewer than 5 analysed words are listed with status `too_small` and no
results. Of the 11,368 texts, 7,529 have results: 3,400 are placed in a tradition and 4,129
are scored but not placed. 3,839 are too small.

| Bin | Texts | Under 5 words | Scored, not placed | Placed | With join candidates |
|---|---|---|---|---|---|
| CTH 470 fragments of rituals | 1,925 | 242 | 977 | 706 | 223 |
| CTH 500 fragments of Kizzuwatna rituals | 479 | 42 | 206 | 231 | 86 |
| CTH 670 fragments of festivals | 3,513 | 544 | 1,225 | 1,744 | 1,012 |
| CTH 832 fragments of various content | 4,260 | 2,455 | 1,358 | 447 | 198 |
| CTH 390-469 rituals no study groups | 1,038 | 502 | 289 | 247 | 94 |
| EBo filed under other CTH numbers | 153 | 54 | 74 | 25 | 21 |

## The method in brief

1. **Reference traditions.** Ten traditions of rituals and festivals, each defined by the study that argued
   for it. Laroche's CTH numbers are only the address of each text. Every text of these CTH numbers with
   17 or more analysed words is a reference manuscript (1,626 in all).

| Tradition | CTH | Reference manuscripts | Defining study |
|---|---|---|---|
| Arzawa / western rituals | 394, 402, 406, 410, 425, 433 | 11 | Bawanypeck 2005 (THeth 25); Mouton 2010; Archi 2015 (BiOr 72) |
| Hattian cult layer | 591, 627, 725–729, 731–746, 820–821 | 480 | Klinger 1996 (StBoT 37) |
| Kizzuwatna rituals | 404, 471–499 | 165 | Miller 2004 (StBoT 46); Strauß 2006; Görke 2010 |
| Kizzuwatna–Lower Land (Hurrian) | 628, 699–700, 711–713, 719, 722 | 318 | Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3; Wegner and Salvini 1991 (ChS I/4) |
| Luwian festivals (Ištanuwa, Lallupiya) | 665, 771–773 | 52 | HFR edition module 'Luwian festivals' (hethport.net/HFR) |
| Luwian rituals (Puriyanni, Kuwattalla) | 758–763 | 10 | Mouton and Yakubovich 2021 (JLR 19/1); Yakubovich and Mouton 2023 (StBoT 72) |
| Mixed (Hurrian, Syrian, Luwian) | 704–706, 720 | 200 | Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3 |
| Palaic festivals | 750–754 | 34 | HFR edition module 'Palaic festivals' (hethport.net/HFR) |
| Syro-Mesopotamia (Hurrian) | 698, 701, 714–715, 721 | 167 | Gordin, Yavasan and Romach 2025 (StBoT 73), Table 3; Salvini and Wegner 1986 (ChS I/2) |
| Ḫuwaššanna festivals | 690–694 | 189 | HFR edition module 'Ḫuwaššanna'; Laroche, CTH titles |

2. **Features.** Each text is read as its word forms (TLHdig's normalised forms) and the sign sequences of
   its spellings (sign 1- to 3-grams within a word), so both vocabulary and scribal habit count. They are
   weighted by tf-idf, fitted on the reference manuscripts.
3. **Closest traditions.** Cosine similarity between a fragment and the centroid (average) of each
   tradition. The *margin* is the lead of the closest tradition over the runner-up. A fragment is *placed*
   when its margin is at least 0.018. That threshold was calibrated on reference texts cut to fragment
   size, so that 80% of the fragments placed this way are placed correctly. On complete reference
   manuscripts, leave-one-out accuracy is 84% (the largest tradition alone would give 30%).
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
   As a check, the CTH 390-469 texts in the dataset have a known composition. Of the 519 of them
   whose CTH number has at least one other manuscript, the own composition ranks first among all
   607 for 223 (43%) and among the closest five for 339
   (65%).
7. **Closest manuscripts and join candidates.** The 20 most similar manuscripts among all 18,491 TLHdig texts
   with 5 or more analysed words. For each pair a *barcode* compares the fragment's content words one by
   one: the same spelling in the candidate (`S`), a different spelling (`W`), or absent (`.`). A candidate
   passes the **join checks**, which were fixed before looking at any result, if it has (1) at least half
   of the fragment's content words, (2) every shared word spelled exactly as in the fragment, and (3) at
   least one shared two-word phrase. 1,634 fragments have at least one candidate that passes
   (5,016 pairs in all).
8. **Word-category profile.** The `words_*` columns give the share of a fragment's analysed words in each
   of ten categories (function words, verbs, realia, agents and deities, places, animals/body/nature,
   abstract nouns, adjectives, foreign words, other). Categories come from rules over the TLHdig editors'
   own word analyses, checked in a blind audit of 178 words (89% correct, weighted by how often each confidence level occurs, before the rules were revised on the audit). Nouns are classed by the meaning of
   their German gloss. That word lexicon remains to be verified manually.

### Placed fragments by tradition

| Tradition | Fragments placed |
|---|---|
| Hattian cult layer | 1,493 |
| Kizzuwatna rituals | 990 |
| Kizzuwatna–Lower Land (Hurrian) | 381 |
| Syro-Mesopotamia (Hurrian) | 167 |
| Mixed (Hurrian, Syrian, Luwian) | 121 |
| Arzawa / western rituals | 75 |
| Ḫuwaššanna festivals | 63 |
| Luwian rituals (Puriyanni, Kuwattalla) | 59 |
| Luwian festivals (Ištanuwa, Lallupiya) | 43 |
| Palaic festivals | 8 |

## How to read the files

### `fragments.csv`

| Column | Meaning |
|---|---|
| `txtid` | TLHdig text id (publication number; a trailing + marks a text TLHdig already stores as a join). |
| `filed_under_cth` | CTH number under which TLHdig files the text (Laroche's catalogue, as on the Portal). |
| `laroche_bin` | The residual bin the text comes from: CTH 470, 500, 670, 832, the CTH 390-469 rituals no study groups, or an EBo piece filed under another CTH. |
| `is_ebo` | True for the EBo pieces (fragments rediscovered at Boğazköy in 2025, transliterations only). |
| `n_words_analysed` | Words with a TLHdig word analysis: what the model reads. |
| `n_words_legible` | Legible words, analysed or not (used by the spellings-only check). |
| `tlhdig_url` | The text in TLHdig on the Mainz Portal. |
| `konkordanz_url` | The text in the Konkordanz der hethitischen Keilschrifttafeln (first piece of a join). |
| `status` | placed: the nearest tradition leads the runner-up by at least the margin; below_margin: scored but not placed; too_small: fewer than 5 analysed words, no results. |
| `tradition_1` | Nearest reference tradition (highest cosine similarity to its centroid). |
| `similarity_1` | Cosine similarity to tradition_1 (0-1). |
| `tradition_2` | Second-nearest tradition. |
| `similarity_2` | Cosine similarity to tradition_2. |
| `tradition_3` | Third-nearest tradition. |
| `similarity_3` | Cosine similarity to tradition_3. |
| `margin` | similarity_1 minus similarity_2: how clearly the nearest tradition wins. |
| `placed_tradition` | tradition_1 if margin >= the calibrated margin (see README), else empty. |
| `fit_floor` | Open-set fit floor for a fragment of this size: 5th percentile of the similarity of reference windows of the same size to their own tradition. |
| `below_fit_floor` | similarity_1 is below fit_floor: the fragment fits no tradition as well as 95% of genuine members do. |
| `nearest_with_outside_genres` | Nearest class when eight outside genres (myths, prayers, oracles, historical texts, instructions, cult inventories, other festivals, Taurisa rituals) are added as classes. |
| `nearest_is_outside_genre` | nearest_with_outside_genres is an outside genre, by at least the margin: the fragment may not be a ritual or festival of the reference traditions. |
| `spellings_only_placed` | Tradition placed by the spellings-only check (sign n-grams of every legible word, reference including manuscripts without word analyses), else empty. |
| `spellings_only_agrees` | Both models place the fragment and agree. Empty if either does not place it. |
| `common_features_share` | Share of the margin carried by features attested in at least 25% of reference texts (e.g. nu, the sign a). Negative: common features pull against the decision. |
| `rests_on_common_features` | More than half of the margin comes from common features: the placement rests on common material and is weaker. |
| `compositions_top5` | The five nearest compositions (CTH numbers outside the residual bins), '; '-separated, nearest first. |
| `compositions_top5_similarity` | Cosine similarity to each of compositions_top5. |
| `manuscripts_top5` | The five nearest manuscripts in the whole release, '; '-separated, nearest first. |
| `manuscripts_top5_similarity` | Cosine similarity to each of manuscripts_top5. |
| `manuscripts_top20` | The 20 nearest manuscripts; details for each in join_candidates.csv. |
| `join_candidates` | Those of the 20 nearest manuscripts that pass all three join checks. |
| `words_function_words` | Share of the analysed words in the word category 'function words'. |
| `words_verbs` | Share of the analysed words in the word category 'verbs'. |
| `words_realia` | Share of the analysed words in the word category 'realia'. |
| `words_agents_and_deities` | Share of the analysed words in the word category 'agents and deities'. |
| `words_places` | Share of the analysed words in the word category 'places'. |
| `words_animals_body_nature` | Share of the analysed words in the word category 'animals body nature'. |
| `words_abstract_nouns` | Share of the analysed words in the word category 'abstract nouns'. |
| `words_adjectives` | Share of the analysed words in the word category 'adjectives'. |
| `words_foreign_words` | Share of the analysed words in the word category 'foreign words'. |
| `words_other_words` | Share of the analysed words in the word category 'other words'. |

### `join_candidates.csv`

| Column | Meaning |
|---|---|
| `txtid` | The fragment (as in fragments.csv). |
| `rank` | 1 = nearest manuscript. |
| `candidate_txtid` | A manuscript of the whole release with 5+ analysed words. |
| `candidate_cth` | CTH number under which TLHdig files the candidate. |
| `candidate_group` | The candidate's reference tradition, residual pool ('CTH 390–469 residue', 'CTH 500 Kizzuwatna fragments'), 'orphan' (CTH 470 or EBo), the Laroche bin, or empty for other CTH numbers. |
| `candidate_n_words` | Analysed words of the candidate. |
| `similarity` | Cosine similarity of fragment and candidate. |
| `barcode` | One character per distinct content word of the fragment, in line order: S = the candidate has the word spelled the same way, W = spelled differently, . = absent. |
| `fragment_content_words` | Distinct content words of the fragment (numbers and broken words left out). |
| `shared_words` | Content words of the fragment found in the candidate (S + W). |
| `same_spelling` | Shared words spelled identically (S). |
| `different_spelling` | Shared words spelled differently (W). |
| `shared_phrases` | Two-word phrases of the fragment (adjacent words) that also occur in the candidate, '; '-separated. |
| `check_half_the_words` | Check 1: the candidate has at least half of the fragment's content words. |
| `check_same_spellings` | Check 2: every shared word is spelled exactly as in the fragment (one scribal habit). |
| `check_shared_phrase` | Check 3: at least one shared two-word phrase. |
| `passes_join_checks` | All three checks pass: a join candidate (or a duplicate copy) to check on the tablets. |
| `candidate_tlhdig_url` | The candidate in TLHdig. |

### `traditions.csv`

| Column | Meaning |
|---|---|
| `tradition` | Reference tradition. |
| `cth` | Its CTH numbers (Laroche), space-separated. |
| `reference_manuscripts` | Reference manuscripts (17+ analysed words). |
| `defining_study` | The study that argued for the tradition. |

### `compositions.csv`

| Column | Meaning |
|---|---|
| `cth` | CTH number. |
| `manuscripts` | Manuscripts with 5+ analysed words that make up the composition's centroid. |
| `tradition` | Reference tradition or residual pool of the CTH number, if any. |

### Two examples

**EBo 133** (filed under CTH 670, 19 analysed words): nearest tradition Ḫuwaššanna festivals (0.2751), then Palaic festivals (0.2321); margin 0.0431, status `placed`. Nearest compositions: CTH 656; CTH 694; CTH 692; CTH 750; CTH 705. Join candidates: KBo 44.140. Its five nearest manuscripts and the candidates that pass the join checks:

| rank | candidate_txtid | candidate_cth | similarity | barcode | passes_join_checks |
|---|---|---|---|---|---|
| 1 | KBo 21.51 | 705 | 0.6125 | SS.S...... | False |
| 2 | KBo 43.137 | 670 | 0.5519 | SS.S...... | False |
| 3 | KBo 42.97 | 635 | 0.5394 | S......... | False |
| 4 | KBo 22.226 | 670 | 0.5312 | SS.S...... | False |
| 5 | KBo 51.173 | 670 | 0.5225 | SS.S...... | False |
| 11 | KBo 44.140 | 669 | 0.4544 | SSSS....S. | True |

EBo 133 has no photograph and no catalogue entry yet. KBo 44.140 is the only one of its 20 nearest
manuscripts that passes the three checks. Both repeat the formula "1-ŠU e-ku-zi / 1 NINDA ta-kar-mu-un
pár-ši-ia" in the same spellings. Whether the two pieces join can only be decided on the tablets.

**KBo 41.22** (filed under CTH 470, 33 analysed words): nearest tradition Luwian rituals (Puriyanni, Kuwattalla) (0.3889), then Kizzuwatna rituals (0.2455); margin 0.1435, status `placed`. Nearest compositions: CTH 409; CTH 760; CTH 458; CTH 335; CTH 767. Join candidates: none. Its five nearest manuscripts:

| rank | candidate_txtid | candidate_cth | similarity | barcode | passes_join_checks |
|---|---|---|---|---|---|
| 1 | KBo 9.125+ | 409 | 0.3486 | .S..SSSS.S..SSS..S..SS..S... | False |
| 2 | KBo 45.267 | 760 | 0.3475 | ......SS.S...........S...... | False |
| 3 | KBo 21.6 | 409 | 0.3409 | ....SSS......SS....SS....... | False |
| 4 | CHDS 7.140+ | 409 | 0.3269 | ....SSSS.S.................. | False |
| 5 | KBo 44.89 | 409 | 0.3056 | ......S..................... | False |

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

| Analysed words | Fragments scored | With join candidates | Share |
|---|---|---|---|
| 5-9 | 3,285 | 772 | 24% |
| 10-16 | 1,909 | 428 | 22% |
| 17-39 | 1,714 | 367 | 21% |
| 40+ | 621 | 67 | 11% |

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
git clone https://github.com/shaigordin/measuring-scribal-literacy
cd measuring-scribal-literacy/orphans
python3 -m pip install -r requirements.txt      # Python 3.13
bash reproduce.sh                                # downloads TLHdig 0.3 from Zenodo, runs all experiments
python3 make_release.py data/tokens.csv --run results/tlhdig03_literature --out release
python3 release_docs.py release --version 1.0.0 --zip
```

`make_release.py` takes about 10 minutes on a laptop. It reproduces exactly the placements, open-set and
robustness results of the paper (files `E5_orphan_placement.csv`, `E5b_residue_placement.csv`,
`E9_orphan_fit.csv`, `E11_report.json`, `R1_spellings_only.json` in `results/tlhdig03_literature/`).

## How to cite

Please cite this dataset, the paper and TLHdig:

- Gordin, Shai. Orphans and Archetypes: closest traditions, compositions and join candidates for the unplaced fragments of the Hittite corpus (TLHdig 0.3), version 1.0.0. Zenodo. [DOI].
- [PAPER REFERENCE]
- Müller, Gerfrid, Doris Prechel, Elisabeth Rieken and Daniel Schwemer. *Thesaurus Linguarum Hethaeorum
  digitalis (TLHdig) Beta Version 0.3*. Zenodo. doi:10.5281/zenodo.20328284.

`CITATION.cff` has the same information in machine-readable form.

## Licence

CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/), like TLHdig 0.3, from which it is derived.
