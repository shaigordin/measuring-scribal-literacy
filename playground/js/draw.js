// Shared presentation: tradition order, colours, the tradition wheel, the similarity rose
// and the word butterfly. No model code here; see model.js.

// Neighbours on the wheel are related groups: the Anatolian festival layers (Hattian, Palaic,
// Luwian, Ḫuwaššanna), then the Hurrian festival groups, then the ritual traditions
// (Kizzuwatna, the Lower Land Luwian rituals, Arzawa).
export const RING = [
  "Hattian cult layer",
  "Palaic festivals",
  "Luwian festivals (Ištanuwa, Lallupiya)",
  "Ḫuwaššanna festivals",
  "Mixed (Hurrian, Syrian, Luwian)",
  "Syro-Mesopotamia (Hurrian)",
  "Kizzuwatna–Lower Land (Hurrian)",
  "Kizzuwatna rituals",
  "Luwian rituals (Puriyanni, Kuwattalla)",
  "Arzawa / western rituals",
];
export const SHORT = {
  "Hattian cult layer": "Hattian",
  "Palaic festivals": "Palaic fest.",
  "Luwian festivals (Ištanuwa, Lallupiya)": "Luwian fest.",
  "Ḫuwaššanna festivals": "Ḫuwaššanna",
  "Mixed (Hurrian, Syrian, Luwian)": "Mixed",
  "Syro-Mesopotamia (Hurrian)": "Syro-Mesopotamia",
  "Kizzuwatna–Lower Land (Hurrian)": "Kizzuwatna–Lower Land",
  "Kizzuwatna rituals": "Kizzuwatna rit.",
  "Arzawa / western rituals": "Arzawa / western",
  "Luwian rituals (Puriyanni, Kuwattalla)": "Luwian rit.",
};
export const colorVar = lab => `var(--series-${RING.indexOf(lab) + 1})`;
const angle = lab => -Math.PI / 2 + (2 * Math.PI * RING.indexOf(lab)) / RING.length;

// Barycentric placement in the tradition wheel: softmax-weighted average of corner positions.
export const TAU = 0.02;
export function hexPos(s, labs, R) {
  const mx = Math.max(...s);
  let x = 0, y = 0, z = 0;
  labs.forEach((lab, i) => {
    const a = angle(lab);
    const w = Math.exp((s[i] - mx) / TAU);
    x += w * Math.cos(a); y += w * Math.sin(a); z += w;
  });
  return [(R * x) / z, (R * y) / z];
}
export function corner(lab, R) {
  const a = angle(lab);
  return [R * Math.cos(a), R * Math.sin(a)];
}

// ---------- signature glyphs ----------
// Similarity rose: one wedge per tradition, at the same angle as its corner of the wheel.
// Radius is sqrt(score / ROSE_MAX), so wedge area tracks the score and roses are
// comparable across fragments. A dashed ring marks a fragment the model abstains on.
export const ROSE_MAX = 0.5;
export function roseSVG(s, labs, { size = 120, assigned = null, title = "" } = {}) {
  const R = size / 2 - 4, top = labs[s.indexOf(Math.max(...s))];
  const pt = (a, r) => `${(r * Math.cos(a)).toFixed(2)},${(r * Math.sin(a)).toFixed(2)}`;
  let out = `<svg viewBox="${-size / 2} ${-size / 2} ${size} ${size}" width="${size}" height="${size}" role="img" aria-label="${title || "similarity rose"}">`;
  for (const g of [0.1, 0.2, 0.3, 0.4])
    out += `<circle r="${(R * Math.sqrt(g / ROSE_MAX)).toFixed(2)}" fill="none" stroke="var(--grid)" stroke-width="1"/>`;
  labs.forEach((lab, i) => {
    const mid = angle(lab);
    const r = R * Math.sqrt(Math.min(Math.max(s[i], 0), ROSE_MAX) / ROSE_MAX);
    const a0 = mid - Math.PI / RING.length, a1 = mid + Math.PI / RING.length;
    out += `<path d="M0,0 L${pt(a0, r)} A${r.toFixed(2)},${r.toFixed(2)} 0 0 1 ${pt(a1, r)} Z" fill="${colorVar(lab)}"
      fill-opacity="${lab === top ? 1 : 0.4}" stroke="var(--surface-1)" stroke-width="1.5"><title>${lab}: ${s[i].toFixed(3)}</title></path>`;
  });
  if (!assigned) out += `<circle r="${R + 2}" fill="none" stroke="var(--text-muted)" stroke-width="1.2" stroke-dasharray="3 3"/>`;
  return out + "</svg>";
}

// Word butterfly: tf-idf of each word in A (left) and B (right), shared words bold.
export function butterflyRows(A, B, sort = "prod", n = 30) {
  const keys = new Set([...A.keys(), ...B.keys()]);
  const rows = [...keys].map(j => ({ j, a: A.get(j) || 0, b: B.get(j) || 0 }));
  const key = { prod: r => r.a * r.b + 1e-6 * (r.a + r.b), a: r => r.a, b: r => r.b, diff: r => Math.abs(r.a - r.b) }[sort];
  return rows.sort((p, q) => key(q) - key(p)).slice(0, n);
}
export function butterflyHTML(rows, vocab, colA, colB, { sel = null, heads = ["A", "B"] } = {}) {
  const mx = Math.max(...rows.map(r => Math.max(r.a, r.b)), 1e-6);
  return `<span></span><span class="head" style="text-align:right">${heads[0]}</span><span></span><span class="head">${heads[1]}</span><span></span>` +
    rows.map(r => `<span class="num">${r.a ? r.a.toFixed(3) : ""}</span>
      <span class="l"><span class="bar" style="width:${(100 * r.a) / mx}%;background:${colA}"></span></span>
      <span class="w translit ${r.a && r.b ? "shared" : ""} ${vocab[r.j] === sel ? "sel" : ""}" data-w="${vocab[r.j]}" title="${vocab[r.j]}">${vocab[r.j]}</span>
      <span class="r"><span class="bar" style="width:${(100 * r.b) / mx}%;background:${colB}"></span></span>
      <span class="num">${r.b ? r.b.toFixed(3) : ""}</span>`).join("");
}
