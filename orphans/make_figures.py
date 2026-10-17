"""Slide figures from a results directory: python make_figures.py results/tlhdig03 ../img/orphans"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RES, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

# reference palette (dataviz skill), light mode: categorical slots 1-3, ink, grid
SERIES = {"words": "#2a78d6", "signs": "#eb6834", "both": "#1baf7a"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 15, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})
LABEL = {"words": "word tf-idf", "signs": "sign n-grams", "both": "words + signs"}
rep = json.loads((RES / "report.json").read_text())


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.png", dpi=200)
    plt.close(fig)


# 1. coverage curve: accuracy vs fragment size
cur = pd.read_csv(RES / "E2_coverage_curve.csv")
k_classes = rep["E1_historical"]["both"]["classes"]
fig, ax = plt.subplots(figsize=(10, 5.6))
ax.grid(axis="y", color=GRID, lw=1)
for sp, g in cur.groupby("space"):
    ax.plot(g.k, g.acc, color=SERIES[sp], lw=2.2, marker="o", ms=8,
            markeredgecolor=SURF, markeredgewidth=2, label=LABEL[sp])
ax.axhline(1 / k_classes, color=MUTED, lw=1.5, ls="--")
ax.text(cur.k.max(), 1 / k_classes + 0.015, f"chance (1/{k_classes})", ha="right", color=MUTED, fontsize=12)
ax.axvline(17, color=GRID, lw=1.5)
ax.text(17.5, 0.08, "17-word cut-off\n(StBoT 73)", color=MUTED, fontsize=11)
ax.set(xlabel="fragment size (legible words)", ylabel="correct tradition (share)", ylim=(0, 1),
       xlim=(0, cur.k.max() * 1.05))
ax.legend(frameon=False, loc="upper left", fontsize=13)
save(fig, "coverage_curve")

# 2. reference-space validation: accuracy against both baselines
REF_NAME = {"literature": "Literature-defined\ntraditions", "hfr": "Literature groups,\nHFR festival modules"}.get(rep.get("groups"), "Historical groups\n(Table 3 + rituals)")
rows = [(REF_NAME, rep["E1_historical"]["both"]),
        ("CTH 670 / 701 / 832\n(abstract)", rep["E1_abstract_670_701_832"]["both"]),
        ("CTH 701 subgroups\n(Salvini–Wegner)", rep["E3_cth701_subgroups"]["both"])]
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.grid(axis="x", color=GRID, lw=1)
for i, (name, r) in enumerate(rows):
    y = len(rows) - 1 - i
    ax.barh(y, r["acc"], height=0.42, color=SERIES["words"], zorder=2)
    ax.plot(r["majority"], y, "|", ms=30, mew=3, color=INK, zorder=3)
    ax.plot(r["null_mean"], y, "|", ms=30, mew=3, color=MUTED, zorder=3)
    ax.text(r["acc"] + 0.012, y, f"{r['acc']:.0%}", va="center", color=INK, fontsize=14, weight="bold")
    ax.text(0.005, y - 0.36, f"n = {r['n']} texts, {r['classes']} classes", color=INK2, fontsize=11)
ax.set_yticks(range(len(rows)), [n for n, _ in rows][::-1])
ax.set(xlim=(0, 1), ylim=(-0.65, len(rows) - 0.5), xlabel="leave-one-out accuracy (words + signs)")
ax.plot([], [], "|", ms=14, mew=3, color=INK, label="majority class")
ax.plot([], [], "|", ms=14, mew=3, color=MUTED, label="permuted labels")
ax.legend(frameon=False, loc="lower right", fontsize=12, ncol=2, bbox_to_anchor=(1, 1.0))
save(fig, "validation")

# 3. orphans placed per tradition
e5 = rep["E5_orphans"]
bt = pd.Series(e5["by_tradition"]).sort_values()
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.grid(axis="x", color=GRID, lw=1)
ax.barh(range(len(bt)), bt.values, height=0.55, color=SERIES["words"], zorder=2)
for i, v in enumerate(bt.values):
    ax.text(v + 2, i, str(v), va="center", color=INK, fontsize=13)
ax.set_yticks(range(len(bt)), bt.index)
ax.set(xlabel="orphan fragments assigned")
ax.set_title(f"{e5['assigned']} assigned · {e5['abstained']} left unassigned (gap below "
             f"{rep['E2_abstention']['margin']:.3f})", loc="left", color=INK2, fontsize=13)
save(fig, "orphans_by_tradition")

# 4. CTH 701 per-subgroup recall
rc = pd.Series(rep["E3_cth701_subgroups"]["both"]["recall_by_class"]).sort_index(ascending=False)
fig, ax = plt.subplots(figsize=(8, 4.8))
ax.grid(axis="x", color=GRID, lw=1)
ax.barh(range(len(rc)), rc.values, height=0.55, color=SERIES["words"], zorder=2)
for i, v in enumerate(rc.values):
    ax.text(v + 0.01, i, f"{v:.0%}", va="center", color=INK, fontsize=13)
ax.set_yticks(range(len(rc)), [f"701.{s}" for s in rc.index])
ax.set(xlim=(0, 1.1), xlabel="share recovered (leave-one-out)")
save(fig, "cth701_subgroups")
print("figures in", OUT)
