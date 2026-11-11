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
import json, sys, csv, os
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
    json.dump(meas, open(os.path.join(base, cfg["out_json"]), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(meas, indent=1, ensure_ascii=False))


def figure(cfg, base, frags, meas, dx, dy):
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
    tok = os.path.join(base, cfg["tokens_csv"])
    for key, label in (("upper", cfg["upper"]["label"]), ("lower", cfg["lower"]["label"])):
        d.text((tx, y), label, fill=INK, font=F(28, True)); y += 44
        for lnr, t in lines_of(tok, cfg[key]["txtid"], cfg[key]["sides"]):
            if set(t.replace(" ", "")) <= set("x"):
                continue
            d.text((tx, y), lnr.split()[-1], fill=MUTE, font=F(24)); d.text((tx + 90, y), t, fill=hl(t), font=F(26)); y += 36
        y += 30
        if key == "upper":
            d.text((tx, y - 10), "[break: number of lost lines unknown]", fill=MUTE, font=F(22)); y += 40
    y += 10
    for k, lab in (("drink", "he drinks (1-ŠU ekuzi …)"), ("bread", "he breaks 1 takarmu-bread"), ("close", "closing: he goes through the gods in turn")):
        d.rectangle([tx, y + 6, tx + 22, y + 28], fill=col[k]); d.text((tx + 34, y), lab, fill=INK, font=F(24)); y += 38
    y += 20
    d.multiline_text((tx, y), "\n".join(cfg["caveats"]), fill=MUTE, font=F(21), spacing=6)
    out.save(os.path.join(base, cfg["out_png"]))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "joinfit_EBo133_KBo44140.json"))
