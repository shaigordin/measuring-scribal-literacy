// Archetype barcodes for one fragment (Mainz deck slide "barcode").
// For each of the ten reference traditions, take its 200 most characteristic features
// (model.core, strongest first, as in the playground's "Archetype barcode") and mark which
// ones the fragment attests, split into distinctive features and features common everywhere
// (model.common, e.g. nu). Uses the playground model built by playground/build/build_data.py.
// Usage: node orphans/slide_barcode.mjs <playground dir> "KBo 41.22" > orphans/results/slide_barcode.json
import fs from "fs";
import path from "path";
import { pathToFileURL } from "url";

const [dir, id] = process.argv.slice(2);
const M = await import(pathToFileURL(path.resolve(dir, "js/model.js")));
const read = f => JSON.parse(fs.readFileSync(path.join(dir, "data", f)));
const model = read("model.json"), gate = read("gate.json");
for (const m of [model, gate]) { m.index = new Map(m.vocab.map((t, i) => [t, i])); m.cents = M.denseCentroids(m); }
model.gate = gate;
model.common = new Set(model.common);
const texts = { ...read("texts.json"), ...read("texts_more.json") };
if (!texts[id]) throw new Error(`no bundled text for ${id}`);
const r = M.scoreText(texts[id], model);
const rows = model.traditions.map(t => {
  const cells = model.core[t].map(j => (r.vec.has(j) ? (model.common.has(j) ? "c" : "d") : "."));
  return { tradition: t, cells: cells.join(""), attested: cells.filter(c => c !== ".").length,
    distinctive: cells.filter(c => c === "d").length, terms: model.core[t].filter(j => r.vec.has(j) && !model.common.has(j)).map(j => model.vocab[j]) };
}).sort((a, b) => b.distinctive - a.distinctive);
console.log(JSON.stringify({ id, top: r.top, runnerUp: r.runnerUp, assigned: r.assigned ?? null,
  topScore: r.topScore, margin: r.gap, coreSize: model.core[r.top].length, rows }, null, 1));
