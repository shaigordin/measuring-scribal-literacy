"""Estimated number of signs lost at the start of each line of a manuscript, from TLHdig's break widths.

TLHdig encodes a break at the start of a line as <space c="n"/> blanks before the first preserved word
(see run_joinfit.lead_gaps). That is a width in characters of transliteration, not a sign count. We turn
it into signs with the manuscript's own ratio of transliteration characters to signs (cu attribute of <lb>),
so the estimate follows the editor's spacing. Rough: shown as x's on slides, never as a measured count.

    python3 lead_breaks.py data/TLHbasisONLINE25_1_ZENODO_Beta_03 "KBo 44.52" results/tlhdig03_literature_C/case/lead_breaks_KBo_44_52.json
"""
import glob, json, os, re, sys


def lines(xml_dir, txt):
    p = glob.glob(os.path.join(xml_dir, "*", txt + ".xml")) + glob.glob(os.path.join(xml_dir, "*", "*", txt + ".xml"))
    s = open(p[0], encoding="utf-8").read()
    for m in re.finditer(r'<lb [^>]*lnr="([^"]+)"[^>]*cu="([^"]*)"[^>]*/>(.*?)(?=<lb |<gap t="line"|$)', s, re.S):
        lnr, cu, body = m.groups()
        words = re.findall(r"<w[^>]*>(.*?)</w>", body, re.S)
        lead = 0
        for w in words:  # blanks before the first written word, as in run_joinfit.lead_gaps
            sp = re.fullmatch(r'\s*<space c="(\d+)"/>\s*', w)
            if sp:
                lead += int(sp.group(1)); continue
            if re.fullmatch(r"\s*<del_(fin|in)/>\s*", w):
                continue
            break
        text = re.sub(r"\s+", " ", " ".join(re.sub(r"<[^>]+>", "", w) for w in words)).strip()
        yield lnr, lead, len(cu), text


def main(xml_dir, txt, out):
    L = list(lines(xml_dir, txt))
    ratio = sum(len(t) for *_, t in L) / sum(n for _, _, n, _ in L)
    rows = [{"line": l, "tlhdig_lead_space": g, "est_lost_signs": int(g / ratio + 0.5), "signs_written": n, "text": t}
            for l, g, n, t in L]
    res = {"txtid": txt, "chars_per_sign": round(ratio, 3), "lines": rows}
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:4])
