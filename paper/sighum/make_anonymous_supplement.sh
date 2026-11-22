#!/usr/bin/env bash
# Anonymous code-and-results package for double-blind review (upload as supplementary material).
# Copies only what the paper needs (a list, not the whole repository): the code that
# orphans/reproduce_paper.sh runs, its hand-made inputs, the result files make_numbers.py reads, and
# the paper's generated numbers and tables. Then removes names and project references and fails if
# anything identifying is left. Usage: bash make_anonymous_supplement.sh OUTDIR
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=${1:-/tmp/anonymous_supplement}; S=$OUT/supplement
rm -rf "$S"; mkdir -p "$S"

O=orphans
CODE="reproduce_paper.sh requirements.txt qtm/__init__.py qtm/assign.py qtm/corpus.py qtm/features.py qtm/groups.py
  qtm/konkordanz.py qtm/layers.py qtm/pieces.py qtm/senses.py qtm/tlhdig.py qtm/variants.py qtm/wordclass.py
  tests/test_tlhdig_brackets.py
  run_experiments.py run_hypotheses.py run_openset.py run_attribution.py run_profiles.py run_wordclass.py
  run_spellings_only.py stats_corpus.py run_case.py run_known_joins.py run_join_model.py run_join_candidates.py
  run_unicode.py ediana_cluwian.py fill_lemmas.py compare_filled.py check_hfr_conventions.py run_senses.py
  check_gloss_wordnet.py review_wordclass.py"
LABELS="cth701_labels.csv cth701_labels.source.txt konkordanz_meta.csv konkordanz_meta.source.txt
  konkordanz_joins_duplicates.csv known_joins_pages.json gloss_lexicon.tsv sense_rules.csv title_pairs.csv
  word_fixes.csv wordclass_corrections.csv wordclass_audit.csv"
# results the paper reads (make_numbers.py), shipped so a rerun can be compared with them
R=results; M=$R/tlhdig04_literature_C_filled; A=$R/tlhdig04_literature_A_filled; U=$R/tlhdig04_literature_C
RUN="report.json E7_report.json E8_report.json E9_report.json E10_report.json E11_report.json R1_spellings_only.json
  corpus_stats.json stats_historical.csv E2_coverage_curve.csv E2_coverage_raw.csv E3_701_unclassified_nearest.csv
  E5_orphan_placement.csv E7_distinctive_features.csv E10a_leave_composition_out.csv E10c_signatures_in_contested.csv
  case/case_KBo_44_52.json case/case_KBo_57_54.json joins/J1_report.json known_joins/known_joins.json"
RESULTS="$R/tlhdig04/report.json $U/E10_report.json $U/E10c_signatures_in_contested.csv $U/stats_historical.csv
  $M/comparison.json $M/U_unicode.json $R/hfr_conventions.json $R/senses/senses.json $R/wordnet_check/wordnet_check.json
  $R/wordclass_audit_scores.json $R/wordclass_confidence.json $R/wordclass_examples.csv $R/wordclass_rule_changes.csv
  $R/wordclass_rule_changes_akk_logograms.csv $R/wordclass_rule_changes_hfr.csv $R/wordclass_rule_changes_audit.csv"
for f in $RUN; do RESULTS="$RESULTS $M/$f $A/$f"; done
P=paper
PAPER="make_numbers.py make_case_figures.py make_case_marks.py traditions.csv figures/make_archive_map.py
  figures/make_fragment_translit.py figures/data/marks_KBo_44_52.csv generated/numbers.tex generated/numbers_index.csv
  generated/case_data_c.tex generated/fragment_size.dat generated/archive_counts.csv generated/archive_map_G.tex
  generated/kbo24_8_translit.tex generated/kbo24_8_translit_a.tex generated/kbo24_8_translit_b.tex"
PAPER="$PAPER $(cd $P && ls generated/tab_*.tex)"

copy() { mkdir -p "$(dirname "$2")"; cp "$1" "$2"; }
for f in $CODE; do copy "$O/$f" "$S/$O/$f"; done
for f in $LABELS; do copy "$O/labels/$f" "$S/$O/labels/$f"; done
for f in $RESULTS; do copy "$O/$f" "$S/$O/$f"; done
for f in $PAPER; do copy "$P/$f" "$S/$P/$f"; done
copy "$P/data/wordnet_audit_ShG.csv" "$S/$P/data/wordnet_audit_expert.csv"
copy "$P/sighum/anonymous_README.md" "$S/README.md"
printf '__pycache__/\ndata/\n' > "$S/$O/.gitignore"
# the released dataset (every manuscript of the residual bins, placed by the main and comparison runs),
# from the release zip that orphans/make_release.py and release_docs.py write; its README is not copied
# (it names the author), the supplement README describes the files instead
RELEASE_ZIP=${RELEASE_ZIP:-/mnt/project-files/zenodo-release/orphans_archetypes_nearest_manuscripts_v2.1.0.zip}
TMPR=$(mktemp -d); unzip -q "$RELEASE_ZIP" -d "$TMPR"
for v in without_restorations with_restorations; do
  mkdir -p "$S/dataset/$v"
  for f in fragments.csv compositions.csv traditions.csv summary.json; do cp "$TMPR"/*/"$v/$f" "$S/dataset/$v/"; done
done
rm -r "$TMPR"

# names and project references in comments and docstrings
grep -rlIE "Mainz Hittite|quoted on the slides|ShG|measuring-scribal-literacy|Mainz (Hittite|talk|deck)|talk|deck|slide|playground|thread|working sheet|sense\.rules\.shg" "$S" \
  | xargs -r sed -i -E "s/ShG's/the expert's/g; s/\bShG\b/expert/g; s/wordnet_audit_ShG/wordnet_audit_expert/g; \
s/sense\.rules\.shg/sense.rules.expert/g; s/measuring-scribal-literacy/anonymous-submission/g; \
s/ ?\((paper thread('s)? suggestion|suggested in review), asked by expert\)//g; s/ \(deck slide( \"barcode\")?\)//g; \
s/[Tt]he (playground|workshop playground)('s)?/the interactive tool\2/g; \
s/ for the Mainz Hittite (&|and) AI workshop//g; s/quoted on the slides/quoted in the paper/g; s/StBoT 73 working sheet/working sheet/g"
grep -rlI "Syro-Mesopotamia\b" "$S" | xargs -r sed -i -E "s/Syro-Mesopotamia([^n]|$)/Syro-Mesopotamian\1/g"
LEAK="shai|gordin|shygordin|ariel|digital pasts|text-orphans|adoptio|mainz (hittite|talk|deck|workshop)|\bShG\b|\
playground|\bdeck\b|\bslides?\b|talk_numbers|\bthread\b|claude\.ai|session_|cmsg_|/home/|/mnt/"
if grep -rnIiE "$LEAK" "$S" | grep -vE "Gordin,? (Yavasan|et al)"; then
  echo "identifying string left"; exit 1; fi   # citations of published work (Gordin, Yavasan & Romach 2025) stay
# spreadsheets and documents carry their author in their metadata: none may be in the package
if find "$S" -name '*.xlsx' -o -name '*.docx' -o -name '*.pdf' -o -name '*.png' | grep .; then echo "binary file left"; exit 1; fi
(cd "$OUT" && rm -f anonymous_supplement.zip && TZ=UTC zip -qrX anonymous_supplement.zip supplement)
echo "wrote $OUT/anonymous_supplement.zip ($(du -h "$OUT/anonymous_supplement.zip" | cut -f1))"
