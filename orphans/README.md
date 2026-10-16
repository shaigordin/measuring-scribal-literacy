# Orphans and Archetypes: experiments

Code for the Mainz workshop talk on assigning unidentified Hittite ritual fragments
(CTH 470, EBo) to textual traditions. See `TALK_OUTLINE.md` for the talk structure.

```
python3 -m pip install scikit-learn pandas
python3 run_experiments.py CORPUS.csv [--orphans ORPHANS.csv] --out results/<run>
```

`CORPUS.csv` uses the token-level schema of Yavasan & Gordin 2024
(Zenodo 10.5281/zenodo.14266302): `txtid, lnr, cth_number, word, translit`,
plus an optional `subgroup` column for CTH 701 (a, a1, b ...).

`results/zenodo_pilot/` is a first run on the Zenodo CSV, which keeps only glossed
words. That leaves CTH 832 with a single text of 17+ words, so the pilot
is effectively CTH 670 vs 701, plus the controls.
