"""Slide figures from a results directory: python make_figures.py results/tlhdig03 ../img/orphans"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
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


def contested_plot(e10, name):
    """E10b: lead of each tradition for the pooled contested texts against random unassigned rituals."""
    tb = pd.DataFrame(e10["E10b"]["table"]).sort_values("lead_over_best_other")
    claim = e10["contested"]["claim"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.grid(axis="x", color=GRID, lw=1)
    for i, (_, r) in enumerate(tb.iterrows()):
        ax.plot([r.null_q05, r.null_q95], [i, i], color=GRID, lw=8, solid_capstyle="round", zorder=1)
        col = SERIES["signs"] if r.tradition == claim else SERIES["words"]
        ax.plot(r.lead_over_best_other, i, "o", ms=12, color=col, mec=SURF, mew=2, zorder=3)
    ax.axvline(0, color=INK2, lw=1.2)
    ax.set_yticks(range(len(tb)), [f"{t}  (claimed)" if t == claim else t for t in tb.tradition])
    ax.set(xlabel="lead over the best other tradition (cosine)")
    ax.set_title("grey: 90% range for random sets of unassigned rituals of the same size", loc="left", color=INK2, fontsize=12)
    save(fig, name)


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
REF_NAME = {"literature": "Literature-defined\ntraditions"}.get(rep.get("groups"), "Historical groups\n(Table 3 + rituals)")
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

# 5. E9 open set: texts of known outside genres, cut to 10-word windows
if (RES / "E9_report.json").exists():
    e9 = json.loads((RES / "E9_report.json").read_text())["by_k"]["10"]
    refw = e9.pop("reference")
    e9.pop("fit_floor")
    g = pd.DataFrame(e9).T.sort_values("gate_sent_outside")
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.grid(axis="x", color=GRID, lw=1)
    for i, (name, r) in enumerate(g.iterrows()):
        ax.plot([r.placed, r.gate_sent_outside], [i, i], color=GRID, lw=3, zorder=1)
        ax.plot(r.placed, i, "o", ms=11, color=SERIES["signs"], mec=SURF, mew=2, zorder=3)
        ax.plot(r.gate_sent_outside, i, "o", ms=11, color=SERIES["words"], mec=SURF, mew=2, zorder=3)
    ax.axvline(refw["gate_sent_outside"], color=INK2, lw=1.5, ls="--")
    ax.text(refw["gate_sent_outside"] + 0.01, -0.85, f"reference texts sent away: {refw['gate_sent_outside']:.0%}",
            color=INK2, fontsize=11)
    ax.set_yticks(range(len(g)), g.index)
    ax.set(xlim=(0, 1), ylim=(-1.1, len(g) - 0.5), xlabel="share of 10-word windows")
    ax.plot([], [], "o", ms=10, color=SERIES["signs"], label="wrongly placed in a tradition (margin rule)")
    ax.plot([], [], "o", ms=10, color=SERIES["words"], label="recognised as outside (genre gate)")
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.4, 1.0), ncol=2, fontsize=12)
    save(fig, "openset")

# 6. E10a leave one composition out, by tradition
if (RES / "E10_report.json").exists():
    e10 = json.loads((RES / "E10_report.json").read_text())
    bt = pd.DataFrame(e10["E10a"]["by_tradition"]).T
    bt["share"] = bt.correct / bt.compositions
    bt = bt.sort_values(["share", "compositions"])
    fig, ax = plt.subplots(figsize=(11, 5.6))
    ax.grid(axis="x", color=GRID, lw=1)
    ax.barh(range(len(bt)), bt.compositions, height=0.6, color=GRID, zorder=2, label="compositions")
    ax.barh(range(len(bt)), bt.correct, height=0.6, color=SERIES["words"], zorder=3,
            label="placed in their scholarly tradition")
    for i, (n, r) in enumerate(bt.iterrows()):
        ax.text(r.compositions + 0.3, i, f"{int(r.correct)} of {int(r.compositions)}", va="center", color=INK, fontsize=12)
    ax.set_yticks(range(len(bt)), bt.index)
    ax.set(xlabel="compositions (CTH numbers), each held out whole",
           xlim=(0, bt.compositions.max() * 1.18))
    ax.legend(frameon=False, loc="lower right", fontsize=12)
    save(fig, "leave_composition_out")

    contested_plot(e10, "contested_fit")

# 8. E11 what a placement rests on: similarity (what all traditions share counts) vs decision (it cancels)
if (RES / "E11_report.json").exists():
    e11 = json.loads((RES / "E11_report.json").read_text())
    CAT6 = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]  # palette slots 1-6, fixed order
    rows = [("similarity to its tradition", e11["E11a"]["similarity_all_correct"]),
            ("decision: lead over runner-up", e11["E11a"]["all_correct"])]
    fig, axes = plt.subplots(1, 2, figsize=(15, 4.8), sharey=True)
    for ax, key, title in ((axes[0], "by_layer", "layer"), (axes[1], "by_category", "word category")):
        names = list(rows[0][1][key])
        for i, (lab, r) in enumerate(rows):
            left = 0.0
            for j, n in enumerate(names):
                v = max(r[key][n], 0)
                ax.barh(i, v, left=left, height=0.55, color=CAT6[j], edgecolor=SURF, linewidth=2,
                        label=n if i == 0 else None)
                if v >= 0.08:
                    ax.text(left + v / 2, i, f"{v:.0%}", ha="center", va="center", color=SURF, fontsize=12, weight="bold")
                left += v
        ax.set_yticks(range(len(rows)), [r[0] for r in rows])
        ax.set(xlim=(0, 1.0), xlabel=f"share, by {title}")
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=11, columnspacing=1.0, handlelength=1.2)
    save(fig, "decision_shares")

    # 9. E11d: placements resting mostly on common features are less often right
    d = pd.DataFrame(e11["E11d"]).T
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.grid(axis="y", color=GRID, lw=1)
    x = range(len(d))
    for off, col, c, lab in ((-0.18, SERIES["words"], "precision_rest", "rest of the placed windows"),
                             (0.18, SERIES["signs"], "precision_mostly_common",
                              "placed mostly (> 50%) on common features")):
        ax.bar([i + off for i in x], d[c].astype(float), width=0.34, color=col, zorder=2, label=lab)
        for i, v in zip(x, d[c].astype(float)):
            ax.text(i + off, v + 0.015, f"{v:.0%}", ha="center", color=INK, fontsize=12)
    ax.set_xticks(list(x), [f"{k} words" for k in d.index])
    ax.set(ylim=(0, 1), ylabel="placed windows that are right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=12)
    save(fig, "common_features")
# 10. the same test for Tunnawiya's rituals (CTH 409) against the Luwian rituals of Puriyanni and Kuwattalla
if (RES / "tunnawiya" / "E10_report.json").exists():
    contested_plot(json.loads((RES / "tunnawiya" / "E10_report.json").read_text()), "contested_fit_tunnawiya")
print("figures in", OUT)
