"""Estimated number of signs lost at the start of each line of a manuscript, from TLHdig's break widths.

TLHdig encodes a break at the start of a line as <space c="n"/> blanks before the first preserved word
(see run_joinfit.lead_gaps). That is a width in characters of transliteration, not a sign count. We turn
it into signs with the manuscript's own ratio of transliteration characters to signs (cu attribute of <lb>),
so the estimate follows the editor's spacing. Rough: shown as x's on slides, never as a measured count.

    python3 lead_breaks.py data/TLHbasisONLINE25_1_ZENODO_Beta_03 "KBo 44.52" results/tlhdig03_literature_C/case/lead_breaks_KBo_44_52.json \
        fotarch/KBo_44_52_line_starts.csv 50

Optional photo check (last two arguments): the x position (px) of the first visible sign of each line, read by eye
on the Mainzer Fotoarchiv photo N06460 as used on the deck (1170 px wide; the 1 cm scale squares are ~140 px), and
the sign width in px (~50: lines 6', 7', 11' have 16-18 signs over ~850 px). The photo gives each line's start
relative to the others, in signs; it cannot show how much is lost before the leftmost preserved sign. That offset is
taken from TLHdig: the median of (TLHdig estimate - photo offset) over the lines, so restored first words count as in
the TLHdig estimate.
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


def photo_check(rows, csv_path, px_per_sign):
    import csv, statistics
    xs = {r["line"]: float(r["first_sign_x_px"]) for r in csv.DictReader(open(csv_path, encoding="utf-8"))}
    x0 = min(xs.values())
    for r in rows:
        if r["line"] in xs:
            r["photo_x_px"] = xs[r["line"]]
            r["photo_offset_signs"] = round((xs[r["line"]] - x0) / px_per_sign, 2)
    off = statistics.median(r["est_lost_signs"] - r["photo_offset_signs"] for r in rows if "photo_offset_signs" in r)
    for r in rows:
        if "photo_offset_signs" in r:
            r["est_lost_signs_photo"] = int(off + r["photo_offset_signs"] + 0.5)
    return {"px_per_sign": px_per_sign, "lost_before_leftmost_line": round(off, 2)}


def main(xml_dir, txt, out, photo_csv=None, px_per_sign=None):
    L = list(lines(xml_dir, txt))
    ratio = sum(len(t) for *_, t in L) / sum(n for _, _, n, _ in L)
    rows = [{"line": l, "tlhdig_lead_space": g, "est_lost_signs": int(g / ratio + 0.5), "signs_written": n, "text": t}
            for l, g, n, t in L]
    res = {"txtid": txt, "chars_per_sign": round(ratio, 3), "lines": rows}
    if photo_csv:
        res["photo"] = photo_check(rows, photo_csv, float(px_per_sign))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:6])
