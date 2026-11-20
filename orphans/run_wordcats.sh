#!/usr/bin/env bash
# Rerun only the word-category results of one filled version after a change to the word classes
# (qtm/wordclass.py, labels/gloss_lexicon.tsv, labels/sense_rules.csv): the fills, the version's token
# table, E7, E8, E11, the case studies that report word classes, and the figures. Placements (E1-E6,
# E9, E10, joins) do not use word classes and are left as they are.
# Usage: bash run_wordcats.sh DATA_DIR C|A   (expects DATA/tokens_marks.csv parsed with the current rules)
set -euo pipefail
cd "$(dirname "$0")"
DATA=${1:-data}
V=${2:-C}
TLH=${TLH:-04}
O=results/tlhdig${TLH}_literature_${V}_filled
python3 fill_lemmas.py "$DATA/tokens_marks.csv" "$DATA/tokens_marks_filled.csv" --ediana "$DATA/ediana_cluwian_forms.csv" > "$O/fill.log"
TOK=$DATA/tokens_F.csv
[ "$V" = C ] || TOK=$DATA/tokens_F$V.csv
python3 -m qtm.variants "$DATA/tokens_marks_filled.csv" "$TOK" --variant "$V" > "$O/variant.log"
L=()
[ -f labels/cth701_labels.csv ] && L=(--labels701 labels/cth701_labels.csv)
python3 run_attribution.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E11_run.log"              # E11
python3 run_profiles.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E7_run.log"   # E7
python3 run_wordclass.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E8_run.log"  # E8
python3 stats_corpus.py "$TOK" --out "$O" --groups literature
C=$O/case
python3 run_case.py "$TOK" --run "$O" --txtid "KBo 41.22" --out "$C" > "$C/run.log"
python3 run_case.py "$TOK" --run "$O" --txtid "EBo 133" --out "$C" >> "$C/run.log"
for T in "KBo 44.52" "DAAM 3.64" "KBo 52.43" "KBo 57.54"; do python3 run_case.py "$TOK" --run "$O" --txtid "$T" --out "$C" >> "$C/run.log"; done
python3 run_barcode.py "$TOK" --run "$O" --txtid "KBo 44.52" --out "$C" >> "$C/run.log"
echo done
