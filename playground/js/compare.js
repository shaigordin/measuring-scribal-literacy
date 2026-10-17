// Word-by-word tf-idf comparison of two witnesses (fragment, manuscript or tradition).
import * as Q from "./model.js";
import * as D from "./draw.js";
const $ = id => document.getElementById(id);
const [model, W, corpus] = await Promise.all([
  Q.loadModel(), fetch("data/words.json").then(r => r.json()), fetch("data/corpus.json").then(r => r.json())]);
const labs = model.traditions;
const windex = new Map(W.vocab.map((t, i) => [t, i]));
const rowOf = new Map(W.ids.map((id, i) => [id, i]));
const meta = new Map(corpus.map(c => [c.id, c]));
const toMap = ([idx, val]) => new Map(idx.map((j, k) => [j, val[k]]));

let state = {};
try { state = JSON.parse(decodeURIComponent(location.hash.slice(1)) || "{}"); } catch {}
const fragVec = state.text
  ? Q.tfidf(Q.parse(state.text, model).words.filter(w => w.word).map(w => w.word), windex, W.idf)
  : null;

function source(key) {
  if (key === "F") return { name: state.label || "your fragment", vec: fragVec, kind: "fragment" };
  if (key.startsWith("T:")) { const l = key.slice(2); return { name: l, vec: toMap(W.centroids[labs.indexOf(l)]), kind: "tradition", lab: l }; }
  const id = key.slice(2), c = meta.get(id);
  return { name: id, vec: toMap(W.rows[rowOf.get(id)]), kind: c?.kind, lab: c?.label || c?.assigned, c };
}
function fill(sel) {
  if (fragVec) sel.append(new Option(`Fragment: ${state.label || "your fragment"}`, "F"));
  const og = document.createElement("optgroup"); og.label = "Traditions (centroids)";
  for (const l of D.RING) og.append(new Option(l, "T:" + l));
  sel.append(og);
  const og2 = document.createElement("optgroup"); og2.label = "Manuscripts"; og2.id = sel.id + "Ms";
  sel.append(og2);
}
fill($("a")); fill($("b"));
$("ids").innerHTML = W.ids.map(id => `<option value="${id}">`).join("");
function setMs(sel, id) {
  if (!rowOf.has(id)) return false;
  const og = $(sel.id + "Ms");
  if (![...og.children].some(o => o.value === "M:" + id)) og.append(new Option(id, "M:" + id));
  sel.value = "M:" + id;
  return true;
}
const pick = (sel, key) => (key.startsWith("M:") ? setMs(sel, key.slice(2)) : (sel.value = key));
pick($("a"), state.a || (fragVec ? "F" : "M:KBo 27.160"));
pick($("b"), state.b || "T:" + labs[0]);
for (const s of ["a", "b"]) {
  $(s + "Id").addEventListener("change", e => { if (setMs($(s), e.target.value.trim())) draw(); });
  $(s).onchange = draw;
}
$("sort").onchange = draw; $("nrows").onchange = draw;
$("swap").onclick = () => { const a = $("a").value, b = $("b").value; pick($("a"), b); pick($("b"), a); draw(); };

const color = lab => (lab ? D.colorVar(lab) : "var(--text-muted)");
let selWord = null;

function draw() {
  const A = source($("a").value), B = source($("b").value);
  let dot = 0, shared = 0;
  for (const [j, x] of A.vec) { const y = B.vec.get(j); if (y) { dot += x * y; shared++; } }
  $("cos").textContent = dot.toFixed(3);
  $("shared").textContent = `${shared} shared word forms; A has ${A.vec.size}, B has ${B.vec.size}.`;
  const top = D.butterflyRows(A.vec, B.vec, $("sort").value, +$("nrows").value);
  $("flyTitle").textContent = `${A.name}  ↔  ${B.name}`;
  $("fly").innerHTML = D.butterflyHTML(top, W.vocab, color(A.lab), color(B.lab), { sel: selWord });
  for (const w of $("fly").querySelectorAll(".w")) w.onclick = () => rank(w.dataset.w);
  if (!selWord && top[0]) rank(W.vocab[top[0].j]); else if (selWord) rank(selWord);
}

let inverted = null;
function rank(word) {
  selWord = word;
  for (const w of $("fly").querySelectorAll(".w")) w.classList.toggle("sel", w.dataset.w === word);
  if (!inverted) {
    inverted = new Map();
    W.rows.forEach(([idx, val], i) => idx.forEach((j, k) => { let l = inverted.get(j); if (!l) inverted.set(j, (l = [])); l.push([i, val[k]]); }));
  }
  const j = windex.get(word);
  const list = (inverted.get(j) || []).sort((p, q) => q[1] - p[1]);
  const shown = list.slice(0, 40), mx = shown[0]?.[1] || 1;
  $("rankTitle").innerHTML = `<span class="translit">${word}</span>`;
  $("rankSub").textContent = `Occurs in ${list.length} manuscripts (idf ${W.idf[j].toFixed(2)}). Top ${shown.length} by tf-idf; click a row to put it on the right.`;
  $("rank").innerHTML = `<tr><th>Manuscript</th><th>Tradition</th><th class="num">tf-idf</th><th></th></tr>` +
    shown.map(([i, v]) => {
      const c = meta.get(W.ids[i]), lab = c?.label || c?.assigned;
      return `<tr data-id="${W.ids[i]}"><td>${W.ids[i]}</td><td>${lab ? `<span class="swatch" style="background:${D.colorVar(lab)}"></span>${D.SHORT[lab]}` : `<span class="muted">orphan, unplaced</span>`}${c?.kind === "orphan" && lab ? ' <span class="muted">(orphan)</span>' : ""}</td>
        <td class="num">${v.toFixed(3)}</td><td class="bar"><span style="width:${(100 * v) / mx}%;background:${color(lab)}"></span></td></tr>`;
    }).join("");
  for (const tr of $("rank").querySelectorAll("tr[data-id]")) tr.onclick = () => { setMs($("b"), tr.dataset.id); draw(); };
}
draw();
