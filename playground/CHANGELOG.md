# Changelog

## 0.4.1 (2026-10-17)

- Rebuilt on the corrected word-class annotation (prepositions split from their nouns): 847 of
  2,026 orphans assigned, margin 0.018.
- Word tags show the class confidence; low-confidence classes have a dashed tag.
- The E11 numbers on the page come from the experiment report instead of the page text.

## 0.4.0 (2026-10-17)

- New opening page, Browse by CTH: every TLHdig text in its original CTH bin against the
  model's classification, with headline tiles for the orphan pools and links to TLHdig and the
  Konkordanz.
- Place a fragment loads any TLHdig text by siglum or by a TLHdig or Konkordanz link, and links
  back to both.
- Code split into modules (`js/`, `css/`, `build/`), with a version number, this changelog and
  a consistency check (`tests/check.mjs`).

## 0.3.0 (2026-10-17)

- What the score rests on: word classes and layers, by default for the decision margin, with a
  warning when a placement rests mostly on features common to all traditions.

## 0.2.0 (2026-10-17)

- Ten literature-defined traditions, the E9 open-set check, the similarity rose and the word
  butterfly.

## 0.1.0 (2026-10-16)

- First version: place a fragment, tradition wheel, archetype barcode, word-by-word comparison.
