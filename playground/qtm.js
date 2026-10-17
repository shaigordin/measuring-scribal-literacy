// Client-side port of orphans/qtm: tokenisation, tf-idf, nearest-centroid scoring.
// Mirrors qtm/corpus.py (signs), qtm/features.py ("both" space) and qtm/assign.py.

const EDIT = /[\[\]⸢⸣()?!~′'<>«»#*]/g;
const LONE_X = /(?<![\p{L}\p{N}_])x(?![\p{L}\p{N}_])/gu;
const SIGN_SPLIT = /[-.\s{}+˽]+/;
const DIGITS = /^[\p{Nd}²³¹⁰-₟]+$/u;
const SUB = { 0: "₀", 1: "₁", 2: "₂", 3: "₃", 4: "₄", 5: "₅", 6: "₆", 7: "₇", 8: "₈", 9: "₉" };
const ACUTE = { a: "á", e: "é", i: "í", u: "ú", A: "Á", E: "É", I: "Í", U: "Ú" };
const GRAVE = { a: "à", e: "è", i: "ì", u: "ù", A: "À", E: "È", I: "Ì", U: "Ù" };

// ASCII conveniences: sz/š, s,/ṣ, t,/ṭ, h/ḫ, u2/ú, u3/ù, ku4/ku₄
function asciiSign(s) {
  s = s.replace(/sz/g, "š").replace(/SZ|Sz/g, "Š").replace(/s,/g, "ṣ").replace(/S,/g, "Ṣ")
       .replace(/t,/g, "ṭ").replace(/T,/g, "Ṭ").replace(/h/g, "ḫ").replace(/H/g, "Ḫ");
  const m = s.match(/^(.*?)(\d+)$/);
  if (!m || !m[1]) return s;
  const [, base, n] = m;
  const vowels = [...base].filter(c => ACUTE[c]);
  if ((n === "2" || n === "3") && vowels.length === 1) {
    const v = vowels[0], map = n === "2" ? ACUTE : GRAVE;
    return base.replace(v, map[v]);
  }
  return base + [...n].map(d => SUB[d]).join("");
}

export function normaliseAscii(word) {
  // keep separators, convert each sign
  return word.split(/([-.{}+])/).map((p, i) => (i % 2 ? p : asciiSign(p))).join("");
}

export function signs(translit) {
  const t = translit.replace(EDIT, "").replace(LONE_X, "");
  return t.split(SIGN_SPLIT).filter(s => s && s !== "x" && !DIGITS.test(s));
}

function clean(w) { return w.replace(EDIT, "").trim(); }

function illegible(w) {
  return /%|…|\.\.\./.test(w) || signs(w).length === 0;
}

// Parse pasted transliteration: whitespace separates words. Words that are
// partly illegible are dropped, as the corpus pipeline drops them.
export function parse(text, model) {
  const words = [], dropped = [];
  for (let raw of text.split(/\s+/).filter(Boolean)) {
    if (/^\d+[′'´]*\.?$/.test(raw) || /^(obv|rev|lk|rs|vs)\.?$/i.test(raw)) continue; // line numbers
    if (illegible(raw)) { dropped.push(raw); continue; }
    let w = clean(raw);
    if (!model.lookup[w] && !model.index.has(w)) {
      const a = normaliseAscii(w);
      if (model.lookup[a] || model.index.has(a) || a !== w) w = a;
    }
    const form = model.lookup[w] || (model.index.has(w) ? w : null);
    words.push({ raw, translit: w, word: form, signs: signs(w) });
  }
  return { words, dropped };
}

export function features(parsed) {
  const toks = [];
  for (const w of parsed.words) if (w.word) toks.push(w.word);
  for (const w of parsed.words) {
    const sg = w.signs;
    for (let k = 1; k <= 3; k++)
      for (let i = 0; i + k <= sg.length; i++) toks.push("§" + sg.slice(i, i + k).join("·"));
  }
  return toks;
}

// TfidfVectorizer(sublinear_tf=True, norm="l2") on a fixed vocabulary
export function tfidf(toks, index, idf) {
  const tf = new Map();
  for (const t of toks) { const j = index.get(t); if (j !== undefined) tf.set(j, (tf.get(j) || 0) + 1); }
  const v = new Map();
  let n2 = 0;
  for (const [j, c] of tf) { const x = (1 + Math.log(c)) * idf[j]; v.set(j, x); n2 += x * x; }
  const n = Math.sqrt(n2) || 1;
  for (const [j, x] of v) v.set(j, x / n);
  return v;
}

export function denseCentroids(model) {
  return model.centroids.map(([idx, val]) => {
    const m = new Map();
    idx.forEach((j, i) => m.set(j, val[i]));
    return m;
  });
}

export function score(vec, cents) {
  return cents.map(c => { let s = 0; for (const [j, x] of vec) { const y = c.get(j); if (y) s += x * y; } return s; });
}

// per-feature contribution to the cosine with one centroid
export function contributions(vec, cent, vocab) {
  const out = [];
  for (const [j, x] of vec) { const y = cent.get(j); if (y) out.push({ term: vocab[j], value: x * y, x, y }); }
  return out.sort((a, b) => b.value - a.value);
}

export function assign(s, labs, margin) {
  const order = s.map((v, i) => i).sort((a, b) => s[b] - s[a]);
  const gap = s[order[0]] - s[order[1]];
  return { top: labs[order[0]], topScore: s[order[0]], runnerUp: labs[order[1]], gap,
           assigned: gap >= margin ? labs[order[0]] : null };
}

export async function loadModel(base = "data") {
  const model = await (await fetch(`${base}/model.json`)).json();
  model.index = new Map(model.vocab.map((t, i) => [t, i]));
  model.cents = denseCentroids(model);
  const gate = await (await fetch(`${base}/gate.json`)).json();
  gate.index = new Map(gate.vocab.map((t, i) => [t, i]));
  gate.cents = denseCentroids(gate);
  model.gate = gate;
  return model;
}

// E9 open-set check. `lowFit`: the best similarity is below what 95% of reference fragments of
// this size reach. `outside`: with outside genres (myths, oracles, treaties ...) added as classes,
// the nearest class is one of them by at least the abstention margin.
export function fitFloor(n, floors) {
  const ks = Object.keys(floors).map(Number).sort((a, b) => a - b);
  const k = ks.filter(k => k <= n).pop() ?? ks[0];
  return floors[k];
}
export function openSet(toks, n, topScore, model) {
  const g = model.gate, os = model.openset;
  const s = score(tfidf(toks, g.index, g.idf), g.cents);
  const a = assign(s, g.classes, 0);
  const floor = fitFloor(n, os.floors);
  const outside = os.outside.includes(a.top) && Math.round(a.gap * 1e4) / 1e4 >= model.margin ? a.top : null;
  return { floor, lowFit: topScore < floor, outside, gateTop: a.top, gateGap: a.gap };
}

export function scoreText(text, model) {
  const parsed = parse(text, model);
  const toks = features(parsed);
  const vec = tfidf(toks, model.index, model.idf);
  const s = score(vec, model.cents);
  const a = assign(s, model.traditions, model.margin);
  const n = parsed.words.length;
  return { parsed, vec, s, ...a, open: openSet(toks, n, a.topScore, model) };
}

// --- shared presentation: tradition order around the wheel, and colours ---
// Neighbours on the wheel are related groups: the Anatolian festival layers (Hattian, Palaic,
// Luwian, Ḫuwaššanna), then the Hurrian festival groups, then the ritual traditions.
export const RING = [
  "Hattian cult layer",
  "Palaic festivals",
  "Luwian festivals (Ištanuwa, Lallupiya)",
  "Ḫuwaššanna festivals",
  "Mixed (Hurrian, Syrian, Luwian)",
  "Syro-Mesopotamia (Hurrian)",
  "Kizzuwatna–Lower Land (Hurrian)",
  "Kizzuwatna rituals",
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
