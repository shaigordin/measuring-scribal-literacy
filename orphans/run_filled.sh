#!/usr/bin/env bash
# Side check: version C with TLHdig's missing analyses filled (fill_lemmas.py: same spelling elsewhere in
# TLHdig, and eDiAna for Luwian words). Main results stay in results/tlhdig03_literature_C.
#
#   bash run_filled.sh [DATA_DIR]      # needs DATA_DIR/tokens_marks.csv (python3 -m qtm.tlhdig)
set -euo pipefail
cd "$(dirname "$0")"
DATA=${1:-data}
O=results/tlhdig03_literature_C_filled
mkdir -p "$O/case"
python3 ediana_cluwian.py --cache "$DATA/ediana" --out "$DATA/ediana_cluwian_forms.csv" > "$O/ediana.log"
python3 fill_lemmas.py "$DATA/tokens_marks.csv" "$DATA/tokens_marks_filled.csv" --ediana "$DATA/ediana_cluwian_forms.csv" > "$O/fill.log"
TOK=$DATA/tokens_F.csv
python3 -m qtm.variants "$DATA/tokens_marks_filled.csv" "$TOK" --variant C > "$O/variant.log"
L=()
[ -f labels/cth701_labels.csv ] && L=(--labels701 labels/cth701_labels.csv)
python3 run_experiments.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 200 > "$O/run.log"   # E1-E6
python3 run_hypotheses.py "$TOK" --out "$O" > "$O/E10_run.log"                                          # E10
python3 run_spellings_only.py "$TOK" --run "$O" > "$O/R1_run.log"                                      # R1
for T in "KBo 44.52" "EBo 133" "KBo 41.22"; do python3 run_case.py "$TOK" --run "$O" --txtid "$T" --out "$O/case" >> "$O/case/run.log"; done
python3 compare_filled.py --main results/tlhdig03_literature_C --filled "$O" --fill "$DATA/tokens_marks_filled.csv" > "$O/comparison.txt"
echo done
