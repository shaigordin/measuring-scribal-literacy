// Browse every TLHdig text by its original CTH bin, or by the model's new classification.
import { loadModel } from "./model.js";
import { SHORT } from "./draw.js";
import { CATEGORIES, UNPLACED, KINDS, verdictOf, verdictColor } from "./verdict.js";
import * as P from "./portal.js";

const $ = id => document.getElementById(id);
const [model, corpus, titles, version] = await Promise.all([
  loadModel(),
  fetch("data/corpus.json").then(r => r.json()),
  fetch("data/cth_titles.json").then(r => r.json()),
  fetch("VERSION").then(r => (r.ok ? r.text() : "")).catch(() => ""),
]);
for (const c of corpus) c.verdict = verdictOf(c, model);
if (version.trim()) $("version").textContent = `Version ${version.trim()}.`;

const pct = (a, b) => (b ? Math.round((100 * a) / b) + "%" : "–");
const label = v => SHORT[v] ?? v;
const isPlaced = v => !UNPLACED.includes(v);
const esc = s => String(s).replace(/[&<>"]/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]);

function counts(texts) {
  const n = Object.fromEntries(CATEGORIES.map(v => [v, 0]));
  for (const c of texts) n[c.verdict]++;
  const judged = texts.length - n["Under 5 words"];
  const placed = CATEGORIES.filter(isPlaced).reduce((a, v) => a + n[v], 0);
  return { n, total: texts.length, judged, placed };
}

// one stacked bar: a segment per category, in the order of the legend
function stack(k) {
  return `<span class="stack">${CATEGORIES.filter(v => k.n[v]).map(v =>
    `<span style="width:${(100 * k.n[v]) / k.total}%;background:${verdictColor(v)}" title="${esc(v)}: ${k.n[v]}" data-v="${esc(v)}"></span>`).join("")}</span>`;
}

// ---------- headline tiles ----------
const TILES = [
  ["CTH 470 ritual fragments", c => c.cth === "470"],
  ["EBo fragments", c => c.id.startsWith("EBo")],
  ["CTH 670 festival fragments", c => c.cth === "670" && !c.id.startsWith("EBo")],
  ["CTH 832 diverse fragments", c => c.cth === "832" && !c.id.startsWith("EBo")],
  ["Reference manuscripts, held out", c => c.kind === "ref"],
];
$("tiles").innerHTML = TILES.map(([name, f]) => {
  const texts = corpus.filter(f), k = counts(texts);
  const right = name.startsWith("Reference") ? texts.filter(c => c.verdict === c.label).length : null;
  return `<div class="tile">
    <div class="small muted">${name}</div>
    <div class="big">${pct(k.placed, k.judged)} <span class="small muted">placed</span></div>
    <div class="small">${k.placed.toLocaleString()} of ${k.judged.toLocaleString()} judged texts${right === null ? "" : `, ${pct(right, k.placed)} of them correctly`}${k.n["Under 5 words"] ? `; ${k.n["Under 5 words"].toLocaleString()} more under 5 words` : ""}</div>
    ${stack(k)}</div>`;
}).join("");
$("legend").innerHTML = CATEGORIES.map(v => `<span><span class="swatch sq" style="background:${verdictColor(v)}"></span>${esc(label(v))}</span>`).join("");

// ---------- bins ----------
const state = Object.assign({ group: "cth", kind: "all", sort: "size", q: "", open: "" },
  Object.fromEntries(new URLSearchParams(location.hash.slice(1))));
for (const k of ["group", "kind", "sort", "q"]) {
  $(k).value = state[k];
  $(k).addEventListener("input", () => { state[k] = $(k).value; state.open = ""; draw(); });
}
const save = () => history.replaceState(null, "", "#" + new URLSearchParams(state));

function bins() {
  const texts = corpus.filter(c => state.kind === "all" || c.kind === state.kind);
  const key = state.group === "cth" ? c => c.cth : c => c.verdict;
  const by = new Map();
  for (const c of texts) { const k = key(c); if (!by.has(k)) by.set(k, []); by.get(k).push(c); }
  let rows = [...by].map(([k, list]) => ({ k, list, counts: counts(list),
    title: state.group === "cth" ? titles[k] ?? "" : "" }));
  const q = state.q.trim().toLowerCase();
  if (q) {
    const ids = new Set(texts.filter(c => c.id.toLowerCase().includes(q)).map(c => c.id));
    rows = rows.filter(r => r.k.toLowerCase() === q || (q.length > 2 && r.title.toLowerCase().includes(q)) ||
                            label(r.k).toLowerCase().includes(q) || r.list.some(c => ids.has(c.id)));
    if (q.length > 2 && ids.size) for (const r of rows) r.hits = r.list.filter(c => ids.has(c.id));
  }
  const num = k => parseFloat(k) || 1e9;
  const order = {
    size: (a, b) => b.list.length - a.list.length,
    placed: (a, b) => b.counts.placed / (b.counts.judged || 1) - a.counts.placed / (a.counts.judged || 1) || b.list.length - a.list.length,
    key: state.group === "cth" ? (a, b) => num(a.k) - num(b.k) || a.k.localeCompare(b.k)
                               : (a, b) => CATEGORIES.indexOf(a.k) - CATEGORIES.indexOf(b.k),
  }[state.sort];
  return rows.sort(order);
}

function draw() {
  save();
  const rows = bins();
  const nTexts = rows.reduce((a, r) => a + r.list.length, 0);
  $("count").textContent = `${rows.length} ${state.group === "cth" ? (rows.length === 1 ? "CTH bin" : "CTH bins") : (rows.length === 1 ? "class" : "classes")}, ${nTexts.toLocaleString()} texts. Click a row to list its texts.`;
  $("bins").innerHTML = `<div class="bin head"><span>${state.group === "cth" ? "CTH" : "Class"}</span><span></span><span class="num">Texts</span><span>${state.group === "cth" ? "Where the model places them" : ""}</span><span class="num">Placed</span></div>` +
    rows.map(r => {
      const name = state.group === "cth"
        ? `<b>${esc(r.k)}</b> <span class="muted">${esc(r.title)}</span>`
        : `<span class="swatch sq" style="background:${verdictColor(r.k)}"></span><b>${esc(r.k)}</b>`;
      const bar = state.group === "cth" ? stack(r.counts)
        : `<span class="kinds small muted">${Object.entries(KINDS).map(([k, l]) => `${r.list.filter(c => c.kind === k).length.toLocaleString()} ${l}`).join(" · ")}</span>`;
      const open = state.open === r.k || (r.hits && rows.length <= 3);
      return `<details class="bin" data-k="${esc(r.k)}" ${open ? "open" : ""}><summary>
          <span class="name">${name}</span><span></span><span class="num">${r.list.length.toLocaleString()}</span>
          ${bar}<span class="num">${state.group === "cth" ? pct(r.counts.placed, r.counts.judged) : ""}</span></summary>
          <div class="list" data-k="${esc(r.k)}"></div></details>`;
    }).join("");
  for (const d of $("bins").querySelectorAll("details")) {
    const r = rows.find(x => x.k === d.dataset.k);
    const fill = () => list(d.querySelector(".list"), r);
    if (d.open) fill();
    d.addEventListener("toggle", () => { if (d.open) { state.open = r.k; save(); fill(); } });
  }
}

const LIMIT = 200;
function list(box, r, filter = "", all = false) {
  if (box.dataset.filled === filter + all) return;
  box.dataset.filled = filter + all;
  const texts = (r.hits ?? r.list).filter(c => !filter || c.verdict === filter)
    .sort((a, b) => (isPlaced(b.verdict) - isPlaced(a.verdict)) || b.n - a.n);
  const shown = all ? texts : texts.slice(0, LIMIT);
  const present = [...new Set(r.list.map(c => c.verdict))].sort((a, b) => CATEGORIES.indexOf(a) - CATEGORIES.indexOf(b));
  const links = state.group === "cth" ? ` · <a href="${P.tlhdigCth(r.k)}" target="_blank" rel="noopener">CTH ${esc(r.k)} in TLHdig</a> · <a href="${P.konkordanzCth(r.k)}" target="_blank" rel="noopener">in the Konkordanz</a>` : "";
  box.innerHTML = `<div class="row small">${state.group === "cth" ? `<span class="muted">Show:</span>` +
      [["", "all"], ...present.map(v => [v, label(v)])].map(([v, l]) => `<button class="pill ${v === filter ? "on" : ""}" data-v="${esc(v)}">${esc(l)}</button>`).join("") : ""}
      <span class="muted">${r.hits ? `${r.hits.length} matching` : ""}${links}</span></div>
    <table class="texts"><tr><th>Text</th><th class="num">Words</th>${state.group === "cth" ? "" : "<th>CTH</th>"}<th>Kind</th><th>Model</th><th class="num">Margin</th><th>Open</th></tr>` +
    shown.map(c => `<tr><td>${esc(c.id)}</td><td class="num">${c.n}</td>${state.group === "cth" ? "" : `<td>${esc(c.cth)}</td>`}
      <td class="muted">${KINDS[c.kind]}</td>
      <td><span class="swatch sq" style="background:${verdictColor(c.verdict)}"></span>${esc(label(c.verdict))}${c.kind === "ref" && c.verdict !== c.label && isPlaced(c.verdict) ? ` <span class="muted" title="Reference manuscript of ${esc(c.label)}">(is ${esc(label(c.label))})</span>` : ""}${notes(c)}</td>
      <td class="num">${c.gap === undefined ? "" : c.gap.toFixed(3)}</td>
      <td class="small">${c.short ? "" : `<a href="place.html#id=${encodeURIComponent(c.id)}">place</a> · `}${P.portalLinks(c.id, c.cth)}</td></tr>`).join("") +
    `</table>` + (shown.length < texts.length ? `<button class="more">Show all ${texts.length.toLocaleString()}</button>` : "");
  for (const b of box.querySelectorAll(".pill")) b.onclick = () => list(box, r, b.dataset.v);
  box.querySelector(".more")?.addEventListener("click", () => list(box, r, filter, true));
}

function notes(c) {
  const n = [];
  if (isPlaced(c.verdict) && c.common > 0.5) n.push(`<span class="warn" title="More than half of the margin comes from features common to all traditions (like nu); such placements are right much less often (E11d).">common words</span>`);
  if (c.gate_fit) n.push(`<span class="muted" title="One of the texts the open-set check was fitted on, so its open-set verdict is not a test.">gate text</span>`);
  return n.length ? " " + n.join(" ") : "";
}

draw();
