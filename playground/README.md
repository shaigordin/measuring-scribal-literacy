# Scribal tradition playground

A static, browser-only site for the Mainz Hittite & AI workshop. It shows every TLHdig text in
its CTH bin next to where the *Orphans and Archetypes* model places it, explains any placement,
and compares any two witnesses word by word. Nothing runs on a server; the version is in
`VERSION` and the changes in `CHANGELOG.md`.

## Pages

- `index.html`, **Browse by CTH** (the opening page). All 23,359 TLHdig texts with a legible
  word, grouped by their original CTH bin (as TLHdig and the Konkordanz file them, with the TLHdig
  CTH titles) or by the model's new classification. Headline tiles show how much of each orphan
  pool the method places. Every text links to its placement page, its TLHdig page and its
  Konkordanz entry; every bin links to its TLHdig and Konkordanz lists. The view is kept in the
  address (`#group=cth&kind=orphan&open=470`), so a link can open a given bin.
- `place.html`, **Place a fragment**. Load a TLHdig text by siglum or by pasting a TLHdig or
  Konkordanz link, or paste any transliteration. It shows the scores, the open-set verdict
  ("fits no known tradition" or "outside the reference", E9), what the score rests on (word
  classes and layers; by default the decision margin, as in E11, with a warning when most of
  it comes from features common to all traditions), the tradition wheel, the archetype
  barcode, the similarity rose and the word butterfly. `place.html#id=KBo%2027.160` opens a text.
- `compare.html`, **Compare word by word**: per-word tf-idf of two witnesses (fragment,
  manuscript or tradition centroid), after the Neo-Babylonian Dillard study (2023).

## Code

| File | What it does |
|---|---|
| `js/model.js` | Port of `../orphans/qtm`: sign splitting, "both" features, tf-idf, nearest-centroid cosine, abstention margin, E9 open-set check, word-class breakdown. |
| `js/draw.js` | Tradition order and colours, wheel geometry, similarity rose, word butterfly. |
| `js/verdict.js` | One category per text (a tradition, or why it is not placed). |
| `js/portal.js` | Links into hethport.net (TLHdig, Konkordanz); loading a bundled TLHdig text by siglum or link. |
| `js/browse.js`, `js/place.js`, `js/compare.js` | One script per page. |
| `css/style.css` | Colour tokens (light and dark) and layout. |
| `build/build_data.py` | Exports the model and every TLHdig text to `data/`. |
| `build/cth_titles.py` | Snapshots the TLHdig CTH titles to `sources/cth_titles.csv`. |
| `tests/check.mjs` | Checks the browser model against the Python export. |

The Mainz portal does not let other sites read its pages, so the texts come from the TLHdig
release bundled in `data/` (`texts.json` for the model's texts, `texts_more.json`, loaded on
demand, for the rest) and the portal is reached by links.

## Rebuild the data

```
python3 -m pip install scikit-learn pandas lxml
python3 -m qtm.tlhdig <TLHdig 0.3 release dir> tokens.csv   # run inside ../orphans
python3 build/cth_titles.py                                  # only if sources/ is missing
python3 build/build_data.py tokens.csv                       # writes data/
node tests/check.mjs
```

The export reuses `../orphans/qtm`, `run_openset.py` and the margin and fit floors of
`../orphans/results/tlhdig03_literature/`, the deck's main reference (literature groups with the
HFR split). It reproduces the deck: 940 of 2,010 orphans assigned, 159 below the fit floor, 255
nearest to an outside genre, 255 assigned orphans whose margin rests mostly on common features
(E5, E9, E11b). Texts outside the reference and the orphan pool are judged the same way as
orphans; those the open-set gate was fitted on are marked, since their gate verdict is in-sample.
`data/category_shares.csv` gives each tradition's similarity and decision shares by word class
and layer (the decision shares match E11a).

The browser maps pasted transliteration to word forms itself, so it agrees with the Python
export on 98.3% of orphan placements and about 98.5% of the open-set flags; the rest differ
because a few transliterations map to more than one normalised word form.

## Serve locally

`python3 -m http.server` in this folder, then open http://localhost:8000. The site build copies
this folder into `_site/playground/` (see `resources` in `../_quarto.yml`).

## Releases

Bump `VERSION`, add a section to `CHANGELOG.md`, and tag the commit `playground-v<version>`.
