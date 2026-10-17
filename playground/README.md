# Scribal tradition playground

A static, browser-only page for the Mainz Hittite & AI workshop. Paste a transliterated fragment
and see which textual tradition the *Orphans and Archetypes* model places it in, why, and how its
words compare with any other manuscript or tradition.

- `index.html`: place a fragment. Scores, the open-set verdict ("fits no known tradition" or
  "outside the reference", from E9), and the four signature views: the tradition wheel
  (every manuscript placed between the ten tradition corners), the archetype barcode (the
  tradition's 200 strongest features, with the ones the fragment attests filled in), the
  similarity rose (one wedge per tradition, pointing to its hexagon corner, with a gallery of
  orphan roses), and the word butterfly (fragment vs. nearest tradition by word tf-idf).

The model is the deck's main reference: the literature-defined traditions with the HFR split
(`--groups literature`, results in `../orphans/results/tlhdig03_literature/`).
- "What the score rests on" (on `index.html`): every feature's contribution to a score is
  shared among the words that produce it, so each word gets a share, split into its word form,
  syllabic spelling and logographic writing. Words are grouped by the E8 word classes
  (`../orphans/qtm/wordclass.py`, after StBoT 73 Table 4; the grouping is shared with E11).
  Two views: by default the decision margin (nearest minus runner-up, x·(c_top − c_2), as in
  E11), where material every tradition shares cancels; or the similarity to the nearest
  tradition (x·c_top), where frequent words such as nu look heavy. The page also gives the
  share of the margin carried by common features (attested in ≥ 25% of the reference texts)
  and warns when a placement rests more than half on them (E11d: such placements are right
  50–66% of the time on 5–20-word windows, against 78–87%; 255 of the 940 placed orphans;
  `build_data.py` prints the count, the browser flags 254). Any class or layer can be left
  out and the fragment rescored. `data/category_shares.csv` gives both breakdowns (similarity
  and decision shares, ratio of sums over each tradition's correctly placed reference
  manuscripts with leave-one-out centroids); the decision shares match E11a.
- `compare.html`: word-by-word tf-idf comparison of two witnesses (fragment, manuscript or
  tradition centroid), and for any word, the manuscripts where it carries the most weight.
  This follows the per-word tf-idf comparison of the Neo-Babylonian Dillard study (2023).
- `qtm.js`: JavaScript port of `../orphans/qtm` (sign splitting, "both" feature space,
  sublinear tf-idf, nearest-centroid cosine, abstention margin) and of the E9 open-set check
  of `../orphans/run_openset.py` (fit floor by fragment size, genre gate).
- `data/`: the model exported by `build_data.py`.

## Rebuild the data

```
python3 -m pip install scikit-learn pandas lxml
python3 -m qtm.tlhdig <TLHdig 0.3 release dir> tokens.csv      # run inside ../orphans
python3 build_data.py tokens.csv                                # writes data/*.json
```

The export reuses `../orphans/qtm`, `run_openset.py` and the margin and fit floors from
`../orphans/results/tlhdig03_literature/`, and it reproduces the deck exactly: 940 of 2,010
orphans placed, 159 below the fit floor, 255 nearest to an outside genre (checked against
`E5_orphan_placement.csv` and `E9_orphan_fit.csv`). The browser, which has to map pasted
transliteration to word forms itself, gives the same placement for 1,975 orphans (98.3%) and the
same open-set flags for about 98%; the rest differ because a few transliterations map to more
than one normalised word form, and the page picks the most frequent one.

## Serve locally

`python3 -m http.server` in this folder, then open http://localhost:8000. The site build copies
this folder into `_site/playground/` (see `resources` in `../_quarto.yml`), so on GitHub Pages it
lives at `/measuring-scribal-literacy/playground/`.
