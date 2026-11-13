"""Slide snippets for a worked example (run_case.py output): the fragment's text as it is read
(`*_text.md`) and the same text with every word shaded by its share of the decision (`*_decision.md`).

Usage: python make_case_slide.py results/<run>/case/case_KBo_41_22.json
"""
import html
import json
import sys
from pathlib import Path

SHADE = "235, 104, 52"  # palette slot 2 (orange), as rgb for an alpha ramp
MIN_SHARE = 0.02


def render(case, shaded):
    rows, cur, line = [], None, []
    for lnr, tl, word, share in case["word_shares"]:
        if lnr != cur and line:
            rows.append((cur, line))
            line = []
        cur = lnr
        t = html.escape(str(tl))
        if shaded and share >= MIN_SHARE:
            a = min(0.15 + share * 3, 0.95)
            t = (f'<span style="background: rgba({SHADE}, {a:.2f}); border-radius: 4px; padding: 0 3px;" '
                 f'title="{share:.0%} of the decision">{t}</span>')
        line.append(t)
    if line:
        rows.append((cur, line))
    out = ['<div class="fragment-text" style="font-family: var(--r-code-font, monospace); font-size: 0.62em; line-height: 1.45;">']
    for lnr, ws in rows:
        out.append(f'<div><span style="color: #8a8984; display: inline-block; min-width: 5.5em;">{html.escape(str(lnr))}</span>'
                   + " ".join(ws) + "</div>")
    out.append("</div>")
    return "```{=html}\n" + "\n".join(out) + "\n```\n"


def main():
    path = Path(sys.argv[1])
    case = json.loads(path.read_text())
    stem = path.with_suffix("")
    Path(f"{stem}_text.md").write_text(render(case, False))
    Path(f"{stem}_decision.md").write_text(render(case, True))
    print("wrote", f"{stem}_text.md", f"{stem}_decision.md")


if __name__ == "__main__":
    main()
