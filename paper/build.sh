#!/usr/bin/env bash
# Build the paper: regenerate every number and table from ../orphans/results, then typeset.
#   bash build.sh
# Needs Python 3 (standard library only) and TeX Live with lualatex, bibtex and the Libertinus fonts.
set -euo pipefail
cd "$(dirname "$0")"
python3 make_numbers.py
python3 make_case_figures.py
# Figure 1 (pipeline), also exported as PNG and SVG for the workshop deck
(cd figures && lualatex -interaction=nonstopmode -halt-on-error pipeline.tex >/dev/null \
  && ! grep -q "Undefined number" pipeline.log \
  && pdftocairo -png -r 300 -singlefile pipeline.pdf pipeline && pdftocairo -svg pipeline.pdf pipeline.svg)
# worked example (KBo 41.22), three draft layouts
(cd figures && for v in a b c; do lualatex -interaction=nonstopmode -halt-on-error case_$v.tex >/dev/null \
  && pdftocairo -png -r 300 -singlefile case_$v.pdf case_$v; done)
latexmk -lualatex -bibtex -interaction=nonstopmode -halt-on-error main.tex
# fail if any \Q{key} was undefined
if grep -q "Undefined number" main.log; then grep "Undefined number" main.log; exit 1; fi
