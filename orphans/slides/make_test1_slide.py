"""Write the Mainz deck slide "test1" (leave one manuscript out) from results/<run>/report.json.
Usage: python3 slides/make_test1_slide.py results/tlhdig03_literature_C_filled results/tlhdig03_literature_A_filled > slides/test1.html"""
import json, sys
from pathlib import Path

SHORT = {"Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamian", "Mixed (Hurrian, Syrian, Luwian)": "Mixed",
         "Luwian rituals (Puriyanni, Kuwattalla)": "Luwian rituals", "Arzawa / western rituals": "Arzawa",
         "Luwian festivals (Ištanuwa, Lallupiya)": "Luwian festivals",
         "Kizzuwatna–Lower Land (Hurrian)": "Kizzuwatna–Lower Land"}
P = "font-family:'Public Sans', Arial, sans-serif; font-size:48px; line-height:1.1;"
main, comp = (json.loads((Path(a) / "report.json").read_text())["E1_historical"]["both"] for a in sys.argv[1:3])
rows = sorted(main["recall_by_class"].items(), key=lambda x: -x[1])
out = []
for t, v in rows:
    hi = t.startswith("Syro-Mesopotamia")
    lab = f'font-weight:600; {P} text-align:right; white-space:nowrap; color:#8a2c12' if hi else f'{P} text-align:right; white-space:nowrap; color:#2b1a10'
    out.append(f'''      <div style="display:flex; flex-direction:row; gap:20px; align-items:center">
        <p style="width:580px; {lab}">{SHORT.get(t, t)}</p>
        <div style="width:{round(v * 560)}px; height:36px; display:flex; flex-direction:column; background:{'#8a2c12' if hi else '#a4633f'}; border-radius:4px">
        </div>
        <p style="{P} color:#2b1a10">{round(v * 100)}%</p>
      </div>''')
recall = "; ".join(f"{SHORT.get(t, t)} {v:.3f}" for t, v in rows)
print(f'''<section id="test1" style="background-color:#e4d3b4; background-image:radial-gradient(ellipse at 30% 15%, #f2e4c8 0%, #e4d3b4 55%, #d7c29d 100%)">
  <p id="e2-16hnb24" style="position:absolute; bottom:36px; left:112px; width:1696px; font-family:'Public Sans', Arial, sans-serif; font-size:24px; color:#6f5842">Orphans and Archetypes · Mainz, 18 November 2026</p>
  <h2 id="pb4e56ee1ddd8r0-93ab0e8e" style="position:absolute; top:60px; left:112px; width:1696px; padding:0 0 10px; font-family:Fraunces, Georgia, serif; font-size:80px; font-weight:600; line-height:1.05; color:#2b1a10; border-bottom:5px solid #8a2c12">Test 1: hide a manuscript, then find it</h2>
  <div id="pb4e56ee1ddd8r2-93ab0e8e" style="position:absolute; top:344px; left:112px; width:1696px; height:650px; display:flex; flex-direction:row; gap:40px">
    <div style="display:flex; flex-direction:column; gap:14px">
{chr(10).join(out)}
    </div>
    <div style="display:flex; flex-direction:column; gap:28px; justify-content:end; flex:1">
      <p style="font-family:'Public Sans', Arial, sans-serif; font-size:48px; line-height:1.2; color:#4e3a2a">Only signs on the tablet count (with restorations: {round(comp["acc"] * 100)}%).</p>
      <p style="font-family:'Public Sans', Arial, sans-serif; font-size:48px; line-height:1.2; color:#4e3a2a">Unanalysed words: same spelling elsewhere, or <i>eDiAna</i> (Luwian).</p>
    </div>
  </div>
  <p id="pb4e56ee1ddd8r1_0-93ab0e8e" style="position:absolute; top:184px; left:128px; width:210.88px; height:143.45px; font-family:Fraunces, Georgia, serif; font-size:120px; font-weight:600; line-height:1; color:#8a2c12">{round(main["acc"] * 100)}%</p>
  <p id="pb4e56ee1ddd8r1_1-93ab0e8e" style="position:absolute; top:180px; left:364.77px; width:1444.23px; height:129.99px; font-family:'Public Sans', Arial, sans-serif; font-size:52px; line-height:1.25; color:#2b1a10">of {main["n"]:,} manuscripts can be placed in a tradition when each is hidden in turn (guessing the largest tradition: {round(main["majority"] * 100)}%).</p>
  <aside>Leave one manuscript out, 10 traditions, manuscripts with enough words on the tablet (without restorations, results/{Path(sys.argv[1]).name}/report.json E1, both words and spellings; slide written by slides/make_test1_slide.py). Accuracy {main["acc"]:.3f} on {main["n"]} manuscripts; majority baseline {main["majority"]:.3f}; shuffled labels {main["null_mean"]:.3f} (p = {main["p"]}). With restorations counted: {comp["acc"]:.3f} on {comp["n"]} manuscripts. Per tradition: {recall}. Highlighted: Syro-Mesopotamian, the tradition KBo 44.52 will be placed in. Words that TLHdig 0.3 leaves without an analysis take the analysis of the same spelling elsewhere in TLHdig (fill_lemmas.py); Cuneiform Luwian words take their lemma from eDiAna (ediana_cluwian.py). This step lets the Luwian rituals of Puriyanni and Kuwattalla (CTH 758–763) enter the test: 57 reference manuscripts instead of 10.</aside>
</section>''')
