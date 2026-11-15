# Slides drawn from the data

The Mainz deck is a Claude Slides artifact edited by hand. These scripts write the slides whose
content is a chart, so that a rerun can redraw them from the results instead of by hand:

| Script | Slide | Source |
|---|---|---|
| `make_test1_slide.py` | Test 1: hide a manuscript (accuracy per tradition) | `report.json` E1, both datasets |
| `make_barcode_slide.py` | KBo 44.52 against ten archetypes | `case/barcode_KBo_44_52.json` |
| `make_scribal_slide.py` | Each tradition's scribal profile | `E7_report.json` E7b |
| `decide44_colours.py` | colours of "Which words decide" (written into the slide by hand) | `case/case_KBo_44_52.json` word_shares |

`caution41.html` and `clay.html` are the hand-written versions of those slides as published
(KBo 57.54, the restored Old Woman; the counting rules). Every number on every slide, with its
source file, is listed by `talk_numbers.py` in `results/talk_numbers.md`.
