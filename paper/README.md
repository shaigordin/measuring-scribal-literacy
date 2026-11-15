# Orphans and Archetypes: paper

The paper version of the Mainz Hittite & AI workshop talk, in the CEUR-WS template (`ceurart`)
that the Computational Humanities Research (CHR) conference uses. The talk itself is
`../orphans_archetypes.qmd`; the experiments are in `../orphans/`.

## Build

```
bash build.sh
```

`build.sh` runs `make_numbers.py`, then `latexmk -lualatex`. It stops if any number in the text is
undefined. It needs Python 3 (standard library only) and TeX Live with LuaLaTeX, BibTeX and the
Libertinus fonts (Debian/Ubuntu: `texlive-luatex texlive-latex-extra texlive-publishers
texlive-fonts-extra latexmk`). LuaLaTeX is used because the transliterations need Unicode
(ḫ, š, subscript numerals).

## Where the numbers come from

No result is typed by hand. `make_numbers.py` reads the experiment outputs in
`../orphans/results/` and writes:

- `generated/numbers.tex`: one macro per number, used in the text as `\Q{key}`;
- `generated/tab_*.tex`: the bodies of every results table;
- `generated/numbers_index.csv`: every key with its value and the file and field it was read from.

The main reference is `results/tlhdig03_literature/` (the literature-defined traditions);
`results/tlhdig03/` is the StBoT 73 baseline. Figures are read directly from
`../img/orphans/literature/`. The reference traditions and their CTH numbers come from
`../orphans/qtm/groups.py`; `traditions.csv` adds the defining studies and the criterion for
each, keyed by one CTH number of the tradition, so a tradition added to `groups.py` picks up its
row (or shows "justification pending" until a row is added).

## After the experiments change

1. Rerun the experiments (`bash ../orphans/reproduce.sh`) or pull the new results.
2. `bash build.sh`.
3. Reread the sentences that interpret a number (for example "the weakest tradition is also the
   smallest", "spelling adds nothing beyond the words"): the macros update, the interpretation
   does not.

## Files

| File | Content |
|---|---|
| `main.tex` | the paper |
| `references.bib` | bibliography; entries marked `% verify` still need a check against the item |
| `make_numbers.py` | numbers and tables from the results |
| `traditions.csv` | defining studies and criterion per reference tradition |
| `ceurart.cls`, `elsarticle-num-names.bst`, `cc-by.pdf` | CEUR-WS template 0.5.3 (LPPL 1.3, `Copyright.lppl.txt`), from ceur-ws.org/Vol-XXX/CEURART.zip |
| `main.pdf` | the current build |
