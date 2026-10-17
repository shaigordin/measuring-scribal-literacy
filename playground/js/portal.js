// The Mainz portal (hethport.net): links to TLHdig and the Konkordanz, and loading TLHdig texts.
// The portal does not allow other sites to read its pages, so texts come from the TLHdig release
// bundled in data/ (texts.json for the model's texts, texts_more.json for the rest of TLHdig).

const PORTAL = "https://hethport.net";
const q = encodeURIComponent;

export const tlhdigText = (id, cth) => `${PORTAL}/TLHdig/tlh_xtx.php?d=${q(id)}${cth ? "&o=" + q("CTH " + cth) : ""}`;
export const tlhdigCth = cth => `${PORTAL}/TLHdig/tlh_idx2.php?t=${q("CTH " + cth)}`;
export const konkordanzCth = cth => `${PORTAL}/hetkonk/hetkonk_abfrage.php?c=${q(cth)}`;
// The Konkordanz is keyed by single publications; a join "KBo 21.33 + KBo 22.1" opens its first piece.
export const konkordanzText = id => `${PORTAL}/hetkonk/hetkonk_abfrage.php?p=${q(id.split(/\s*\+/)[0].trim())}`;

export function portalLinks(id, cth) {
  return `<a href="${tlhdigText(id, cth)}" target="_blank" rel="noopener">TLHdig</a> · ` +
    `<a href="${konkordanzText(id)}" target="_blank" rel="noopener">Konkordanz</a>`;
}

let main = null, more = null;
const json = path => fetch(path).then(r => r.json());

// Transliteration of one TLHdig text, or undefined.
export async function getText(id) {
  main ??= await json("data/texts.json");
  if (id in main) return main[id];
  more ??= await json("data/texts_more.json");
  return more[id];
}

// A siglum ("KBo 27.160", "kbo 27.160") or a TLHdig or Konkordanz address -> a TLHdig text id.
const norm = s => s.toLowerCase().replace(/\s+/g, " ").replace(/\s*([.+,])\s*/g, "$1").trim();
export function findId(input, ids) {
  const param = input.match(/[?&](?:d|p|txtnr)=([^&#]+)/);  // a TLHdig or Konkordanz address
  let s = input.trim();
  if (param) try { s = decodeURIComponent(param[1]); } catch { s = param[1]; }
  const want = norm(s);
  const byNorm = new Map(ids.map(id => [norm(id), id]));
  if (byNorm.has(want)) return byNorm.get(want);
  // a piece of a join
  return ids.find(id => norm(id).split("+").includes(want)) ?? null;
}
