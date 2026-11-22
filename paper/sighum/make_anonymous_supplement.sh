#!/usr/bin/env bash
# Anonymous code-and-results package for double-blind review (upload as supplementary material).
# Copies the code, labels and the TLHdig 0.4 results, leaves out data, photos, slides and release
# scripts, and replaces names and project references. Usage: bash make_anonymous_supplement.sh OUTDIR
set -euo pipefail
cd "$(dirname "$0")/../.."
OUT=${1:-/tmp/anonymous_supplement}; S=$OUT/supplement
rm -rf "$S"; mkdir -p "$S/paper/figures" "$S/paper/data"
tar -cf - --exclude='orphans/data' --exclude='orphans/fotarch' --exclude='orphans/slides' \
  --exclude='orphans/release' --exclude='orphans/release_template' --exclude='orphans/results/tlhdig03*' \
  --exclude='__pycache__' --exclude='orphans/joinfit_*' --exclude='orphans/TALK_OUTLINE.md' orphans | tar -xf - -C "$S"
rm -f "$S"/orphans/{release_docs.py,make_release.py,talk_script_filled.py,make_case_slide.py,talk_numbers.py,slide_barcode.mjs}
cp paper/make_numbers.py paper/make_case_figures.py paper/*.csv "$S/paper/"; cp -r paper/generated "$S/paper/"
cp paper/figures/*.py "$S/paper/figures/"; cp paper/data/wordnet_audit_ShG.csv "$S/paper/data/wordnet_audit_expert.csv"
cp paper/sighum/anonymous_README.md "$S/orphans/README.md"
grep -rlIE "\bShG\b|measuring-scribal-literacy|Mainz Hittite|Mainz talk|talk.s|working sheet|sense\.rules\.shg|workshop playground|wordnet_audit_ShG" "$S" \
  | xargs -r sed -i -E "s/ShG's/the expert's/g; s/\bShG\b/expert/g; s/measuring-scribal-literacy/anonymous-submission/g; \
s/the Mainz Hittite (&|and) AI workshop( talk)?/an earlier presentation/g; s/Mainz Hittite (&|and) AI workshop/an earlier presentation/g; \
s/the Mainz talk/an earlier presentation/g; s/Mainz talk/earlier presentation/g; s/the talk.s/the/g; s/StBoT 73 working sheet/working sheet/g; \
s/sense\.rules\.shg/sense.rules.expert/g; s/the workshop playground/the interactive tool/g; s/wordnet_audit_ShG/wordnet_audit_expert/g"
if grep -rnIiE "shai|shygordin|shaigordin|ariel univ|digital pasts|text-orphans|adoptio" "$S" | grep -v konkordanz_literature; then
  echo "identifying string left"; exit 1; fi
(cd "$OUT" && rm -f anonymous_supplement.zip && zip -qr anonymous_supplement.zip supplement -x '*/__pycache__/*')
echo "wrote $OUT/anonymous_supplement.zip"
