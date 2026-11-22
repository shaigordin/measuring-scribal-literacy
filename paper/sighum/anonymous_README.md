# Orphans and Archetypes: code and results (anonymous review copy)

Supplementary material for the submission "Orphans and Archetypes: Quantitative Tradition
Mapping for Fragmentary Hittite Texts". It holds the code that produces every number, table
and figure of the paper, and the outputs it was run on.

## Contents

- `qtm/`: the method (parsing TLHdig, word classes, features, placement, decomposition).
- `run_*.py`, `run_*.sh`, `reproduce.sh`: the experiments; `reproduce.sh` downloads TLHdig 0.4
  from Zenodo (doi:10.5281/zenodo.24373727), checks its checksum and reruns everything.
- `labels/`: hand-made inputs (Konkordanz snapshots, the gloss-to-class list, the context rules
  with their dictionary references).
- `results/`: the outputs used in the paper. Main run: `tlhdig04_literature_C_filled` (without
  restorations); comparison: `tlhdig04_literature_A_filled` (with restorations).
- `../paper/make_numbers.py`: writes every number in the paper from `results/` into
  `../paper/generated/numbers.tex`; `../paper/figures/*.py` draw the figures.

## Reproducing

```
python3 -m pip install -r requirements.txt     # Python 3.13, pinned versions
bash reproduce.sh                              # download TLHdig 0.4, parse, run, write results
cd ../paper && python3 make_numbers.py         # numbers and tables of the paper
```

All randomness is seeded and files are read in sorted order, so a rerun gives the same numbers.
The TLHdig corpus itself is not included; it is openly licensed and downloaded by `reproduce.sh`.
Photographs and hand copies used in Figure 1 are not included; they are published by the
Hethitologie-Portal Mainz.
