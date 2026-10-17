// Check the browser model against the Python export: run `node tests/check.mjs` in playground/.
// For every orphan it re-scores the bundled transliteration in JavaScript and compares the
// placement and the open-set flags with data/corpus.json (written by build/build_data.py), and it
// checks that the word-class breakdown sums exactly to the score and to the decision margin.
import fs from "fs";
import * as M from "../js/model.js";

const read = f => JSON.parse(fs.readFileSync(new URL(`../data/${f}`, import.meta.url)));
const model = read("model.json"), gate = read("gate.json");
for (const m of [model, gate]) { m.index = new Map(m.vocab.map((t, i) => [t, i])); m.cents = M.denseCentroids(m); }
model.gate = gate;
model.common = new Set(model.common);
const corpus = read("corpus.json"), texts = read("texts.json");

const orphans = corpus.filter(c => c.kind === "orphan" && !c.short);
let placed = 0, lowFit = 0, outside = 0, flagged = { js: 0, py: 0 }, worst = 0;
for (const c of orphans) {
  const r = M.scoreText(texts[c.id], model);
  placed += (r.assigned ?? null) === (c.assigned ?? null);
  lowFit += r.open.lowFit === c.low_fit;
  outside += (r.open.outside ?? null) === (c.outside ?? null);
  const sim = M.attribute(r, model.cents[model.traditions.indexOf(r.top)], model);
  const dec = M.attribute(r, M.decisionWeights(r, model), model);
  worst = Math.max(worst, Math.abs(sim.sum - r.topScore), Math.abs(dec.sum - r.gap));
  flagged.js += r.gap >= model.margin && dec.sum > 0 && dec.common / dec.sum > 0.5;
  flagged.py += c.gap >= model.margin && c.common > 0.5;
}
const share = k => `${k} of ${orphans.length} (${((100 * k) / orphans.length).toFixed(1)}%)`;
console.log(`same placement:          ${share(placed)}`);
console.log(`same fit-floor flag:     ${share(lowFit)}`);
console.log(`same outside-genre flag: ${share(outside)}`);
console.log(`placed mostly on common features: browser ${flagged.js}, Python ${flagged.py}`);
console.log(`largest breakdown error: ${worst.toExponential(1)}`);
if (worst > 1e-9 || placed / orphans.length < 0.97) process.exit(1);
