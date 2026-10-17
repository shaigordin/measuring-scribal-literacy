#!/usr/bin/env bash
# Build the paper: regenerate every number and table from ../orphans/results, then typeset.
#   bash build.sh
# Needs Python 3 (standard library only) and TeX Live with lualatex, bibtex and the Libertinus fonts.
set -euo pipefail
cd "$(dirname "$0")"
python3 make_numbers.py
latexmk -lualatex -bibtex -interaction=nonstopmode -halt-on-error main.tex
# fail if any \Q{key} was undefined
if grep -q "Undefined number" main.log; then grep "Undefined number" main.log; exit 1; fi
