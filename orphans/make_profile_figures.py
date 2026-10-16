"""E7 slide figures: python make_profile_figures.py results/tlhdig03 ../img/orphans"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

# reference palette (dataviz skill), light mode
CONTENT, SCRIBAL = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, SURF, MID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb", "#f0efec"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
rep = json.loads((RES / "E7_report.json").read_text())


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)


# 1. which layer identifies a tradition?
L = rep["E7a_layers"]
rows = [("Logograms", "logograms", CONTENT), ("Hittite vocabulary", "lexicon", CONTENT),
        ("Hurrian/Luwian/Hattian words*", "foreign", CONTENT),
        ("Same words, spelling ignored", "collapsed", SCRIBAL), ("Same words, spelling kept", "spelling", SCRIBAL),
        ("Orthographic habits (7 rates)", "orthographic_indices", SCRIBAL)]
fig, ax = plt.subplots(figsize=(11, 5.4))
ax.grid(axis="x", color=GRID, lw=1)
for i, (name, key, col) in enumerate(rows):
    y = len(rows) - 1 - i
    r = L[key]
    ax.barh(y, r["acc"], height=0.5, color=col, zorder=2)
    ax.plot(r["majority"], y, "|", ms=26, mew=3, color=INK, zorder=3)
    ax.plot(r["null_mean"], y, "|", ms=26, mew=3, color=MUTED, zorder=3)
    ax.text(r["acc"] + 0.012, y, f"{r['acc']:.0%}", va="center", color=INK, fontsize=14, weight="bold")
ax.set_yticks(range(len(rows)), [n for n, _, _ in rows][::-1])
ax.set(xlim=(0, 1), xlabel="correct tradition (share of texts)")
ax.axhline(2.5, color=MUTED, lw=1, ls=":")
ax.text(0.99, 5.45, "what is written", ha="right", color=CONTENT, fontsize=13, weight="bold")
ax.text(0.99, 2.2, "how it is written", ha="right", color=SCRIBAL, fontsize=13, weight="bold")
ax.plot([], [], "|", ms=14, mew=3, color=INK, label="majority class")
ax.plot([], [], "|", ms=14, mew=3, color=MUTED, label="permuted labels")
ax.legend(frameon=False, loc="lower right", fontsize=12, ncol=2, bbox_to_anchor=(1, 1.0))
save(fig, "layers")

# 2. orthographic profile per tradition (mean z-score)
Z = pd.DataFrame(rep["E7b_index_profile_z"]).T
names = {"logogram_share": "logograms\nper word", "akkadogram_share": "Akkado-\ngrams", "complement_rate": "phonetic\ncomplements",
         "determinative_rate": "determi-\nnatives", "plene_rate": "plene\nwriting", "cvc_share": "CVC\nsigns",
         "u_acute_share": "ú for u"}
Z = Z[list(names)]
cmap = LinearSegmentedColormap.from_list("div", [CONTENT, MID, "#d03b3b"])
fig, ax = plt.subplots(figsize=(12, 5.2))
lim = 0.7
ax.imshow(Z.to_numpy(), cmap=cmap, vmin=-lim, vmax=lim, aspect="auto")
for (i, j), v in np.ndenumerate(Z.to_numpy()):
    ax.text(j, i, f"{v:+.2f}", ha="center", va="center", fontsize=12, color=INK if abs(v) < 0.45 else SURF)
ax.set_xticks(range(Z.shape[1]), list(names.values()), fontsize=12)
ax.set_yticks(range(Z.shape[0]), Z.index, fontsize=13)
ax.tick_params(length=0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title("mean z-score vs all reference texts (blue = less, red = more)", loc="left", color=INK2, fontsize=13)
save(fig, "orthography_profile")
print("figures in", OUT)
