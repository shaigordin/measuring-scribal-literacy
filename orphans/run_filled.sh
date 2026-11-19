#!/usr/bin/env bash
# Main results: TLHdig's missing word analyses filled (fill_lemmas.py: same spelling elsewhere in
# TLHdig, and eDiAna for Cuneiform Luwian words), then every experiment, case study and join check.
#
#   bash run_filled.sh [DATA_DIR] [VARIANT]   # needs DATA_DIR/tokens_marks.csv (python3 -m qtm.tlhdig)
#
# VARIANT C (default): without restorations (results/tlhdig$TLH_literature_C_filled);
# VARIANT A: with the editors' restorations (results/tlhdig$TLH_literature_A_filled).
set -euo pipefail
cd "$(dirname "$0")"
DATA=${1:-data}
V=${2:-C}
TLH=${TLH:-04}
O=results/tlhdig${TLH}_literature_${V}_filled
mkdir -p "$O/case"
python3 ediana_cluwian.py --cache "$DATA/ediana" --out "$DATA/ediana_cluwian_forms.csv" > "$O/ediana.log"
python3 fill_lemmas.py "$DATA/tokens_marks.csv" "$DATA/tokens_marks_filled.csv" --ediana "$DATA/ediana_cluwian_forms.csv" > "$O/fill.log"
TOK=$DATA/tokens_F.csv
[ "$V" = C ] || TOK=$DATA/tokens_F$V.csv
python3 -m qtm.variants "$DATA/tokens_marks_filled.csv" "$TOK" --variant "$V" > "$O/variant.log"
L=()
[ -f labels/cth701_labels.csv ] && L=(--labels701 labels/cth701_labels.csv)
python3 run_experiments.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 200 > "$O/run.log"   # E1-E6
python3 run_openset.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E9_run.log"                    # E9
python3 run_hypotheses.py "$TOK" --out "$O" > "$O/E10_run.log"                                          # E10
mkdir -p "$O/tunnawiya"
python3 run_hypotheses.py "$TOK" --cths 409 --claim "Luwian rituals (Puriyanni, Kuwattalla)" --out "$O/tunnawiya" > "$O/tunnawiya/E10_run.log"
python3 run_attribution.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E11_run.log"              # E11
python3 run_profiles.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E7_run.log"   # E7
python3 run_wordclass.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E8_run.log"  # E8
python3 run_spellings_only.py "$TOK" --run "$O" > "$O/R1_run.log"                                      # R1
python3 stats_corpus.py "$TOK" --out "$O" --groups literature
C=$O/case
python3 run_case.py "$TOK" --run "$O" --txtid "KBo 41.22" --out "$C" > "$C/run.log"
python3 run_case.py "$TOK" --run "$O" --txtid "EBo 133" --out "$C" >> "$C/run.log"
python3 run_trail.py "$TOK" --run "$O" --out "$C" >> "$C/run.log"
python3 run_word_spread.py "$TOK" --word takarmun --exclude "EBo 133" --out "$C/spread_takarmun.json" >> "$C/run.log"
python3 run_join_candidates.py "$TOK" --run "$O" --txtid "EBo 133" --out "$C" >> "$C/run.log"
python3 run_size_example.py "$TOK" --run "$O" --txtid "KUB 29.4+" --starts 0 200 400 --out "$C" >> "$C/run.log"
for T in "KBo 61.39" "KUB 35.146" "EBo 133"; do
  python3 run_unplaced_example.py "$TOK" --run "$O" --txtid "$T" --out "$C" >> "$C/run.log"
done
for T in "KBo 44.52" "DAAM 3.64" "KBo 52.43" "KBo 57.54"; do python3 run_case.py "$TOK" --run "$O" --txtid "$T" --out "$C" >> "$C/run.log"; done
python3 run_test_examples.py "$TOK" --run "$O" --out "$C" >> "$C/run.log"
python3 run_barcode.py "$TOK" --run "$O" --txtid "KBo 44.52" --out "$C" >> "$C/run.log"
mkdir -p "$O/known_joins" "$O/joins"
python3 run_known_joins.py "$TOK" --run "$O" --cache "$DATA/konkordanz" --out "$O/known_joins" --labels "$O/known_joins/labels.csv" \
  --pages-from results/tlhdig03_literature/known_joins/known_joins.json > "$O/known_joins/run.log"
python3 run_join_model.py "$TOK" --run "$O" --xml "$DATA/TLHbasisONLINE25_1_ZENODO_Beta_$TLH" --cache "$DATA/konkordanz" \
  --fetch --k 200 --out "$O/joins" > "$O/joins/run.log"
[ "$V" = C ] && python3 compare_filled.py --main results/tlhdig${TLH}_literature_C --filled "$O" --fill "$DATA/tokens_marks_filled.csv" > "$O/comparison.txt"
echo done
