#!/usr/bin/env bash
# Rebuild every number, table and figure of the Mainz talk from the public TLHdig release.
#
#   bash reproduce.sh [DATA_DIR]
#
# DATA_DIR (default ./data) receives the TLHdig zip and the parsed token table.
# The CTH 701 subgroup labels (Salvini-Wegner a-f, script date) are read from
# $LABELS701 (default labels/cth701_labels.csv). Without them E3, E7c and the
# CTH 701 part of E8 are skipped.
# Needs Python 3.13 with requirements.txt, and Quarto 1.6 for the slides.
set -euo pipefail
cd "$(dirname "$0")"
DATA=${1:-data}
OUT=results/tlhdig03
LABELS701=${LABELS701:-labels/cth701_labels.csv}
ZIP=$DATA/TLHbasisONLINE25_1_ZENODO_Beta_03.zip
URL=https://zenodo.org/api/records/20328284/files/TLHbasisONLINE25_1_ZENODO_Beta_03.zip/content
MD5=f9acbc8db3111cc7dd88d82f7819a912
mkdir -p "$DATA" "$OUT"

# 1. data: TLHdig Beta 0.3 (doi:10.5281/zenodo.20328284), checksum-verified
[ -f "$ZIP" ] || curl -L -o "$ZIP" "$URL"
echo "$MD5  $ZIP" | md5sum -c -
[ -d "$DATA/TLHbasisONLINE25_1_ZENODO_Beta_03" ] || unzip -q "$ZIP" -d "$DATA"

# 2. token table (one row per word, with word classes)
python3 -m qtm.tlhdig "$DATA/TLHbasisONLINE25_1_ZENODO_Beta_03" "$DATA/tokens.csv" > "$DATA/parse.log" 2> "$DATA/parse.err"
TOK=$DATA/tokens.csv

L=()
if [ -f "$LABELS701" ]; then L=(--labels701 "$LABELS701"); else echo "no CTH 701 labels: skipping the subgroup tests"; fi

# 3. experiments
python3 run_experiments.py "$TOK" "${L[@]}" --out "$OUT" --perm 200 > "$OUT/run.log"   # E1-E6
python3 run_profiles.py   "$TOK" "${L[@]}" --out "$OUT" --perm 100 > "$OUT/E7_run.log" # E7
python3 run_wordclass.py  "$TOK" "${L[@]}" --out "$OUT" --perm 100 > "$OUT/E8_run.log" # E8
python3 stats_corpus.py   "$TOK" --out "$OUT"                                          # slide numbers

# 4. figures and slides
python3 make_figures.py "$OUT" ../img/orphans
python3 make_profile_figures.py "$OUT" ../img/orphans
(cd .. && quarto render orphans_archetypes.qmd)
