#!/usr/bin/env bash
# SIGHUM 2027 version: regenerate every number from ../../orphans/results, build main.pdf (ACL style,
# anonymous) and main.docx (a Word copy for review). Fails on any undefined number.
set -euo pipefail
cd "$(dirname "$0")"
(cd .. && python3 make_numbers.py && python3 make_case_figures.py)
latexmk -lualatex -bibtex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
if grep -q "Undefined number" main.log; then grep "Undefined number" main.log; exit 1; fi
python3 make_docx.py
