// Place a fragment: score pasted text, explain the placement, draw the wheel, rose and butterfly.
import * as Q from "./model.js";
import * as D from "./draw.js";
import * as P from "./portal.js";

const $ = id => document.getElementById(id);
const model = await Q.loadModel();
const corpus = await (await fetch("data/corpus.json")).json();
let W = null;
const getWords = async () => {
  if (!W) { W = await (await fetch("data/words.json")).json(); W.index = new Map(W.vocab.map((t, i) => [t, i])); }
  return W;
};
const labs = model.traditions;
const byId = new Map(corpus.map(c => [c.id, c]));
const R = 200;
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs = {}, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  parent?.appendChild(e);
  return e;
};
const fmt = x => x.toFixed(3);
const tip = $("tip");
function showTip(ev, html) {
  tip.innerHTML = html; tip.style.display = "block";
  const w = tip.offsetWidth, h = tip.offsetHeight;
  tip.style.left = Math.min(ev.clientX + 12, innerWidth - w - 8) + "px";
  tip.style.top = Math.min(ev.clientY + 12, innerHeight - h - 8) + "px";
}
const hideTip = () => (tip.style.display = "none");

// ---------- hexagon ----------
const svg = $("hex");
const gGrid = el("g", {}, svg), gRef = el("g", {}, svg), gOrph = el("g", {}, svg), gMe = el("g", {}, svg);
const pts = D.RING.map(l => D.corner(l, R));
el("polygon", { points: pts.map(p => p.join(",")).join(" "), fill: "none", stroke: "var(--border)", "stroke-width": 1.5 }, gGrid);
for (const p of pts) el("line", { x1: 0, y1: 0, x2: p[0], y2: p[1], stroke: "var(--grid)", "stroke-width": 1 }, gGrid);
for (const lab of D.RING) {
  const [x, y] = D.corner(lab, R + 16);
  const t = el("text", { x, y: y + (y > 10 ? 10 : y < -10 ? -2 : 4), "text-anchor": Math.abs(x) < 5 ? "middle" : x > 0 ? "start" : "end", class: "label-strong" }, gGrid);
  t.textContent = D.SHORT[lab];
  el("circle", { cx: D.corner(lab, R)[0], cy: D.corner(lab, R)[1], r: 5, fill: D.colorVar(lab) }, gGrid);
}
function dot(c, g, r, opacity) {
  const [x, y] = D.hexPos(c.s, labs, R);
  const lab = c.label || c.assigned;
  const d = el("circle", { cx: x, cy: y, r, fill: D.colorVar(lab), "fill-opacity": opacity, stroke: "var(--surface-1)", "stroke-width": 0.6 }, g);
  d.style.cursor = "pointer";
  d.addEventListener("mousemove", ev => showTip(ev,
    `<b>${c.id}</b> (CTH ${c.cth}, ${c.n} words)<br>${c.kind === "ref" ? "Reference: " + c.label : "Orphan placed in: " + c.assigned}`));
  d.addEventListener("mouseleave", hideTip);
  d.addEventListener("click", () => load(c.id));
}
for (const c of corpus) if (c.kind === "ref") dot(c, gRef, 2.6, 0.55);
for (const c of corpus) if (c.kind === "orphan" && c.assigned) dot(c, gOrph, 3.2, 0.9);
gOrph.style.display = "none";
$("showRef").onchange = e => (gRef.style.display = e.target.checked ? "" : "none");
$("showOrph").onchange = e => (gOrph.style.display = e.target.checked ? "" : "none");
$("legend").innerHTML = D.RING.map(l => `<span><span class="swatch" style="background:${D.colorVar(l)}"></span>${l}</span>`).join("");

// ---------- examples ----------
const orphans = corpus.filter(c => c.kind === "orphan");
const placed = orphans.filter(c => c.assigned).sort((a, b) => b.gap - a.gap);
const ex = $("examples");
const group = (label, items) => {
  const og = document.createElement("optgroup"); og.label = label;
  for (const c of items) og.append(new Option(`${c.id} (${c.n} words${c.outside ? ", outside: " + c.outside : c.assigned ? ", " + D.SHORT[c.assigned] : c.label ? ", " + D.SHORT[c.label] : ""})`, c.id));
  ex.append(og);
};
group("Orphans the model places confidently", placed.filter(c => !c.outside && !c.low_fit).slice(0, 8));
group("Orphans too close to call", orphans.filter(c => !c.assigned && !c.outside && !c.low_fit && c.n >= 20).slice(0, 6));
group("Orphans that fit no known tradition", orphans.filter(c => c.outside && c.n >= 15).slice(0, 6));
group("Reference manuscripts", D.RING.map(l => corpus.find(c => c.kind === "ref" && c.label === l && c.n > 60 && c.n < 200)).filter(Boolean));
ex.onchange = () => ex.value && load(ex.value);
$("random").onclick = () => load(orphans[Math.floor(Math.random() * orphans.length)].id);
$("clear").onclick = () => { $("input").value = ""; run(); };

// ---------- scoring ----------
// ---------- what the score rests on ----------
// short tags for the word categories of qtm/wordclass.py (CATEGORIES), in the same order
const CLS_ABBR = Object.fromEntries(model.categories.map(c => [c, {
  "Function words": "fn", "Verbs": "v", "Realia": "re", "Agents and deities": "ag", "Places": "pl",
  "Animals, body, nature": "nat", "Abstract nouns": "abs", "Adjectives": "adj", "Foreign words": "for", "Other words": "?",
}[c] ?? c.slice(0, 3).toLowerCase()]));
const drop = { classes: new Set(), layers: new Set() };
$("restLegend").innerHTML = model.layers.map((l, i) => `<span><span class="swatch sq" style="background:var(--layer-${i + 1})"></span>${l}</span>`).join("") +
  `<span><span class="tick-swatch"></span>same share in the tradition's manuscripts</span>` +
  `<span class="muted">Word tags: ${Object.entries(CLS_ABBR).map(([k, v]) => v + " " + k.toLowerCase()).join(", ")}; a dashed tag marks a class of low confidence (the TLHdig analyses disagree or are missing).</span>`;
$("dropRow").innerHTML = `<span class="muted">Leave out and rescore:</span>` +
  model.categories.map(c => `<label><input type="checkbox" data-c="${c}"> ${c.toLowerCase()}</label>`).join("") +
  model.layers.map((l, i) => `<label><input type="checkbox" data-l="${i}"> ${l.toLowerCase()}</label>`).join("");
for (const cb of $("dropRow").querySelectorAll("input")) cb.onchange = () => {
  const set = cb.dataset.c ? drop.classes : drop.layers, key = cb.dataset.c ?? +cb.dataset.l;
  cb.checked ? set.add(key) : set.delete(key);
  run(currentId);
};
let currentId;
let mode = "decision";
for (const rb of document.querySelectorAll("input[name=mode]")) rb.onchange = () => { mode = rb.value; run(currentId); };
const SUB = {
  decision: "Which words decide between the nearest tradition and the runner-up: the margin between the two scores, split by word class (after StBoT 73 Table 4, with realia split by meaning; from TLHdig's morphological analyses) and by layer: the word form itself, its syllabic spelling, or its logographic writing. Bars to the left pull toward the runner-up. Material every tradition shares, like nu, cancels out here. The tick marks the same share in that tradition's own correctly placed manuscripts. The words above are coloured by the tradition they pull toward.",
  similarity: "Each word's share of the similarity to the nearest tradition, by word class and layer. Much of any similarity is material all traditions share (nu, the signs a and i), so frequent function words look heavy here even when they decide nothing; switch to the first view to see what decides. The tick marks the same share in that tradition's own correctly placed manuscripts. The words above are shaded by their share.",
};
const E = model.e11, percent = x => Math.round(100 * x) + "%", range = ([a, b]) => `${Math.round(100 * a)}–${percent(b)}`;
function drawRest(r, at) {
  $("restSub").textContent = SUB[mode];
  if (!at.matrix.length || !(at.sum > 0)) { $("rest").replaceChildren(); $("commonNote").replaceChildren(); return; }
  const tot = at.sum, base = (mode === "decision" ? model.decisionBaseline : model.categoryBaseline)[r.top];
  const rows = model.categories.map((c, ci) => ({ c, parts: at.matrix[ci].map(v => v / tot), base: base[ci].reduce((a, b) => a + b, 0) }));
  const pos = x => x.parts.reduce((a, v) => a + Math.max(v, 0), 0), neg = x => x.parts.reduce((a, v) => a + Math.max(-v, 0), 0);
  const L = Math.max(...rows.map(x => Math.max(neg(x), -x.base, 0))), R = Math.max(...rows.map(x => Math.max(pos(x), x.base)), 0.05);
  const span = L + R, zero = (100 * L) / span, pc = v => (100 * v) / span;
  const layerTot = model.layers.map((_, l) => rows.reduce((a, x) => a + x.parts[l], 0));
  $("rest").innerHTML = rows.map(x => {
    let right = zero, left = zero;
    const segs = x.parts.map((v, l) => {
      const w = pc(Math.abs(v)), at0 = v >= 0 ? right : (left -= w);
      if (v >= 0) right += w;
      return `<span class="seg" style="left:${at0}%;width:${w}%;background:var(--layer-${l + 1})" title="${model.layers[l]}: ${(100 * v).toFixed(1)}%"></span>`;
    }).join("");
    const sum = x.parts.reduce((a, b) => a + b, 0);
    return `<span class="lab">${x.c}${drop.classes.has(x.c) ? ' <span class="muted">(left out)</span>' : ""}</span>
      <span class="track">${L > 0 ? `<span class="zero" style="left:${zero}%"></span>` : ""}${segs}<span class="tick" style="left:${zero + pc(x.base)}%" title="${r.top} manuscripts: ${(100 * x.base).toFixed(0)}%"></span></span>
      <span class="val">${(100 * sum).toFixed(0)}%</span>`;
  }).join("") +
  `<span class="lab muted">By layer</span><span class="small muted" style="grid-column: span 2">${model.layers.map((l, i) => `${l.toLowerCase()} ${(100 * layerTot[i]).toFixed(0)}%`).join(" · ")}</span>`;
  const cs = at.common / tot;
  $("commonNote").innerHTML = mode === "decision"
    ? `<b>${cs > 1 ? "More than all" : (100 * cs).toFixed(0) + "%"}</b> of the margin comes from common features (attested in at least a quarter of the reference manuscripts, like nu or the sign a). ` +
      (cs > 0.5 ? `<b>When more than half of a placement rests on them, it is right only ${range(E.precision_mostly_common)} of the time on test windows of ${E.windows[0]}–${E.windows.at(-1)} words, against ${range(E.precision_rest)} otherwise (experiment E11d); ${E.assigned_mostly_common} of the ${E.assigned_orphans} placed orphans are such cases.</b>` : `Across the correctly placed reference manuscripts that share is about ${percent(E.common_share_of_decision)}.`)
    : `<span class="muted">${(100 * cs).toFixed(0)}% of this similarity comes from common features (attested in at least a quarter of the reference manuscripts), against about ${percent(E.common_share_of_decision)} of the decision.</span>`;
}

let timer;
$("input").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(() => run(), 200); });

function run(fromId) {
  currentId = fromId;
  const text = $("input").value.trim();
  gMe.replaceChildren();
  if (!text) {
    $("verdict").textContent = "Waiting for text."; $("verdict").className = "verdict muted";
    for (const id of ["verdictSub", "bars", "chips", "parseInfo", "contrib", "barcode", "rose", "fly", "rest", "commonNote"]) $(id).replaceChildren();
    return;
  }
  const r = Q.scoreText(text, model, { dropClasses: [...drop.classes], dropLayers: [...drop.layers] });
  r.parsed.dropped = r.all.dropped;
  const known = r.all.words.filter(w => w.word).length;
  $("parseInfo").textContent = `${r.all.words.length} words read, ${known} in the model's vocabulary` +
    (r.parsed.dropped.length ? `, ${r.parsed.dropped.length} broken words ignored` : "") + (fromId ? ` · ${fromId}${byId.get(fromId) ? ", CTH " + byId.get(fromId).cth : ""} · ` : "");
  if (fromId) $("parseInfo").insertAdjacentHTML("beforeend", P.portalLinks(fromId, byId.get(fromId)?.cth));
  const weights = mode === "decision" && r.runnerUp ? Q.decisionWeights(r, model) : model.cents[labs.indexOf(r.top)];
  const at = r.vec.size ? Q.attribute(r, weights, model) : { perWord: [], matrix: [], sum: 0, common: 0 };
  const share = new Map(at.perWord.map(p => [p.word, p]));
  const wmax = Math.max(...at.perWord.map(p => Math.abs(p.total)), 1e-9), denom = at.sum || 1;
  const what = mode === "decision" ? "of the margin" : "of the score";
  $("chips").innerHTML = r.all.words.map(w => {
    const p = share.get(w), cls = Q.wordClass(w, model), [conf, rule] = Q.classConfidence(w, model);
    if (!p) return `<span class="chip translit drop" title="${cls}: left out">${w.translit}</span>`;
    const pct = (100 * p.total) / denom, f = v => `${((100 * v) / denom).toFixed(0)}%`;
    const toward = mode === "decision" ? (p.total >= 0 ? ` · pulls toward ${D.SHORT[r.top]}` : ` · pulls toward ${D.SHORT[r.runnerUp]}`) : "";
    const tip = `${cls} (class confidence ${conf}, ${rule.replaceAll("_", " ")})${w.word ? " · word form " + w.word : " · not in vocabulary"} · ${pct.toFixed(0)}% ${what}${toward}` +
      ` (form ${f(p.parts[0])}, syllabic ${f(p.parts[1])}, logographic ${f(p.parts[2])})`;
    const col = mode === "decision" ? D.colorVar(p.total >= 0 ? r.top : r.runnerUp) : "var(--accent)";
    return `<span class="chip translit ${w.word ? "" : "unk"}" title="${tip}" style="background:color-mix(in srgb, ${col} ${Math.round(70 * Math.abs(p.total) / wmax)}%, var(--surface-0))"><span class="cls ${conf === "low" ? "low" : ""}">${CLS_ABBR[cls]}</span>${w.translit}</span>`;
  }).join("") +
    r.parsed.dropped.map(w => `<span class="chip translit drop" title="ignored">${w}</span>`).join("");

  if (r.vec.size === 0) {
    $("verdict").textContent = "Nothing in this text matches the model's vocabulary."; $("verdict").className = "verdict muted";
    return;
  }
  const v = $("verdict");
  v.className = "verdict";
  const o = r.open, placedHere = r.assigned && !o.outside && !o.lowFit;
  v.innerHTML = o.outside
    ? `Outside the reference traditions <span class="muted">(closest genre: ${o.outside})</span>`
    : o.lowFit
      ? `Fits no known tradition <span class="muted">(nearest: ${r.top})</span>`
      : r.assigned
        ? `Placed in <b>${r.assigned}</b>`
        : `Too close to call <span class="muted">(nearest: ${r.top})</span>`;
  $("verdictSub").textContent = (o.outside
      ? `With other genres added as classes, the nearest class is ${o.outside}, by a margin of ${fmt(o.gateGap)}. `
      : o.lowFit ? `Its best similarity, ${fmt(r.topScore)}, is below ${fmt(o.floor)}, which 95% of reference fragments of this size reach. ` : "") +
    `Nearest tradition ${fmt(r.topScore)}, runner-up ${r.runnerUp} ${fmt(r.topScore - r.gap)}. Margin ${fmt(r.gap)} ${r.gap >= model.margin ? "clears" : "is below"} the abstention threshold of ${model.margin}.` +
    (r.parsed.words.length < 8 ? " Fragments under about 8 words are rarely placed reliably." : "") +
    (drop.classes.size || drop.layers.size ? ` Scored without: ${[...[...drop.classes].map(c => c.toLowerCase()), ...[...drop.layers].map(l => model.layers[l].toLowerCase())].join(", ")}.` : "");

  drawRest(r, at);
  const dAt = mode === "decision" ? at : Q.attribute(r, Q.decisionWeights(r, model), model);
  if (placedHere && dAt.sum > 0 && dAt.common / dAt.sum > 0.5)
    $("verdictSub").textContent += ` Caution: ${(100 * dAt.common / dAt.sum).toFixed(0)}% of the margin comes from common features such as nu, and such placements are right much less often (see below).`;

  const mx = Math.max(...r.s, 0.001);
  $("bars").innerHTML = D.RING.map(l => {
    const i = labs.indexOf(l), s = r.s[i];
    return `<span><span class="swatch" style="background:${D.colorVar(l)}"></span>${l}</span>
      <span class="track"><span class="fill" style="width:${(100 * Math.max(s, 0)) / mx}%;background:${D.colorVar(l)}"></span></span>
      <span class="val">${fmt(s)}</span>`;
  }).join("");

  $("rose").innerHTML = D.roseSVG(r.s, labs, { size: 132, assigned: placedHere, title: "similarity rose" });
  drawFly(r);

  // marker on the wheel
  const [x, y] = D.hexPos(r.s, labs, R);
  el("circle", { cx: x, cy: y, r: 11, fill: "none", stroke: "var(--hi)", "stroke-width": 2.5 }, gMe);
  el("circle", { cx: x, cy: y, r: 5, fill: D.colorVar(r.top), stroke: "var(--surface-1)", "stroke-width": 2 }, gMe);
  const t = el("text", { x: x + 15, y: y + 4, class: "label-strong" }, gMe);
  t.textContent = fromId || "your fragment";

  // contributions
  const ti = labs.indexOf(r.top);
  const cs = Q.contributions(r.vec, model.cents[ti], model.vocab).slice(0, 12);
  const cmax = cs[0]?.value || 1;
  $("whySub").textContent = `What adds most to the similarity with ${r.top}. Sign sequences are marked §, signs joined by ·.`;
  $("contrib").innerHTML = cs.map(c => `<span class="term translit" title="${c.term}">${c.term}</span>
    <span class="track"><span class="fill" style="width:${(100 * c.value) / cmax}%;background:${D.colorVar(r.top)}"></span></span>
    <span class="val small muted">${(100 * c.value / r.topScore).toFixed(0)}%</span>`).join("");

  // barcode
  const core = model.core[r.top];
  const hit = core.filter(j => r.vec.has(j)).length;
  $("barcodeSub").textContent = `The 200 most characteristic features of ${r.top}, strongest first. Your fragment attests ${hit} of them.`;
  $("barcode").innerHTML = core.map(j => `<div class="${r.vec.has(j) ? "on" : ""}" title="${model.vocab[j]}"></div>`).join("");

  const state = { text, label: fromId || "your fragment", b: "T:" + r.top };
  $("toCompare").href = "compare.html#" + encodeURIComponent(JSON.stringify(state));
  $("cmpLink").href = $("toCompare").href;
}

// ---------- word butterfly ----------
async function drawFly(r) {
  const W = await getWords();
  const words = r.parsed.words.filter(w => w.word).map(w => w.word);
  const A = Q.tfidf(words, W.index, W.idf);
  const [idx, val] = W.centroids[labs.indexOf(r.top)];
  const B = new Map(idx.map((j, k) => [j, val[k]]));
  $("flySub").textContent = `Word tf-idf in your fragment (left) against ${r.top} (right). Bold words occur in both; the order puts what they share first.`;
  $("fly").innerHTML = D.butterflyHTML(D.butterflyRows(A, B, "prod", 14), W.vocab, "var(--text-muted)", D.colorVar(r.top),
    { heads: ["fragment", D.SHORT[r.top]] });
}

// ---------- rose gallery ----------
const fits = c => !c.outside && !c.low_fit;
const perTradition = D.RING.flatMap(l => placed.filter(c => c.assigned === l && fits(c)).slice(0, 1));
const outsiders = orphans.filter(c => c.outside && c.n >= 15).sort((a, b) => b.n - a.n);
const galleryItems = [...perTradition, ...orphans.filter(c => !c.assigned && fits(c) && c.n >= 20).slice(0, 3),
  ...[...new Map(outsiders.map(c => [c.outside, c])).values()].slice(0, 3)];
const tag = c => c.outside ? "outside: " + c.outside : c.low_fit ? "fits nothing known" : c.assigned ? D.SHORT[c.assigned] : "unplaced";
$("gallery").innerHTML = galleryItems.map(c => `<button class="tile" data-id="${c.id}" title="${c.id}: ${tag(c)}">
  ${D.roseSVG(c.s, labs, { size: 88, assigned: c.assigned && fits(c), title: c.id })}
  <span class="small">${c.id}</span><span class="small muted">${tag(c)}</span></button>`).join("");
for (const b of $("gallery").querySelectorAll(".tile"))
  b.onclick = () => { load(b.dataset.id); window.scrollTo({ top: 0, behavior: "smooth" }); };

// ---------- load a TLHdig text by siglum, or by a TLHdig or Konkordanz link ----------
async function load(id) {
  const text = await P.getText(id);
  if (text === undefined) return false;
  $("input").value = text;
  history.replaceState(null, "", "#id=" + encodeURIComponent(id));
  run(id);
  return true;
}
$("fetchForm").onsubmit = async ev => {
  ev.preventDefault();
  const id = P.findId($("fetchId").value, [...byId.keys()]);
  $("fetchMsg").textContent = id ? "" : "Not in TLHdig Beta 0.3. Try a siglum like KBo 27.160, or paste a TLHdig or Konkordanz link.";
  if (id) { $("fetchId").value = id; await load(id); }
};
$("fetchIds").innerHTML = corpus.filter(c => c.kind !== "other").map(c => `<option value="${c.id}">`).join("");

// start with the text named in the address, or a confident example so the page is never empty
const asked = new URLSearchParams(location.hash.slice(1)).get("id");
if (!(asked && await load(asked))) await load(placed.find(c => !c.outside && !c.low_fit).id);
