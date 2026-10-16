# Orphans and Archetypes: experiments

Code for the Mainz Hittite & AI workshop talk (November 2026) on assigning unidentified
Hittite ritual fragments (CTH 470, EBo) to textual traditions. The slides are
`../orphans_archetypes.qmd`, and `TALK_OUTLINE.md` has the talk structure.

## Data

- **TLHdig Beta 0.3** XML (Zenodo [10.5281/zenodo.20328284](https://doi.org/10.5281/zenodo.20328284)), parsed with
  `python3 -m qtm.tlhdig <unzipped release dir> tokens.csv`. The output has one row per word:
  `txtid, cth_number, source, lnr, lang, word, translit`.
- **CTH 701 subgroup labels** (Salvini–Wegner a–f, plus script date) for 131 manuscripts, from the
  StBoT 73 working sheet `early_hurrian_nicer_tsne_final_for_280424_only_cth701_with_zeit.csv`.
  126 of them match TLHdig 0.3 IDs (unpublished Bo numbers have since changed).

## Run

```
python3 -m pip install scikit-learn pandas lxml matplotlib
python3 run_experiments.py tokens.csv --labels701 cth701.csv --out results/tlhdig03
python3 make_figures.py results/tlhdig03 ../img/orphans
```

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
