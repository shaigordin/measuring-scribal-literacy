#!/usr/bin/env bash
# SIGHUM 2027 version: regenerate every number from ../../orphans/results, build main.pdf (ACL style,
# anonymous) and main.docx (a Word copy for review). Fails on any undefined number.
set -euo pipefail
cd "$(dirname "$0")"
# figures/data/marks_KBo_44_52.csv (writing layers, for italics) comes from make_case_marks.py and the TLHdig XML
(cd .. && python3 make_numbers.py && python3 make_case_figures.py \
  && python3 make_case_figures.py ../orphans/results/tlhdig03_literature_C/case/case_KBo_44_52.json generated/case_data_c.tex)
(cd ../figures && lualatex -interaction=nonstopmode -halt-on-error case_sighum.tex >/dev/null \
  && pdftocairo -png -r 600 -singlefile case_sighum.pdf case_sighum)
latexmk -lualatex -bibtex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
if grep -q "Undefined number" main.log; then grep "Undefined number" main.log; exit 1; fi
python3 make_docx.py
