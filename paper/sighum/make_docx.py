"""Word copy of the SIGHUM draft, for review and markup (the PDF from main.tex is the paper).

Expands the generated-number macros (\\Q, \\C, \\gentab) into plain text, then converts with pandoc,
citations resolved from ../references.bib. Usage: python3 make_docx.py  -> main.docx
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "..", "generated")


def macros(path, cmd):
    vals = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\\" + cmd + r"\{([^}]*)\}\{(.*)\}\s*$", line)
        if m:
            vals[m.group(1)] = m.group(2)
    return vals


Q = macros(os.path.join(GEN, "numbers.tex"), "qtmdef")
C = {}
for line in open(os.path.join(GEN, "case_data.tex"), encoding="utf-8"):
    m = re.match(r"\\expandafter\\def\\csname case@([^\\]*)\\endcsname\{(.*)\}\s*$", line)
    if m:
        C[m.group(1)] = m.group(2)

src = open(os.path.join(HERE, "main.tex"), encoding="utf-8").read()
body = src[src.index("\\title"):]          # drop the preamble (macro definitions, packages)
body = re.sub(r"\\Q\{([^}]*)\}", lambda m: Q.get(m.group(1), f"[{m.group(1)}?]"), body)
body = re.sub(r"\\C\{([^}]*)\}", lambda m: C.get(m.group(1), f"[{m.group(1)}?]"), body)
body = re.sub(r"\\gentab\{([^}]*)\}",
              lambda m: "\n".join(l for l in open(os.path.join(GEN, f"tab_{m.group(1)}.tex"), encoding="utf-8")
                                  if not l.startswith("%")), body)
body = re.sub(r"\\CTH\{([^}]*)\}", r"CTH \1", body)


def plain_tabular(text):
    """Replace each tabular column spec (pandoc misreads >{...}p{...}) by plain l columns."""
    out, i = [], 0
    while True:
        j = text.find("\\begin{tabular}{", i)
        if j < 0:
            return "".join(out) + text[i:]
        k, depth = j + len("\\begin{tabular}{"), 1
        start = k
        while depth:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        spec = text[start:k - 1]
        ncol = len(re.findall(r"[lrcpX]", re.sub(r"\{[^{}]*\}|[@>|<!*]|\s", "", spec)))
        out.append(text[i:j] + "\\begin{tabular}{" + "l" * max(ncol, 1) + "}")
        i = k


body = plain_tabular(body)
body = re.sub(r"\\todraft\{", r"\\emph{", body)
body = body.replace("\\bibliography{../references}", "")
# Word cannot show PDF figures: use the PNG rendered next to each figure PDF.
body = re.sub(r"\\includegraphics(\[[^]]*\])?\{([^}]+)\.pdf\}",
              lambda m: "\\includegraphics" + (m.group(1) or "") + "{../figures/" + m.group(2) + ".png}", body)
tex = "\\documentclass{article}\n\\usepackage{booktabs}\n" + body
tmp = os.path.join(HERE, "_docx_source.tex")
open(tmp, "w", encoding="utf-8").write(tex)
subprocess.run(["pandoc", tmp, "--metadata", "title=" + re.search(r"\\title\{(.*?)\}\n", src, re.S).group(1).replace("\\\\", ""), "-o", os.path.join(HERE, "main.docx"), "--citeproc",
                "--bibliography", os.path.join(HERE, "..", "references.bib"), "--number-sections"],
               check=True, cwd=HERE)
os.remove(tmp)
print("wrote main.docx")
