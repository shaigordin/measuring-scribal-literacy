"""Physical fit check for a proposed join from two photographs (EBo 133 + KBo 44.140).

A visual aid for the philologist, not evidence of a join. Pipeline:
  1. scale: read the cm ruler in each photo (alternating black/white 1 cm blocks)
  2. cut-out: separate fragment from background (threshold, morphology, largest component)
  3. deskew (optional, off for these two photos: their lines are already horizontal and the
     angle search is biased by the rotated borders of the cut-out)
  4. line spacing: row profile of vertical gradient energy in the text band, spectrum peak
     between 0.3 and 0.9 cm; where the profile is too irregular (old print of KBo 44.140),
     use the distance between two paragraph rulings (located by eye, refined by the code)
     divided by the number of lines between them (counted by eye; both counts reported)
  5. placement: both at the same scale; the second fragment's right boundary aligned with
     the first's (hypothetical common right edge); moved up until the cut-outs touch
  6. figure: true-scale fit with line-spacing markers, ruling markers, the hypothetical edge,
     and the transliterations beside the photo, formula by formula

Usage: python run_joinfit.py joinfit_EBo133_KBo44140.json
Photos are not in the repository (copyright); put them where the config says (data/photos/).
"""
import json
import re, sys, csv, os
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))


def ruler_px_per_cm(gray, x0, x1, y0=0, y1=None):
    """Mean length in px of the alternating 1 cm blocks of the ruler strip x0..x1."""
    col = gray[y0:y1, x0:x1].mean(1)
    b = (col > 128).astype(int)
    ch = np.flatnonzero(np.diff(b))
    d = np.diff(ch)
    big = d[d > 0.5 * np.median(d[d > np.percentile(d, 50)])]  # drop the fine mm ticks
    return float(np.median(big)), [int(v) for v in big]


def cutout(img, box, dark_bg, thr):
    im = img.crop(box)
    a = np.asarray(im.convert("RGB")).astype(float)
    if dark_bg:
        m = a.max(2) > thr
    else:  # light background: flood from the borders
        bg = a.mean(2) > thr
        lab, _ = ndimage.label(bg)
        border = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
        m = ~np.isin(lab, list(border))
    m = ndimage.binary_closing(ndimage.binary_opening(m, iterations=3), iterations=12)
    lab, _ = ndimage.label(m)
    m = ndimage.binary_fill_holes(lab == np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    return im, m


def row_profile(gray, pxcm):
    gy = np.abs(ndimage.sobel(ndimage.gaussian_filter(gray, 0.03 * pxcm), axis=0))
    p = gy.mean(1)
    return p - ndimage.gaussian_filter1d(p, 1.2 * pxcm)


def spectrum_pitch(p, pxcm, lo=0.3, hi=0.9):
    p = p * np.hanning(len(p))
    n = 1 << 15
    F = np.abs(np.fft.rfft(p, n)); f = np.fft.rfftfreq(n)
    per = 1 / np.maximum(f, 1e-9)
    ok = (per > lo * pxcm) & (per < hi * pxcm)
    i = int(np.argmax(F * ok)); P = per[i]
    y = np.arange(len(p))
    ph = np.arctan2(np.sum(p * np.sin(2 * np.pi * y / P)), np.sum(p * np.cos(2 * np.pi * y / P)))
    return P, (ph / (2 * np.pi)) * P % P, float(F[i] / (F * ok).sum())


def deskew(gray, band, pxcm, angles=np.arange(-6, 6.01, 0.5)):
    x0, y0, x1, y1 = band
    best = (0, -1)
    for a in angles:
        g = ndimage.rotate(gray, a, reshape=False, order=1, mode="nearest")[y0:y1, x0:x1]
        _, _, sharp = spectrum_pitch(row_profile(g, pxcm), pxcm)
        if sharp > best[1]:
            best = (float(a), sharp)
    return best[0]


def rulings(gray, band, pxcm, approx):
    """Rows of the n strongest paragraph rulings inside band.

    A ruling is a long horizontal groove: a light edge followed a few px lower by a dark
    edge (or the reverse, depending on the light), continuous across much of the column.
    Score per row = min(light-edge strength, dark-edge strength k px lower), each the
    median over the row of a 1.5 cm horizontal running mean.
    """
    x0, y0, x1, y1 = band
    gy = ndimage.sobel(ndimage.gaussian_filter(gray[y0:y1, x0:x1], 1.0), axis=0)
    run = int(1.5 * pxcm)
    P = np.median(ndimage.uniform_filter1d(np.clip(gy, 0, None), run, axis=1), axis=1)
    N = np.median(ndimage.uniform_filter1d(np.clip(-gy, 0, None), run, axis=1), axis=1)
    sc = np.zeros(len(P))
    for a, b in ((P, N), (N, P)):
        for k in range(2, max(3, int(0.12 * pxcm))):
            sc[:-k] = np.maximum(sc[:-k], np.minimum(a[:-k], b[k:]))
    sc = sc - ndimage.gaussian_filter1d(sc, 0.6 * pxcm)
    # rulings are located by eye (approx rows, in the config) and refined here to the
    # best-scoring row within +-0.3 cm; the free search also picks up sign rows on this print
    w = int(0.3 * pxcm)
    rows = []
    for a in approx:
        lo, hi = max(0, a - y0 - w), min(len(sc), a - y0 + w)
        rows.append(int(lo + np.argmax(sc[lo:hi])) + y0)
    return rows


def lines_of(tok_csv, txt, sides):
    L = defaultdict(list)
    for r in csv.DictReader(open(tok_csv)):
        if r["txtid"] == txt and any(r["lnr"].startswith(s) for s in sides):
            L[r["lnr"]].append(r["translit"])
    return [(k, " ".join(v)) for k, v in L.items()]


_PIECES = re.compile(r"([-.\s+˽]+)")


def rich_word(translit, status, layer):
    """Segments (text, kind) of one word with TLHdig's break marks restored from the per-sign status
    (P preserved, D damaged, R restored, L lost, O omitted) and layer (H Hittite, A Akkadogram,
    S Sumerogram, d determinative). kind: 'i' italic (Hittite, Akkadogram), 'u' upright, 'b' bracket,
    'r' restored text (upright or italic follows as 'ri'/'ru')."""
    m0 = re.match(r"^([-.\s+˽]*)(.*?)([-.\s+˽]*)$", translit)
    lead, translit, trail = m0.group(1), m0.group(2), m0.group(3)
    units, seps = [], []
    for k, piece in enumerate(_PIECES.split(translit)):
        if k % 2:
            seps.append(piece); continue
        # a piece may hold determinatives: {NINDA}ta -> {NINDA}, ta
        for m in re.finditer(r"\{[^}]*\}|[^{}]+", piece):
            if units and len(units) > len(seps):
                seps.append("")
            units.append(m.group(0))
    if len(seps) < len(units):
        seps.append("")
    out, i, open_ = [], 0, None
    counted = lambda u: not (u.strip("{}") in ("x", "") or u.strip("{}").isdigit())
    st = [None] * len(units)
    for j, u in enumerate(units):
        if counted(u) and i < len(status):
            st[j] = (status[i], layer[i] if i < len(layer) else "H"); i += 1
    for j, u in enumerate(units):
        s, l = st[j] if st[j] else ("P", "S" if u.isupper() or u.isdigit() else "H")
        mark = "[" if s in "RL" else ("⸢" if s == "D" else ("<" if s == "O" else None))
        if mark != open_:
            if open_:
                out.append(({"[": "]", "⸢": "⸣", "<": ">"}[open_], "b"))
            if mark:
                out.append((mark, "b"))
            open_ = mark
        kind = "i" if l in "HA" and u.strip("{}") != "x" else "u"
        out.append((u, ("r" + kind) if s in "RL" else kind))
        if seps[j]:
            # a separator inside a bracket run stays inside; one after the run's end goes outside
            nxt = st[j + 1] if j + 1 < len(units) and st[j + 1] else ("P", "")
            nmark = "[" if nxt[0] in "RL" else ("⸢" if nxt[0] == "D" else ("<" if nxt[0] == "O" else None))
            if open_ and nmark != open_:
                out.append(({"[": "]", "⸢": "⸣", "<": ">"}[open_], "b")); open_ = None
            out.append((seps[j], "u"))
    if open_:
        out.append(({"[": "]", "⸢": "⸣", "<": ">"}[open_], "b"))
    return ([(lead, "u")] if lead else []) + out + ([(trail, "u")] if trail else [])


def rich_lines_of(tok_csv, txt, sides):
    """Lines of a text as rich segments, from the token table with sign marks (tokens_marks.csv)."""
    L = defaultdict(list)
    for r in csv.DictReader(open(tok_csv)):
        if r["txtid"] == txt and any(r["lnr"].startswith(s) for s in sides):
            if L[r["lnr"]]:
                L[r["lnr"]].append((" ", "u"))
            L[r["lnr"]] += rich_word(r["translit"], r.get("status") or "", r.get("layer") or "")
    return list(L.items())


def lead_gaps(xml_dir, txt):
    """Width of the break at the start of each line, as TLHdig encodes it: the <space c="n"/> blanks
    before the first preserved word of a line that opens inside a break (the break's ] comes after them).
    TLHdig gives a width, not a sign count; we keep its units."""
    import glob, re
    paths = [p for p in glob.glob(os.path.join(xml_dir, "*", txt + ".xml"))]
    if not paths:
        return {}
    s = open(paths[0], encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'<lb [^>]*lnr="([^"]+)"[^>]*/>(.*?)(?=<lb |$)', s, re.S):
        body, n = m.group(2), 0
        for w in re.finditer(r"<w[^>]*>(.*?)</w>", body, re.S):
            inner = w.group(1)
            sp = re.fullmatch(r'\s*<space c="(\d+)"/>\s*', inner)
            if sp:
                n += int(sp.group(1)); continue
            if re.fullmatch(r"\s*<del_(fin|in)/>\s*", inner):
                continue
            break
        if n:
            out[m.group(1)] = n
    return out


def main(cfg_path):
    cfg = json.load(open(cfg_path))
    base = os.path.dirname(os.path.abspath(cfg_path))
    out_scale = cfg["out_px_per_cm"]
    frags, meas = {}, {}
    for key in ("upper", "lower"):
        c = cfg[key]
        img = Image.open(os.path.join(base, c["photo"]))
        gray = np.asarray(img.convert("L")).astype(float)
        pxcm, blocks = ruler_px_per_cm(gray, *c["ruler_strip_x"], *c.get("ruler_strip_y", [0, None]))
        im, m = cutout(img, c["crop"], c["dark_background"], c["bg_threshold"])
        g = np.asarray(im.convert("L")).astype(float)
        band = c["text_band_in_crop"]
        ang = deskew(g, band, pxcm) if c.get("deskew", True) else 0.0
        g = ndimage.rotate(g, ang, reshape=False, order=1, mode="nearest")
        m = ndimage.rotate(m.astype(float), ang, reshape=False, order=0) > 0.5
        rgb = im.convert("L").rotate(-ang, resample=Image.BICUBIC, fillcolor=0) if False else Image.fromarray(np.clip(g, 0, 255).astype("uint8"))
        x0, y0, x1, y1 = band
        P, phase, sharp = spectrum_pitch(row_profile(g[y0:y1, x0:x1], pxcm), pxcm)
        r = {"px_per_cm": round(pxcm, 2), "ruler_blocks_px": blocks, "deskew_deg": ang,
             "spectrum_pitch_cm": round(P / pxcm, 3), "spectrum_sharpness": round(sharp, 4)}
        grid = [y0 + phase + k * P for k in range(int((y1 - y0 - phase) / P) + 1)]
        if "ruling_lines_between" in c:
            ru = rulings(g, band, pxcm, c["ruling_rows_approx_in_crop"])
            n = c["ruling_lines_between"]
            r["rulings_px"] = ru
            r["ruling_distance_cm"] = round((ru[1] - ru[0]) / pxcm, 3)
            r["pitch_from_rulings_cm"] = {str(k): round((ru[1] - ru[0]) / pxcm / k, 3) for k in n}
            grid = None
        meas[key] = r
        # rescale to the common output scale
        s = out_scale / pxcm
        gi = Image.fromarray(np.clip(g * c.get("gain", 1.0), 0, 255).astype("uint8"))
        alpha = Image.fromarray((m * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.5))
        rgba = Image.merge("RGBA", (gi, gi, gi, alpha))
        bb = rgba.getbbox()
        rgba = rgba.crop(bb)
        W, H = round(rgba.width * s), round(rgba.height * s)
        rgba = rgba.resize((W, H), Image.LANCZOS)
        mm = np.asarray(rgba.split()[3]) > 128
        sc = lambda v, o: (v - o) * s
        frags[key] = dict(img=rgba, mask=mm, s=s, bb=bb,
                          grid=[sc(v, bb[1]) for v in grid] if grid else None,
                          rulings=[sc(v, bb[1]) for v in r.get("rulings_px", [])],
                          band=(sc(x0, bb[0]), sc(y0, bb[1]), sc(x1, bb[0]), sc(y1, bb[1])),
                          edge_rows=[sc(v, bb[1]) for v in c["edge_rows_in_crop"]])
        meas[key]["size_cm"] = [round(W / out_scale, 2), round(H / out_scale, 2)]

    # placement: right boundaries aligned (on the rows where each piece shows its edge),
    # then the lower piece moved up until the cut-outs touch
    def right_x(f):
        r0, r1 = [int(v) for v in f["edge_rows"]]
        xs = [np.flatnonzero(row).max() for row in f["mask"][r0:r1] if row.any()]
        return float(np.median(xs))
    U, Lo = frags["upper"], frags["lower"]
    dx = right_x(U) - right_x(Lo)
    best = None
    for dy in range(U["mask"].shape[0] + 200, -Lo["mask"].shape[0] // 2, -1):
        H = max(U["mask"].shape[0], dy + Lo["mask"].shape[0]) + 2
        Wd = max(U["mask"].shape[1], int(dx) + Lo["mask"].shape[1]) + 2
        a = np.zeros((H + 10, Wd + 10), bool); b = a.copy()
        a[:U["mask"].shape[0], :U["mask"].shape[1]] = U["mask"]
        ox = int(round(dx))
        if ox < 0:
            continue
        b[dy:dy + Lo["mask"].shape[0], ox:ox + Lo["mask"].shape[1]] = Lo["mask"]
        if (a & b).sum() > cfg.get("touch_overlap_px", 40):
            best = dy + 1
            break
    meas["placement"] = {"dx_px": round(dx, 1), "dy_px": best, "rule": "right boundaries aligned; moved up until the cut-outs touch"}
    figure(cfg, base, frags, meas, dx, best)
    if cfg.get("out_slide_full_png"):   # the same figure for a slide: no caveats, larger transliteration
        figure(cfg, base, frags, meas, dx, best, caveats=False, out_png=cfg["out_slide_full_png"], tl_size=30)
    if cfg.get("out_slide_png"):
        slide_figure(cfg, base, frags, meas, dx, best)
    if cfg.get("out_slide_wide_png"):
        slide_wide(cfg, base, frags, meas, dx, best)
    json.dump(meas, open(os.path.join(base, cfg["out_json"]), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(meas, indent=1, ensure_ascii=False))


def figure(cfg, base, frags, meas, dx, dy, caveats=True, out_png=None, tl_size=26):
    S = cfg["out_px_per_cm"]
    F = lambda n, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), n)
    U, Lo = frags["upper"], frags["lower"]
    ox, oy = 340, 150
    W, H = 2700, max(oy + dy + Lo["img"].height + 160, 1680)
    out = Image.new("RGB", (W, H), (236, 226, 206)); d = ImageDraw.Draw(out)
    INK, RED, BLUE, GREEN, MUTE = (43, 26, 16), (138, 44, 18), (31, 78, 140), (60, 110, 50), (111, 88, 66)
    d.text((ox, 30), cfg["title"], fill=INK, font=F(40, True))
    d.text((ox, 84), cfg["subtitle"], fill=MUTE, font=F(24))
    out.paste(U["img"], (ox, oy), U["img"])
    lx, ly = ox + int(round(dx)), oy + dy
    out.paste(Lo["img"], (lx, ly), Lo["img"])
    # hypothetical common right edge
    ex = ox + int(np.median([np.flatnonzero(r).max() for r in U["mask"][int(U["edge_rows"][0]):int(U["edge_rows"][1])] if r.any()]))
    for y in range(oy - 20, ly + Lo["img"].height + 20, 24):
        d.line([(ex + 14, y), (ex + 14, y + 12)], fill=RED, width=4)
    d.multiline_text((ex - 250, ly + Lo["img"].height + 10), "hypothetical common\nright edge (unverified)", fill=RED, font=F(24))
    # line-spacing markers
    m = meas["upper"]
    if U["rulings"]:
        x0 = ox + U["band"][0] - 10
        for r in U["rulings"]:
            d.line([(ox + U["band"][0], oy + r), (ox + U["band"][2], oy + r)], fill=BLUE, width=3)
        y0, y1 = oy + U["rulings"][0], oy + U["rulings"][1]
        bx = ox + U["band"][0] - 280
        d.line([(bx, y0), (bx, y1)], fill=BLUE, width=4); d.line([(bx, y0), (bx + 20, y0)], fill=BLUE, width=4); d.line([(bx, y1), (bx + 20, y1)], fill=BLUE, width=4)
        pr = m["pitch_from_rulings_cm"]
        txt = "rulings %.2f cm apart\n%s" % (m["ruling_distance_cm"], "\n".join("%s lines: %.2f cm/line" % (k, v) for k, v in pr.items()))
        d.multiline_text((bx - 280, y0 + 10), txt, fill=BLUE, font=F(22), anchor="la")
    if Lo["grid"]:
        gs = [g for g in Lo["grid"] if Lo["band"][1] <= g <= Lo["band"][3]]
        for g in gs:
            d.line([(lx + Lo["band"][0] - 30, ly + g), (lx + Lo["band"][0] - 6, ly + g)], fill=BLUE, width=4)
        p = meas["lower"]["spectrum_pitch_cm"]
        d.multiline_text((lx + Lo["band"][0] - 300, ly + gs[0] - 10), "%.2f cm/line\n(%d lines marked)" % (p, len(gs)), fill=BLUE, font=F(22))
    # scale bar
    for i in range(5):
        d.rectangle([ox + i * S, H - 70, ox + (i + 1) * S, H - 56], fill=INK if i % 2 == 0 else (236, 226, 206), outline=INK)
    d.text((ox + 5 * S + 20, H - 80), "5 cm (each photo scaled by its own ruler)", fill=INK, font=F(22))
    # transliteration panel
    tx = ox + max(U["img"].width, int(dx) + Lo["img"].width) + 260
    y = oy
    col = {"drink": RED, "bread": BLUE, "close": GREEN}
    def hl(s):
        for k, pats in cfg["highlight"].items():
            if any(p in s for p in pats):
                return col[k]
        return INK
    tok = os.path.join(base, cfg.get("marks_csv", cfg["tokens_csv"]))
    IN = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
    FT = {"u": ImageFont.truetype(IN % "Regular", tl_size), "i": ImageFont.truetype(IN % "Italic", tl_size),
          "b": ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", tl_size)}
    lh = int(tl_size * 1.38)
    def mute(c):
        return tuple(int(v + (b - v) * 0.5) for v, b in zip(c, (236, 226, 206)))
    for key, label in (("upper", cfg["upper"]["label"]), ("lower", cfg["lower"]["label"])):
        d.text((tx, y), label, fill=INK, font=F(tl_size + 2, True)); y += int(lh * 1.25)
        for lnr, segs in rich_lines_of(tok, cfg[key]["txtid"], cfg[key]["sides"]):
            plain = "".join(t for t, k in segs if k != "b")
            if set(plain.replace(" ", "")) <= set("x"):
                continue
            c = hl(plain)
            d.text((tx, y), lnr.split()[-1], fill=MUTE, font=F(tl_size - 2))
            x = tx + int(tl_size * 3.4)
            for t, k in segs:
                f = FT[k[-1]] if k != "b" else FT["b"]
                d.text((x, y), t, fill=mute(c) if k.startswith("r") else c, font=f)
                x += d.textlength(t, font=f)
            y += lh
        y += 30
        if key == "upper":
            d.text((tx, y - 10), "[break: number of lost lines unknown]", fill=MUTE, font=F(22)); y += 40
    y += 10
    for k, lab in (("drink", "he drinks (1-ŠU ekuzi …)"), ("bread", "he breaks 1 takarmu-bread"), ("close", "closing: he goes through the gods in turn")):
        d.rectangle([tx, y + 6, tx + 22, y + 28], fill=col[k]); d.text((tx + 34, y), lab, fill=INK, font=F(24)); y += 38
    y += 20
    if caveats:
        d.multiline_text((tx, y), "\n".join(cfg["caveats"]), fill=MUTE, font=F(21), spacing=6)
    out.save(os.path.join(base, out_png or cfg["out_png"]))


def slide_figure(cfg, base, frags, meas, dx, dy):
    """Slide version: the placed pieces and the measurement marks only, on a transparent
    ground, with a few large labels; the transliteration and the key go on the slide itself."""
    F = lambda n: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", n)
    U, Lo = frags["upper"], frags["lower"]
    RED, BLUE = (138, 44, 18, 255), (31, 78, 140, 255)
    fs = cfg.get("slide_font_px", 80)
    ox, oy = cfg.get("slide_left_margin_px", 560), 30
    lx, ly = ox + int(round(dx)), oy + dy
    W = max(ox + U["img"].width, lx + Lo["img"].width) + 60
    H = ly + Lo["img"].height + 30
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    out.alpha_composite(U["img"], (ox, oy)); out.alpha_composite(Lo["img"], (lx, ly))
    ex = ox + int(np.median([np.flatnonzero(r).max() for r in U["mask"][int(U["edge_rows"][0]):int(U["edge_rows"][1])] if r.any()])) + 18
    for y in range(0, H, 36):
        d.line([(ex, y), (ex, y + 20)], fill=RED, width=7)
    m = meas["upper"]
    if U["rulings"]:
        for r in U["rulings"]:
            d.line([(ox + U["band"][0], oy + r), (ox + U["band"][2], oy + r)], fill=BLUE, width=6)
        y0, y1 = oy + U["rulings"][0], oy + U["rulings"][1]
        bx = ox + U["band"][0] - 40
        d.line([(bx, y0), (bx, y1)], fill=BLUE, width=7)
        for yy in (y0, y1):
            d.line([(bx, yy), (ox + U["band"][0], yy)], fill=BLUE, width=7)
        v = sorted(m["pitch_from_rulings_cm"].values())
        left = ox + min(np.flatnonzero(r).min() for r in U["mask"][int(U["rulings"][0]):int(U["rulings"][1])] if r.any())
        d.multiline_text((left - 30, (y0 + y1) / 2), "%.2f–%.2f\ncm/line" % (v[0], v[-1]), fill=BLUE, font=F(fs), anchor="rm", align="right")
    if Lo["grid"]:
        gs = [g for g in Lo["grid"] if Lo["band"][1] <= g <= Lo["band"][3]]
        tx = lx + Lo["band"][0] - 20
        for g in gs:
            d.line([(tx - 40, ly + g), (tx, ly + g)], fill=BLUE, width=7)
        d.multiline_text((tx - 64, ly + (gs[0] + gs[-1]) / 2), "%.2f\ncm/line" % meas["lower"]["spectrum_pitch_cm"], fill=BLUE, font=F(fs), anchor="rm", align="right")
    S = cfg["out_px_per_cm"]
    d.rectangle([ox - 480, H - 50, ox - 480 + 2 * S, H - 36], fill=(43, 26, 16, 255))
    d.text((ox - 480, H - 74), "2 cm", fill=(43, 26, 16, 255), font=F(fs), anchor="lb")
    out.save(os.path.join(base, cfg["out_slide_png"]))


def slide_wide(cfg, base, frags, meas, dx, dy, W=2880, H=1530, top_band=230):
    """Slide-shaped version (16:9 slide at 1.5x, minus a footer strip): the placed pieces fill the
    left, the transliteration fills the right below an empty band for the slide's own title.
    No title, subtitle or caveats; the scale bar sits bottom left, clear of the pieces."""
    F = lambda n, b=False: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if b else ""), n)
    U, Lo = frags["upper"], frags["lower"]
    BG, INK, RED, BLUE, GREEN, MUTE = (236, 226, 206), (43, 26, 16), (138, 44, 18), (31, 78, 140), (60, 110, 50), (111, 88, 66)
    S = cfg["out_px_per_cm"]
    # left panel at photo scale
    ox, oy = 600, 20
    lx, ly = ox + int(round(dx)), oy + dy
    ex = ox + int(np.median([np.flatnonzero(r).max() for r in U["mask"][int(U["edge_rows"][0]):int(U["edge_rows"][1])] if r.any()]))
    pw = max(ox + U["img"].width, lx + Lo["img"].width, ex + 60) + 20
    ph = ly + Lo["img"].height + 90
    L = Image.new("RGB", (pw, ph), BG); d = ImageDraw.Draw(L)
    L.paste(U["img"], (ox, oy), U["img"]); L.paste(Lo["img"], (lx, ly), Lo["img"])
    for y in range(oy, ly + Lo["img"].height + 20, 24):
        d.line([(ex + 14, y), (ex + 14, y + 12)], fill=RED, width=4)
    d.multiline_text((ex + 6, ly + Lo["img"].height + 24), "common right edge?", fill=RED, font=F(26), anchor="ra")
    m = meas["upper"]
    if U["rulings"]:
        for r in U["rulings"]:
            d.line([(ox + U["band"][0], oy + r), (ox + U["band"][2], oy + r)], fill=BLUE, width=3)
        y0, y1 = oy + U["rulings"][0], oy + U["rulings"][1]
        bx = ox + U["band"][0] - 260
        d.line([(bx, y0), (bx, y1)], fill=BLUE, width=4); d.line([(bx, y0), (bx + 20, y0)], fill=BLUE, width=4); d.line([(bx, y1), (bx + 20, y1)], fill=BLUE, width=4)
        pr = m["pitch_from_rulings_cm"]
        txt = "rulings %.2f cm apart\n%s" % (m["ruling_distance_cm"], "\n".join("%s lines: %.2f cm/line" % (k, v) for k, v in pr.items()))
        d.multiline_text((bx - 16, (y0 + y1) / 2), txt, fill=BLUE, font=F(28), anchor="rm", align="right")
    if Lo["grid"]:
        gs = [g for g in Lo["grid"] if Lo["band"][1] <= g <= Lo["band"][3]]
        for g in gs:
            d.line([(lx + Lo["band"][0] - 30, ly + g), (lx + Lo["band"][0] - 6, ly + g)], fill=BLUE, width=4)
        d.multiline_text((lx + Lo["band"][0] - 44, ly + gs[0]), "%.2f cm/line\n(%d lines)" % (meas["lower"]["spectrum_pitch_cm"], len(gs)),
                         fill=BLUE, font=F(28), anchor="ra", align="right")
    for i in range(5):
        d.rectangle([30 + i * S, ph - 60, 30 + (i + 1) * S, ph - 44], fill=INK if i % 2 == 0 else BG, outline=INK)
    d.text((30, ph - 70), "5 cm, each photo scaled by its own ruler", fill=INK, font=F(26), anchor="lb")
    k = (H - 20) / ph
    L = L.resize((int(pw * k), int(ph * k)), Image.LANCZOS)
    out = Image.new("RGB", (W, H), BG); out.paste(L, (10, 10)); d = ImageDraw.Draw(out)
    # transliteration panel
    tx = 10 + L.width + 50
    col = {"drink": RED, "bread": BLUE, "close": GREEN}
    def hl(t):
        for kk, pats in cfg["highlight"].items():
            if any(p in t for p in pats):
                return col[kk]
        return INK
    tok = os.path.join(base, cfg.get("marks_csv", cfg["tokens_csv"]))
    blocks = []
    for key in ("upper", "lower"):
        gaps = lead_gaps(os.path.join(base, cfg["xml_dir"]), cfg[key]["txtid"]) if cfg[key].get("show_lead_gaps") else {}
        rows = []
        for lnr, segs in rich_lines_of(tok, cfg[key]["txtid"], cfg[key]["sides"]):
            if set("".join(t for t, kk in segs if kk != "b").replace(" ", "")) <= set("x"):
                continue
            g = gaps.get(lnr, 0)
            if g:  # "[" + blank as wide as TLHdig's spacing; a restored first word stays inside the same break
                segs = ([("[", "b"), ("", "g%d" % g)] + segs[1:]) if segs and segs[0] == ("[", "b") \
                    else ([("[", "b"), ("", "g%d" % g), ("]", "b")] + ([] if segs and segs[0][0].startswith("-") else [(" ", "u")]) + segs)
            rows.append((lnr, segs))
        blocks.append((cfg[key]["label"], rows))
    nrows = sum(len(r) for _, r in blocks)
    IN = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
    for size in range(60, 20, -1):  # largest size whose lines fit the panel
        lh = int(size * 1.32)
        need = top_band + 2 * int(lh * 1.25) + nrows * lh + int(lh * 1.0) + 2 * 24 + int(lh * 1.1) * 3
        FT = {"u": ImageFont.truetype(IN % "Regular", size), "i": ImageFont.truetype(IN % "Italic", size),
              "b": ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)}
        GW = lambda kk: int(kk[1:]) * size * cfg.get("gap_em_per_unit", 0.25)
        wid = max(sum(GW(kk) if kk[0] == "g" else d.textlength(t, font=FT[kk[-1]] if kk != "b" else FT["b"]) for t, kk in segs)
                  for _, rows in blocks for _, segs in rows) + size * 3.2
        if need <= H and tx + wid <= W - 30:
            break
    def mute(c):
        return tuple(int(v + (b - v) * 0.5) for v, b in zip(c, BG))
    y = top_band
    for bi, (label, rows) in enumerate(blocks):
        d.text((tx, y), label, fill=INK, font=F(size, True)); y += int(lh * 1.25)
        for lnr, segs in rows:
            c = hl("".join(t for t, kk in segs if kk != "b"))
            d.text((tx, y + size * 0.08), lnr.split()[-1], fill=MUTE, font=F(int(size * 0.85)))
            x = tx + int(size * 3.2)
            for t, kk in segs:
                if kk[0] == "g":
                    x += GW(kk); continue
                f = FT[kk[-1]] if kk != "b" else FT["b"]
                d.text((x, y), t, fill=mute(c) if kk.startswith("r") else c, font=f)
                x += d.textlength(t, font=f)
            y += lh
        y += 24
        if bi == 0:
            d.text((tx, y - 6), "[break: number of lost lines unknown]", fill=MUTE, font=F(int(size * 0.8))); y += int(lh * 1.0)
    for kk, lab in (("drink", "he drinks"), ("bread", "he breaks a takarmu-bread"), ("close", "closing the round of the gods")):
        d.rectangle([tx, y + size * 0.25, tx + size * 0.75, y + size], fill=col[kk]); d.text((tx + size * 1.1, y), lab, fill=INK, font=F(int(size * 0.9))); y += int(lh * 1.1)
    out.save(os.path.join(base, cfg["out_slide_wide_png"]))
    print("slide_wide: font %d px, text from x=%d, left panel %dx%d" % (size, tx, L.width, L.height))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "joinfit_EBo133_KBo44140.json"))
