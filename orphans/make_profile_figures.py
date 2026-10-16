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

# 3. E8 word classes: each class alone vs everything except that class (word forms)
E8 = json.loads((RES / "E8_report.json").read_text())
CL = [("foreign", "Hurrian / foreign"), ("realia", "realia (nouns)"), ("deity", "divine names"),
      ("agent", "agents"), ("verb", "verbs"), ("function", "function words")]
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
h = E8["historical"]["all"]["words"]
for ax, (key, title) in zip(axes, [("historical", f"{h['classes']} traditions ({h['n']:,} texts)"),
                                   ("cth701_subgroups", f"CTH 701 subgroups ({E8['cth701_subgroups']['all']['words']['n']} texts)")]):
    R = E8[key]
    ax.grid(axis="x", color=GRID, lw=1)
    allacc = R["all"]["words"]["acc"]
    ax.axvline(allacc, color=INK2, lw=1.5, ls="--")
    ax.text(allacc + 0.01, -0.75, f"all words {allacc:.0%}", ha="left", color=INK2, fontsize=11)
    for i, (c, name) in enumerate(CL):
        y = len(CL) - 1 - i
        a, w = R[f"only_{c}"]["words"]["acc"], R[f"without_{c}"]["words"]["acc"]
        ax.plot([a, w], [y + 0.12, y - 0.12], color=GRID, lw=3, zorder=1)
        ax.plot(a, y + 0.12, "o", ms=11, color=CONTENT, mec=SURF, mew=2, zorder=3)
        ax.plot(w, y - 0.12, "o", ms=11, color=SCRIBAL, mec=SURF, mew=2, zorder=3)
        ax.plot(R[f"only_{c}"]["words"]["majority"], y, "|", ms=18, mew=2.5, color=INK, zorder=2)
    ax.set_yticks(range(len(CL)), [n for _, n in CL][::-1])
    ax.set(xlim=(0, 1), ylim=(-0.95, len(CL) - 0.5), title=title, xlabel="correct group (word forms)")
    ax.title.set_color(INK2); ax.title.set_fontsize(13)
axes[0].plot([], [], "o", ms=10, color=CONTENT, label="this class alone")
axes[0].plot([], [], "o", ms=10, color=SCRIBAL, label="all words except this class")
axes[0].plot([], [], "|", ms=12, mew=2.5, color=INK, label="majority class")
fig.legend(frameon=False, loc="upper center", ncol=3, fontsize=12, bbox_to_anchor=(0.55, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(OUT / "wordclasses.png", dpi=200)
plt.close(fig)
print("figures in", OUT)
