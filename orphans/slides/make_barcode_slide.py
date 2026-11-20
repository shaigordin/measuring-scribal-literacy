"""Write the Mainz deck slide "barcode" (KBo 44.52 against ten archetypes) from
results/<run>/case/barcode_KBo_44_52.json (run_barcode.py).
Usage: python3 slides/make_barcode_slide.py results/tlhdig03_literature_C_filled > slides/barcode.html"""
import json, sys
from pathlib import Path

SHORT = {"Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamian", "Mixed (Hurrian, Syrian, Luwian)": "Mixed Hurrian",
         "Luwian rituals (Puriyanni, Kuwattalla)": "Luwian rituals", "Arzawa / western rituals": "Arzawa",
         "Luwian festivals (Ištanuwa, Lallupiya)": "Luwian festivals",
         "Kizzuwatna–Lower Land (Hurrian)": "Kizzuwatna–Lower Land"}
FONT = "font-family:'Public Sans', Arial, sans-serif; font-size:48px; line-height:1.1;"

def bars(cells, kind):
    return "".join(f"M{i*5} 0h4v40h-4z" for i, c in enumerate(cells) if c == kind)

def row(r, first):
    name = SHORT.get(r["tradition"], r["tradition"])
    lab = (f'<p style="width:540px; flex:0 0 auto; {FONT} text-align:right; white-space:nowrap; '
           + ('font-weight:600; color:#8A2C12">' if first else 'color:#2B1A10">') + name + "</p>")
    svg = ('<svg width="1000" height="40" viewBox="0 0 1000 40" style="flex:0 0 auto"><rect width="1000" height="40" fill="#efe3c9"/>'
           f'<path d="{bars(r["cells"], "c")}" fill="#a58a5f"/><path d="{bars(r["cells"], "d")}" fill="#8a2c12"/></svg>')
    num = (f'<p style="{FONT} ' + ('font-weight:700; color:#8A2C12">' if first else 'color:#4E3A2A">')
           + str(r["distinctive"]) + "</p>")
    return f'<div style="display:flex; flex-direction:row; gap:24px; align-items:center">{lab}{svg}{num}</div>'

run = Path(sys.argv[1])
d = json.loads((run / "case" / "barcode_KBo_44_52.json").read_text())
rows = sorted(d["rows"], key=lambda r: -r["distinctive"])
core = len(rows[0]["cells"])
counts = "; ".join(f'{SHORT.get(r["tradition"], r["tradition"])} {r["distinctive"]} of {core}' for r in rows)
lead_terms = ", ".join(rows[0]["terms"][:8])
print(f'''<section id="barcode" style="display:flex; flex-direction:column; gap:24px; padding:60px 112px 110px; background-color:#e4d3b4; background-image:radial-gradient(ellipse at 30% 15%, #f2e4c8 0%, #e4d3b4 55%, #d7c29d 100%)">
  <h2 style="padding:0 0 10px; font-family:Fraunces, Georgia, serif; font-size:80px; font-weight:600; line-height:1.05; color:#2b1a10; border-bottom:5px solid #8a2c12">KBo 44.52 against ten archetypes</h2>
  <div style="display:flex; flex-direction:column; gap:8px">{"".join(row(r, i == 0) for i, r in enumerate(rows))}</div>
  <div style="display:flex; flex-direction:row; gap:40px; align-items:center; padding-left:564px"><div style="display:flex; flex-direction:row; gap:12px; align-items:center"><div style="width:32px; height:32px; background:#8a2c12; border-radius:4px"></div><p style="font-family:'Public Sans', Arial, sans-serif; font-size:44px; line-height:1.25; color:#4E3A2A; white-space:nowrap">KBo 44.52 has it</p></div><div style="display:flex; flex-direction:row; gap:12px; align-items:center"><div style="width:32px; height:32px; background:#a58a5f; border-radius:4px"></div><p style="font-family:'Public Sans', Arial, sans-serif; font-size:44px; line-height:1.25; color:#4E3A2A; white-space:nowrap">has it, but common everywhere</p></div></div>
  <p style="position:absolute; bottom:36px; left:112px; width:1696px; font-family:'Public Sans', Arial, sans-serif; font-size:24px; color:#6f5842">Orphans and Archetypes · Mainz, 18 November 2026</p>
  <aside>Each bar: one tradition's archetype, its {core} most characteristic features (largest weights in the tradition's average profile), most characteristic on the left. A cell is filled when KBo 44.52 has the feature: dark red if it is distinctive, light brown if it is common (in at least a quarter of all reference manuscripts, like nu). The number is the count of distinctive matches. run_barcode.py, without restorations ({run.name}/case/barcode_KBo_44_52.json; slide written by slides/make_barcode_slide.py): {counts}. The Syro-Mesopotamian archetype lights up from its left end: {lead_terms} (features with § are sign sequences inside words). Same placement as the tug of war: lead {d["margin"]:.3f}.</aside>
</section>''')
