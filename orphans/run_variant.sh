#!/usr/bin/env bash
# Rerun the literature-tradition experiments on a damage-aware token table (qtm.variants).
#
#   bash run_variant.sh C [DATA_DIR]      # C = main (on the tablet + same-text support); B = diagnostic
#
# Needs DATA_DIR/tokens_marks.csv (python3 -m qtm.tlhdig, with sign marks). Version A is the token
# table as published so far (tokens.csv) and its results stay in results/tlhdig03_literature.
set -euo pipefail
cd "$(dirname "$0")"
V=${1:-C}
DATA=${2:-data}
O=results/tlhdig03_literature_$V
L=()
[ -f labels/cth701_labels.csv ] && L=(--labels701 labels/cth701_labels.csv)
mkdir -p "$O/case" "$O/tunnawiya"
TOK=$DATA/tokens_$V.csv
python3 -m qtm.variants "$DATA/tokens_marks.csv" "$TOK" --variant "$V" > "$O/variant.log"
python3 run_experiments.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 200 > "$O/run.log"   # E1-E6
python3 run_openset.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E9_run.log"                    # E9
python3 run_hypotheses.py "$TOK" --out "$O" > "$O/E10_run.log"                                          # E10
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
python3 run_test_examples.py "$TOK" --run "$O" --out "$C" >> "$C/run.log"
echo done
