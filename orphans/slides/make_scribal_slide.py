"""Write the Mainz deck slide "scribal" (each tradition's scribal profile, heat map of z-scores)
from results/<run>/E7_report.json (E7b) and the reference counts in case/case_KBo_44_52.json.
Usage: python3 slides/make_scribal_slide.py results/tlhdig03_literature_C_filled > slides/scribal.html"""
import json, sys
from pathlib import Path

ORDER = ["Hattian cult layer", "Palaic festivals", "Ḫuwaššanna festivals", "Luwian festivals (Ištanuwa, Lallupiya)",
         "Kizzuwatna rituals", "Kizzuwatna–Lower Land (Hurrian)", "Syro-Mesopotamia (Hurrian)",
         "Mixed (Hurrian, Syrian, Luwian)", "Luwian rituals (Puriyanni, Kuwattalla)", "Arzawa / western rituals"]
SHORT = {"Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamian", "Mixed (Hurrian, Syrian, Luwian)": "Mixed Hurrian",
         "Luwian rituals (Puriyanni, Kuwattalla)": "Luwian rituals", "Arzawa / western rituals": "Arzawa",
         "Luwian festivals (Ištanuwa, Lallupiya)": "Luwian festivals",
         "Kizzuwatna–Lower Land (Hurrian)": "Kizzuwatna–Lower Land"}
COLS = [("logogram_share", "logograms"), ("akkadogram_share", "Akkadograms"), ("determinative_rate", "determinatives"),
        ("cvc_share", "CVC signs"), ("plene_rate", "plene-writing"), ("complement_rate", "complements")]
MID, BLUE, RED, FULL = (0xF1, 0xE4, 0xC8), (0x1F, 0x4E, 0x8C), (0x8A, 0x2C, 0x12), 0.9

def colour(z):
    t = min(abs(z) / FULL, 1.0); end = BLUE if z > 0 else RED
    return "#" + "".join(f"{round(a + (b - a) * t):02x}" for a, b in zip(MID, end))

run = Path(sys.argv[1])
z = json.loads((run / "E7_report.json").read_text())["E7b_index_profile_z"]
n = json.loads((run / "case" / "case_KBo_44_52.json").read_text())["ref_counts"]
parts = [f'<text x="{526 + 212 * i:.1f}" y="46" text-anchor="middle" font-size="29" font-weight="600" fill="#6f5842">{lab}</text>'
         for i, (_, lab) in enumerate(COLS)]
for r, t in enumerate(ORDER):
    y = 67 + 56 * r
    parts.append(f'<text x="400" y="{y + 37:.1f}" text-anchor="end" font-size="34" fill="#2b1a10">{SHORT.get(t, t)}</text>')
    for i, (k, _) in enumerate(COLS):
        v = z[t][k]; x = 423 + 212 * i
        parts.append(f'<rect x="{x}" y="{y}" width="206" height="50" rx="6" fill="{colour(v)}"/>'
                     f'<text x="{x + 103:.1f}" y="{y + 37:.1f}" text-anchor="middle" font-size="34" '
                     f'fill="{"#ffffff" if abs(v) >= 0.55 else "#2b1a10"}">{("0.00" if round(v, 2) == 0 else f"{v:+.2f}")}</text>')
counts = "; ".join(f"{SHORT.get(t, t)} ({n[t]} MSS)" for t in ORDER)
print(f'''<section id="scribal" style="display:flex; flex-direction:column; gap:20px; padding:60px 112px 110px; background-color:#e4d3b4; background-image:radial-gradient(ellipse at 30% 15%, #f2e4c8 0%, #e4d3b4 55%, #d7c29d 100%)">
  <h2 style="padding:0 0 10px; font-family:Fraunces, Georgia, serif; font-size:80px; font-weight:600; line-height:1.05; color:#2b1a10; border-bottom:5px solid #8a2c12">Each tradition’s scribal profile</h2>
  <svg viewBox="0 0 1696 624" width="1696" height="624" xmlns="http://www.w3.org/2000/svg" style="font-family:'Public Sans', Arial, sans-serif">{"".join(parts)}</svg>
  <p style="font-family:'Public Sans', Arial, sans-serif; font-size:48px; line-height:1.25; color:#4e3a2a"><span style="color:#1f4e8c; font-weight:600">blue</span> more, <span style="color:#8a2c12; font-weight:600">red</span> less than the average manuscript<br>The differences are small</p>
  <p style="position:absolute; bottom:36px; left:112px; width:1696px; font-family:'Public Sans', Arial, sans-serif; font-size:24px; color:#6f5842">Orphans and Archetypes · Mainz, 18 November 2026</p>
  <aside>Without restorations, run_profiles.py E7b (results/{run.name}/E7_report.json E7b_index_profile_z; slide written by slides/make_scribal_slide.py): mean z-score of each per-text rate within a tradition, against all reference manuscripts (0 = the average manuscript; units are standard deviations). Colour: blue = above average, red = below, full colour at |z| ≥ 0.9. {counts}. The Hattian layer writes fewer logograms and more plene: that may reflect date (Old Hittite manuscripts) as much as tradition; the Palaic festivals add many phonetic complements; Ḫuwaššanna uses more Akkadograms and determinatives; the Luwian rituals fewer Akkadograms and determinatives; the Kizzuwatna rituals fewer determinatives. The rate of ú (not shown) also varies little.</aside>
</section>''')
