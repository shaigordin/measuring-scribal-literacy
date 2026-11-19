"""Colours for the Mainz deck slide "decide44": each word's background alpha from its share of
the decision (case_KBo_44_52.json word_shares). alpha = 0.3 + 0.6*sqrt(|s|/max|s|); none below |s| < 0.01;
red for positive (toward the nearest tradition), blue for negative; light text on red when alpha >= 0.6.
Usage: python3 slides/decide44_colours.py results/tlhdig03_literature_C_filled"""
import json, math, sys
from pathlib import Path
d = json.loads((Path(sys.argv[1]) / "case" / "case_KBo_44_52.json").read_text())
m = max(abs(w[3]) for w in d["word_shares"])
for lnr, tr, word, s in d["word_shares"]:
    if abs(s) < 0.01:
        bg, fg = "#00000000", "#2b1a10"
    else:
        a = 0.3 + 0.6 * math.sqrt(abs(s) / m)
        bg = ("#8a2c12" if s > 0 else "#1f4e8c") + f"{round(a * 255):02x}"
        fg = "#f7ebd3" if (s > 0 and a >= 0.6) else "#2b1a10"
    print(f"{lnr}\t{tr}\t{s:+.3f}\t{bg}\t{fg}")
