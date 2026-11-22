"""Map of the Hittite archives for the SIGHUM paper.

Base map: M. Cammarosano, "A Map of the Hittite World" (OSF, https://osf.io/cbyv8/),
file MHW_basic_blank.png, based on "Near East topographic map-blank.svg" by Sémhur /
Wikimedia Commons; the image carries CC BY-SA. It is fetched at build time, not stored in git.

Archive sizes: number of manuscripts in TLHdig 0.4 (orphans/data/tokens_marks.csv), assigned
to a find site by the siglum of the publication series (HKM = Maşat Höyük, KuSa/KuT = Kuşaklı,
Or. = Ortaköy, Kp = Kayalıpınar, Msk = Meskene/Emar, RS = Ras Shamra/Ugarit, AT = Alalaḫ);
every other manuscript is counted for Ḫattuša.

Writes ../generated/archive_map.tex (site positions and counts as TikZ macros) and the
cropped base maps in external/.
"""
import csv, os, re, sys, collections, urllib.request
from PIL import Image, ImageOps, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "external")
GEN = os.path.join(HERE, "..", "generated")
TOKENS = os.path.join(HERE, "..", "..", "orphans", "data", "tokens_marks.csv")
BASE_URL = "https://osf.io/download/vd5eg/"   # MHW_basic_blank.png
BASE = os.path.join(EXT, "MHW_basic_blank.png")

SERIES = {"HKM": "tapikka", "KuSa": "sarissa", "KuT": "sarissa", "Or": "sapinuwa",
          "Kp": "samuha", "Msk": "emar", "RS": "ugarit", "AT": "alalah"}
# symbol centres on the base map, in pixels of the full image (7806 x 5167), read off the image
SITES = {  # key: (label, modern name, x, y)
    "hattusa":  ("Ḫattuša", "Boğazköy", 3358, 1161),
    "sapinuwa": ("Šapinuwa", "Ortaköy", 3545, 1092),
    "tapikka":  ("Tapikka", "Maşat Höyük", 3710, 1116),
    "samuha":   ("Šamuḫa", "Kayalıpınar", 3917, 1322),
    "sarissa":  ("Šarišša", "Kuşaklı", 4080, 1402),
    "emar":     ("Emar", "Meskene", 4365, 2725),
    "ugarit":   ("Ugarit", "Ras Shamra", 3688, 2832),
    "alalah":   ("Alalaḫ", "Tell Atchana", 3845, 2630),
}
CROPS = {"wide": (900, 350, 5100, 3150), "core": (2950, 750, 4400, 1650)}


def counts():
    ids = set()
    with open(TOKENS, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ids.add(row["txtid"])
    c = collections.Counter()
    for t in ids:
        c[SERIES.get(re.split(r"[ .]", t)[0], "hattusa")] += 1
    return c


def main():
    os.makedirs(EXT, exist_ok=True)
    if not os.path.exists(BASE):
        urllib.request.urlretrieve(BASE_URL, BASE)
    im = Image.open(BASE).convert("RGB")
    for name, box in CROPS.items():
        c = im.crop(box)
        c.save(os.path.join(EXT, f"map_{name}_colour.png"))
        g = ImageOps.grayscale(c)
        g = ImageEnhance.Brightness(ImageEnhance.Contrast(g).enhance(0.55)).enhance(1.25)
        g.save(os.path.join(EXT, f"map_{name}_grey.png"))
    n = counts()
    for opt, spec in OPTIONS.items():
        with open(os.path.join(GEN, f"archive_map_{opt}.tex"), "w", encoding="utf-8") as f:
            f.write(tikz(opt, spec, n))
    with open(os.path.join(GEN, "archive_counts.csv"), "w", encoding="utf-8") as f:
        f.write("site,label,modern,manuscripts\n")
        for k, (lab, modern, x, y) in SITES.items():
            f.write(f"{k},{lab},{modern},{n[k]}\n")
    for k in SITES:
        print(k, n[k])
    print("total", sum(n.values()))


# Published sizes of the archives (tablets and fragments). hm2024 = Hoffner and Melchert 2024,
# Introduction, sections 0.6-0.8: Hattusa "well over 30,000", Ortakoy "more than three thousand",
# Masat "approximately 116". Kusakli and Kayalipinar: no total given there; the number of their
# published manuscripts in TLHdig 0.4 is used instead (marked with an asterisk).
PUBLISHED = {"hattusa": (30000, "30{,}000+", "hm2024"), "sapinuwa": (3000, "3{,}000+", "hm2024"),
             "tapikka": (116, "116", "hm2024"),
             # Kayalipinar: 53 tablets and fragments from 1999-2017 (Rieken 2019) and 131 from the
             # 2026 season (excavation press release, Koc University and Turkish Ministry of Culture)
             "samuha": (184, "184", "press2026")}

CORE = ["hattusa", "sapinuwa", "tapikka", "samuha", "sarissa"]
SYRIA = ["emar", "ugarit", "alalah"]
# label: (dx, dy) in cm from the site to the label anchor, the anchor, and whether to show the name
WIDE_LABELS = {"hattusa": (-1.25, 0.55, "south east"), "sapinuwa": (-0.35, 1.05, "south"),
               "tapikka": (0.55, 0.95, "south west"), "samuha": (1.1, 0.35, "west"),
               "sarissa": (0.95, -0.35, "west"), "emar": (0.3, 0.55, "south west"),
               "ugarit": (-1.0, -0.25, "east"), "alalah": (-1.0, 0.25, "east")}
CORE_LABELS = {"hattusa": (-0.2, -1.2, "north"), "sapinuwa": (0.0, 0.75, "south"),
               "tapikka": (0.45, 0.7, "south west"), "samuha": (0.05, -0.55, "north"),
               "sarissa": (0.0, -0.45, "north")}
D_LABELS = {"hattusa": (-0.9, 0.5, "south east"), "sapinuwa": (-0.25, 0.8, "south"),
            "tapikka": (0.45, 0.75, "south west"), "samuha": (0.9, 0.25, "west"),
            "sarissa": (0.8, -0.3, "west")}
OPTIONS = {
    # A: true area (area = manuscripts), Ḫattuša drawn as a ring so its neighbours stay visible
    "A": dict(crop="wide", base="colour", sites=CORE + SYRIA, width=7.7, scale="area", rmax=0.75,
              wash=0.5, labels=WIDE_LABELS, names=True),
    # B: radius by order of magnitude, with a size key
    "B": dict(crop="wide", base="grey", sites=CORE + SYRIA, width=7.7, scale="log", rmax=0.42,
              wash=0.0, labels=WIDE_LABELS, names=True, key="sw"),
    # C: close-up of the core; the base map already names the sites, so only counts are added
    # D: terrain map in colour, circle area in true proportion to the published size of each archive
    "D": dict(crop="wide", base="colour", sites=CORE, width=7.7, scale="area", rmax=0.22, rmin=0.035,
              wash=0.2, labels=D_LABELS, names=True, key="sw", sizes="published"),
    "C": dict(crop="core", base="grey", sites=CORE, width=7.7, scale="log", rmax=0.5,
              wash=0.0, labels=CORE_LABELS, names=False, key="below"),
}


def fmt(v):
    return f"{v:,}".replace(",", "{,}")


def radius(spec, v, nmax):
    if spec["scale"] == "area":
        return max(spec["rmax"] * (v / nmax) ** 0.5, spec.get("rmin", 0.05))
    import math
    return spec["rmax"] * math.log10(max(v, 1) + 1) / math.log10(nmax + 1) if v else 0.05


def tikz(opt, spec, n):
    x0, y0, x1, y1 = CROPS[spec["crop"]]
    W = spec["width"]; H = W * (y1 - y0) / (x1 - x0)
    size = {k: n[k] for k in spec["sites"]}
    shown = {k: fmt(n[k]) for k in spec["sites"]}
    if spec.get("sizes") == "published":
        for k in spec["sites"]:
            if k in PUBLISHED:
                size[k], shown[k] = PUBLISHED[k][0], PUBLISHED[k][1]
            else:
                shown[k] = fmt(n[k]) + "*"
    nmax = max(size.values())
    L = ["% generated by figures/make_archive_map.py; do not edit",
         "\\begin{tikzpicture}[lbl/.style={font=\\scriptsize, align=center, inner sep=1.2pt, fill=white, fill opacity=0.85, text opacity=1, rounded corners=1pt}]",
         f"\\node[anchor=south west, inner sep=0] at (0,0) {{\\includegraphics[width={W}cm]{{external/map_{spec['crop']}_{spec['base']}.png}}}};"]
    if spec["wash"]:
        L.append(f"\\fill[white, opacity={spec['wash']}] (0,0) rectangle ({W},{H:.3f});")
    L.append(f"\\draw[gray!60, line width=0.3pt] (0,0) rectangle ({W},{H:.3f});")
    for k in sorted(spec["sites"], key=lambda k: -size[k]):
        lab, modern, x, y = SITES[k]
        X = (x - x0) / (x1 - x0) * W; Y = H - (y - y0) / (y1 - y0) * H
        r = radius(spec, size[k], nmax)
        if spec["scale"] == "area" and k == "hattusa" and opt == "A":
            L.append(f"\\fill[clay, fill opacity=0.12] ({X:.3f},{Y:.3f}) circle ({r:.3f});")
            L.append(f"\\draw[clay!80!black, line width=0.7pt] ({X:.3f},{Y:.3f}) circle ({r:.3f});")
            L.append(f"\\fill[clay!80!black] ({X:.3f},{Y:.3f}) circle (0.04);")
        else:
            fo = 0.6 if r > 0.15 else 0.85
            L.append(f"\\fill[clay, fill opacity={fo}, draw=clay!60!black, line width=0.4pt] ({X:.3f},{Y:.3f}) circle ({r:.3f});")
        dx, dy, anc = spec["labels"][k]
        if opt == "A" and k == "hattusa":
            dx, dy = -r * 0.75, r * 0.75
        txt = (f"\\textbf{{{lab}}} {shown[k]}" if spec["names"] else f"\\textbf{{{shown[k]}}}")
        L.append(f"\\draw[clay!60!black, line width=0.3pt] ({X:.3f},{Y:.3f}) -- ({X+dx:.3f},{Y+dy:.3f});")
        L.append(f"\\node[lbl, anchor={anc}] at ({X+dx:.3f},{Y+dy:.3f}) {{{txt}}};")
    if spec["scale"] == "log" or spec.get("key"):
        vals = (10, 100, 1000, 10000) if spec["scale"] == "log" else (1000, 10000, 30000)
        rs = [radius(spec, v, nmax) for v in vals]
        kw = sum(2 * r + (0.18 if spec["scale"] == "log" else 0.5) for r in rs) + 0.12
        kh = 2 * max(rs) + 0.55
        kx = 0.12 if spec["key"] in ("sw", "nw") else W - kw - 0.12
        ky = 0.12 if spec["key"] in ("sw", "se") else H - kh - 0.12
        if spec["key"] == "below":
            kx, ky = (W - kw) / 2, -kh - 0.02
        L.append(f"\\fill[white, opacity=0.88, rounded corners=1pt] ({kx:.3f},{ky:.3f}) rectangle ({kx+kw:.3f},{ky+kh:.3f});")
        cx = kx + 0.15
        base = ky + 0.42
        for v, r in zip(vals, rs):
            L.append(f"\\fill[clay, fill opacity=0.8, draw=clay!60!black, line width=0.4pt] ({cx+r:.3f},{base+r:.3f}) circle ({r:.3f});")
            L.append(f"\\node[font=\\tiny, anchor=north, inner sep=1pt] at ({cx+r:.3f},{base:.3f}) {{{fmt(v)}}};")
            cx += 2 * r + (0.18 if spec["scale"] == "log" else 0.5)
        L.append(f"\\node[font=\\tiny, anchor=south, inner sep=1pt] at ({kx+kw/2:.3f},{ky+0.02:.3f}) {{{'tablets and fragments' if spec.get('sizes') == 'published' else 'manuscripts in TLHdig 0.4'}}};")
    L.append(f"\\node[anchor=south east, font=\\tiny, text=gray!70!black, align=right] at ({W-0.05},0.03) {{Base map: Cammarosano, CC BY-SA}};")
    L.append("\\end{tikzpicture}")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# Classed symbols (E, F): archaeological maps mark sites with one symbol whose size shows an
# ordinal class, not a proportional circle; the counts go in the legend or caption.
CLASSES = [(10000, 0.30, "over 10{,}000"), (1000, 0.21, "1{,}000--10{,}000"),
           (100, 0.15, "100--1{,}000"), (0, 0.11, "under 100")]
LABELS_EF = {"hattusa": (-0.22, 0.0, "east"), "sapinuwa": (0.0, 0.2, "south"),
             "tapikka": (0.14, 0.2, "south west"), "samuha": (0.2, -0.02, "south west"),
             "sarissa": (0.14, -0.06, "north west")}


def site_size(k, n):
    return PUBLISHED[k][0] if k in PUBLISHED else n[k]


def tikz_classed(opt, n, inset):
    x0, y0, x1, y1 = CROPS["wide"]
    W = 7.7; H = W * (y1 - y0) / (x1 - x0)
    L = ["% generated by figures/make_archive_map.py; do not edit",
         "\\begin{tikzpicture}[lbl/.style={align=left, inner sep=1pt, fill=white, fill opacity=0.8, text opacity=1, rounded corners=1pt}]",
         f"\\node[anchor=south west, inner sep=0] at (0,0) {{\\includegraphics[width={W}cm]{{external/map_wide_colour.png}}}};",
         f"\\fill[white, opacity=0.2] (0,0) rectangle ({W},{H:.3f});",
         f"\\draw[gray!60, line width=0.3pt] (0,0) rectangle ({W},{H:.3f});"]
    for k in CORE:
        lab, modern, x, y = SITES[k]
        X = (x - x0) / (x1 - x0) * W; Y = H - (y - y0) / (y1 - y0) * H
        side = next(sz for lo, sz, _ in CLASSES if site_size(k, n) >= lo)
        h = side / 2
        L.append(f"\\filldraw[fill=clay, draw=white, line width=0.5pt] ({X-h:.3f},{Y-h:.3f}) rectangle ({X+h:.3f},{Y+h:.3f});")
        dx, dy, anc = LABELS_EF[k]
        L.append(f"\\node[lbl, anchor={anc}, font=\\scriptsize] at ({X+dx:.3f},{Y+dy:.3f}) {{\\textbf{{{lab}}}\\\\[-2pt]{{\\tiny\\itshape {modern}}}}};")
    if not inset:
        # legend of the classes, bottom left (in the sea)
        kx, ky = 0.15, 0.15
        rows = len(CLASSES)
        L.append(f"\\fill[white, opacity=0.88, rounded corners=1pt] ({kx},{ky}) rectangle ({kx+2.3},{ky+0.32*rows+0.35});")
        L.append(f"\\node[anchor=north west, font=\\tiny\\bfseries, inner sep=1pt] at ({kx+0.05},{ky+0.32*rows+0.32}) {{Tablets and fragments}};")
        for i, (lo, side, txt) in enumerate(CLASSES):
            cy = ky + 0.32 * (rows - i) - 0.12; h = side / 2; cx = kx + 0.22
            L.append(f"\\filldraw[fill=clay, draw=white, line width=0.5pt] ({cx-h:.3f},{cy-h:.3f}) rectangle ({cx+h:.3f},{cy+h:.3f});")
            L.append(f"\\node[anchor=west, font=\\tiny, inner sep=1pt] at ({kx+0.45},{cy:.3f}) {{{txt}}};")
    else:
        # small bar chart on a log scale, bottom left (in the sea)
        order = sorted(CORE, key=lambda k: -site_size(k, n))
        kx, ky, bw, rh = 0.15, 0.15, 1.7, 0.24
        import math
        lo, hi = 1, math.log10(30000)
        top = ky + rh * len(order) + 0.55
        L.append(f"\\fill[white, opacity=0.9, rounded corners=1pt] ({kx},{ky}) rectangle ({kx+3.0},{top:.3f});")
        L.append(f"\\node[anchor=north west, font=\\tiny\\bfseries, inner sep=1pt] at ({kx+0.05},{top-0.02:.3f}) {{Tablets and fragments (log scale)}};")
        bx = kx + 0.8
        base = ky + 0.3
        for i, k in enumerate(order):
            v = site_size(k, n)
            cy = base + rh * (len(order) - 1 - i) + rh / 2
            w = bw * (math.log10(v) - lo) / (hi - lo)
            shown = PUBLISHED[k][1] if k in PUBLISHED else fmt(n[k]) + "*"
            L.append(f"\\node[anchor=east, font=\\tiny, inner sep=1pt] at ({bx-0.03:.3f},{cy:.3f}) {{{SITES[k][0]}}};")
            L.append(f"\\fill[clay] ({bx:.3f},{cy-rh*0.32:.3f}) rectangle ({bx+w:.3f},{cy+rh*0.32:.3f});")
            L.append(f"\\node[anchor=west, font=\\tiny, inner sep=1pt] at ({bx+w+0.02:.3f},{cy:.3f}) {{{shown}}};")
        for t, tl in ((10, "10"), (100, "100"), (1000, "1k"), (10000, "10k")):
            tx = bx + bw * (math.log10(t) - lo) / (hi - lo)
            L.append(f"\\draw[gray!60, line width=0.2pt] ({tx:.3f},{base:.3f}) -- ({tx:.3f},{base-0.04:.3f}); \\node[anchor=north, font=\\tiny, text=gray!70!black, inner sep=0.5pt] at ({tx:.3f},{base-0.04:.3f}) {{{tl}}};")
        # same symbol for all sites on the map in F: replace sized squares by one size
    L.append(f"\\node[anchor=south east, font=\\tiny, text=gray!70!black, align=right] at ({W-0.05},0.03) {{Base map: Cammarosano, CC BY-SA}};")
    L.append("\\end{tikzpicture}")
    out = "\n".join(L) + "\n"
    if inset:
        import re as _re
        def same(m):
            X0, Y0, X1, Y1 = map(float, m.groups())
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
            return f"\\filldraw[fill=clay, draw=white, line width=0.5pt] ({cx-0.08:.3f},{cy-0.08:.3f}) rectangle ({cx+0.08:.3f},{cy+0.08:.3f});"
        out = _re.sub(r"\\filldraw\[fill=clay, draw=white, line width=0\.5pt\] \(([\d.]+),([\d.]+)\) rectangle \(([\d.]+),([\d.]+)\);", same, out)
    return out


_main = main


def main():
    _main()
    n = counts()
    for opt, inset in (("E", False), ("F", True)):
        with open(os.path.join(GEN, f"archive_map_{opt}.tex"), "w", encoding="utf-8") as f:
            f.write(tikz_classed(opt, n, inset))


if __name__ == "__main__":
    main()
