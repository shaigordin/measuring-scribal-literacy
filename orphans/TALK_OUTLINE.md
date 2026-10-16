# Orphans and Archetypes: talk outline (draft, assumes a 20-minute slot)

Mainz workshop on Hittite and AI. The talk builds on Gordin, Yavasan and Romach 2025,
"Matters of Genre, Style and Orthography" (StBoT 73: 107–123).

| # | Section | Min | Slides | Evidence / figure |
|---|---------|-----|--------|-------------------|
| 1 | **The orphan problem** | 2 | 2 | Laroche's residual CTH 470, the EBo digitisation wave, and why parallel-passage search fails on low-coverage fragments |
| 2 | **Where we left off (StBoT 73)** | 2 | 2 | Fig. 1 "galaxy" (tf-idf, t-SNE), CTH 701 under the microscope (KBo 23.44 vs KBo 38.281+) |
| 3 | **From exploration to assignment** | 3 | 3 | Two reference spaces (word tf-idf; sign n-grams for orthography), nearest-centroid scores, open-set abstention |
| 4 | **Does it work? Validation** | 4 | 4 | E1 leave-one-out accuracy vs majority/permutation baseline; E2 coverage curve (accuracy vs fragment size in words); E4 logogram ablation (orthography vs vocabulary) |
| 5 | **CTH 701 as a test bed** | 3 | 2 | E3 Salvini–Wegner subgroups a–f recovered or not; where group f and the unclassified 701 fragments land |
| 6 | **Orphans placed** | 3 | 3 | E5 CTH 470 / EBo fragments: ranked candidate traditions, abstentions, two worked examples for philological check |
| 7 | **QTM: witnesses and archetypes** | 2 | 2 | Fragments as low-coverage witnesses; how much of each tradition's "archetype" vocabulary the orphans cover; transmission questions |
| 8 | **Limits and next steps** | 1 | 1 | Normalisation, preservation bias, script date (MS/NS) as a confounder, joins, sign-level paleography (link to the DANES landmark work) |

## Experiments (code in `run_experiments.py`)

- **E1 Reference space.** Leave-one-text-out nearest-centroid assignment across CTH 670, 701, 832 (+ controls 628, 699, 500, 694), compared against majority and label-permutation baselines.
- **E2 Coverage curve.** Well-attested texts are cut to random k-word windows (5–60 words) to measure how small a fragment can be and still be assigned. This sets the abstention threshold for E5.
- **E3 CTH 701 subgroups.** The same procedure on the a–f labels, where partial ground truth exists.
- **E4 Ablation.** Logograms dropped, to separate scribal orthography from cultic vocabulary.
- **E5 Orphan placement.** CTH 470 and EBo fragments scored against every tradition, with an open-set margin.
