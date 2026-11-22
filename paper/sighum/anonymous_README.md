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

## Contents

- `orphans/qtm/`: the method (parsing TLHdig, word classes, meaning rules, features, placement,
  decomposition).
- `orphans/run_*.py` and the other scripts named in `reproduce_paper.sh`: the experiments.
- `orphans/labels/`: hand-made inputs. Konkordanz snapshots (with access dates), the
  gloss-to-class list, the context rules for meaning classes with their dictionary references,
  the word-class corrections and the expert-marked audit sample.
- `orphans/results/`: the outputs the paper reports. Main run: `tlhdig04_literature_C_filled`
  (without restorations); comparison: `tlhdig04_literature_A_filled` (with restorations);
  `tlhdig04` is the baseline, `tlhdig04_literature_C` the run before missing analyses were
  filled. The `wordclass_rule_changes*.csv` files record how revisions of the word-class rules
  moved words between classes; they compare successive versions of the rules and are not rebuilt.
- `paper/make_numbers.py`: reads `results/` and writes the paper's numbers and tables.
  `paper/figures/*.py` prepare Figure 1 (the map and the transliteration).

The TLHdig corpus itself is not included; it is openly licensed and downloaded by the script.
The photograph and hand copy in Figure 1 are not included; they are published by the
Hethitologie-Portal Mainz.
