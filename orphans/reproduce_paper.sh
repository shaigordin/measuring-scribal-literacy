#!/usr/bin/env bash
# Rebuild every number and table of the paper "Orphans and Archetypes: Quantitative Tradition Mapping
# for Fragmentary Hittite Texts" from the public TLHdig Beta 0.4 release.
#
#   pip install -r requirements.txt      # Python 3.13
#   bash reproduce_paper.sh [DATA_DIR]   # DATA_DIR (default ./data) receives TLHdig and the token tables
#
# Writes results/tlhdig04*/ and ../paper/generated/numbers.tex (every number of the paper, each with
# its source file and key in ../paper/generated/numbers_index.csv). Network access is needed for
# TLHdig (Zenodo, checksum-verified), eDiAna (Cuneiform Luwian lemmata, used to fill missing analyses),
# the Konkordanz pages behind the join checks (hethport.net) and the two WordNets (wn package).
# Runs single-threaded; the permutation tests (200 and 100 shuffles) take most of the time.
set -euo pipefail
cd "$(dirname "$0")"
DATA=${1:-data}
export TLH=04
REC=24373727; MD5=a31a1ac9808ac77432466a910ed85969
XML=$DATA/TLHbasisONLINE25_1_ZENODO_Beta_$TLH
ZIP=$XML.zip
OUT=results/tlhdig$TLH
L=(--labels701 labels/cth701_labels.csv)      # CTH 701 subgroups (Salvini-Wegner), Konkordanz snapshot
mkdir -p "$DATA" "$OUT"
log() { echo "[$(date +%H:%M:%S)] $*"; }

# 1. TLHdig Beta 0.4 from Zenodo, checksum-verified
if [ ! -d "$XML" ]; then
  [ -f "$ZIP" ] || curl -fsSL --retry 3 -o "$ZIP" "https://zenodo.org/api/records/$REC/files/TLHbasisONLINE25_1_ZENODO_Beta_$TLH.zip/content"
  echo "$MD5  $ZIP" | md5sum -c -
  unzip -oq "$ZIP" -d "$DATA"
fi

# 2. token table: one row per word, with word class, sign status (preserved, damaged, restored) and
#    writing layer; tokens.csv is version A (restorations counted, analyses as published)
log "parsing TLHdig"
python3 -m qtm.tlhdig "$XML" "$DATA/tokens_marks.csv" --wide-titles > "$DATA/parse.log" 2> "$DATA/parse.err"
python3 -m qtm.variants "$DATA/tokens_marks.csv" "$DATA/tokens.csv" --variant A > /dev/null

# 3. baseline: the traditions of StBoT 73 Table 3 plus CTH-range controls
log "baseline"
python3 run_experiments.py "$DATA/tokens.csv" "${L[@]}" --groups historical --out "$OUT" --perm 200 > "$OUT/run.log"

# 4. literature-defined traditions, without restorations and without filled analyses (for the
#    comparison with the filled table)
log "without restorations, unfilled"
O=${OUT}_literature_C; mkdir -p "$O"
python3 -m qtm.variants "$DATA/tokens_marks.csv" "$DATA/tokens_C.csv" --variant C > "$O/variant.log"
python3 run_experiments.py "$DATA/tokens_C.csv" "${L[@]}" --groups literature --out "$O" --perm 200 > "$O/run.log"
python3 run_hypotheses.py "$DATA/tokens_C.csv" --out "$O" > "$O/E10_run.log"
python3 run_spellings_only.py "$DATA/tokens_C.csv" --run "$O" > "$O/R1_run.log"
mkdir -p "$O/case"
for T in "KBo 44.52" "EBo 133" "KBo 41.22"; do     # the cases compare_filled.py compares
  python3 run_case.py "$DATA/tokens_C.csv" --run "$O" --txtid "$T" --out "$O/case" >> "$O/case/run.log"
done

# 5. main results: missing analyses filled (same spelling elsewhere in TLHdig, or the eDiAna lemma),
#    once without restorations (C, the main results) and once with them (A)
log "filling missing analyses"
python3 ediana_cluwian.py --cache "$DATA/ediana" --out "$DATA/ediana_cluwian_forms.csv" > "$DATA/ediana.log"
python3 fill_lemmas.py "$DATA/tokens_marks.csv" "$DATA/tokens_marks_filled.csv" --ediana "$DATA/ediana_cluwian_forms.csv" > "$DATA/fill.log"
for V in C A; do
  log "filled, version $V"
  O=${OUT}_literature_${V}_filled; TOK=$DATA/tokens_F.csv; [ "$V" = C ] || TOK=$DATA/tokens_F$V.csv
  mkdir -p "$O/case" "$O/known_joins" "$O/joins"
  python3 -m qtm.variants "$DATA/tokens_marks_filled.csv" "$TOK" --variant "$V" > "$O/variant.log"
  python3 run_experiments.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 200 > "$O/run.log"  # E1-E6
  python3 run_openset.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E9_run.log"                   # E9
  python3 run_hypotheses.py "$TOK" --out "$O" > "$O/E10_run.log"                                         # E10
  python3 run_attribution.py "$TOK" --report "$O/report.json" --out "$O" > "$O/E11_run.log"             # E11
  python3 run_profiles.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E7_run.log"  # E7
  python3 run_wordclass.py "$TOK" "${L[@]}" --groups literature --out "$O" --perm 100 > "$O/E8_run.log" # E8
  python3 run_spellings_only.py "$TOK" --run "$O" > "$O/R1_run.log"                                     # spellings only
  python3 stats_corpus.py "$TOK" --out "$O" --groups literature --run "$O"
  for T in "KBo 44.52" "KBo 57.54" "EBo 133" "KBo 41.22"; do                                            # worked examples
    python3 run_case.py "$TOK" --run "$O" --txtid "$T" --out "$O/case" >> "$O/case/run.log"
  done
  python3 run_known_joins.py "$TOK" --run "$O" --cache "$DATA/konkordanz" --out "$O/known_joins" \
    --labels "$O/known_joins/labels.csv" --fetch --pages-from labels/known_joins_pages.json > "$O/known_joins/run.log"
  python3 run_join_model.py "$TOK" --run "$O" --xml "$XML" --cache "$DATA/konkordanz" --fetch --k 200 \
    --out "$O/joins" > "$O/joins/run.log"
done
python3 compare_filled.py --main "${OUT}_literature_C" --filled "${OUT}_literature_C_filled" \
  --fill "$DATA/tokens_marks_filled.csv" > "${OUT}_literature_C_filled/comparison.txt"
python3 run_unicode.py "$DATA/tokens_F.csv" --xml "$XML" --run "${OUT}_literature_C_filled" > "${OUT}_literature_C_filled/U_run.log"
# every manuscript of Laroche's residual bins, placed by the main run (the supplementary dataset)
python3 make_release.py "$DATA/tokens_F.csv" --run "${OUT}_literature_C_filled" --out "$DATA/release_C" > "$DATA/release_C.log"
python3 summarise_bins.py "$DATA/release_C/fragments.csv" "${OUT}_literature_C_filled/bin_placements.json" > /dev/null

# 6. checks of the annotation layer: HFR conventions, meaning classes, WordNet, the audited sample
log "annotation checks"
python3 check_hfr_conventions.py "$XML" results/hfr_conventions.json > /dev/null
python3 check_gloss_wordnet.py --wn-data "$DATA/wn" --out results/wordnet_check > /dev/null   # before run_senses.py, which reads its gloss_wordnet.csv
python3 run_senses.py "$DATA/tokens_marks.csv" --out results/senses > /dev/null
python3 review_wordclass.py examples --tokens "$DATA/tokens.csv"
python3 review_wordclass.py score --tokens "$DATA/tokens.csv"     # the expert-marked audit sample
python3 review_wordclass.py rescore --tokens "$DATA/tokens.csv"

# 7. the paper's numbers, tables and worked-example data
log "paper numbers"
XMLABS=$(cd "$XML" && pwd)
(cd ../paper && python3 make_case_marks.py "$XMLABS/CTH 470_XML_TLH/KBo 44.52.xml" 470 \
  && python3 make_case_figures.py ../orphans/results/tlhdig04_literature_C_filled/case/case_KBo_44_52.json generated/case_data_c.tex \
  && python3 make_numbers.py)
log "done: ../paper/generated/numbers.tex"
