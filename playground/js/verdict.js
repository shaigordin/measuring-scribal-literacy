// What the model says about one text of data/corpus.json, as one of the categories below.
// Reference texts are judged held out (leave-one-out scores) by the abstention margin alone;
// all other texts also go through the open-set check (E9).
import { RING } from "./draw.js";

export const UNPLACED = ["Too close to call", "Fits no known tradition", "Outside the reference genres", "Under 5 words"];
export const CATEGORIES = [...RING, ...UNPLACED];

export function verdictOf(c, model) {
  if (c.short) return "Under 5 words";
  if (c.kind === "ref") {
    const s = c.s, order = s.map((_, i) => i).sort((a, b) => s[b] - s[a]);
    return s[order[0]] - s[order[1]] >= model.margin ? model.traditions[order[0]] : "Too close to call";
  }
  if (c.outside) return "Outside the reference genres";
  if (c.low_fit) return "Fits no known tradition";
  return c.assigned ?? "Too close to call";
}

export const verdictColor = v => RING.includes(v) ? `var(--series-${RING.indexOf(v) + 1})` : `var(--v-${UNPLACED.indexOf(v) + 1})`;

export const KINDS = { ref: "reference", orphan: "orphan", other: "other TLHdig" };
