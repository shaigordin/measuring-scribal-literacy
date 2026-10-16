# Scribal tradition playground

A static, browser-only page for the Mainz Hittite & AI workshop. Paste a transliterated fragment
and see which textual tradition the *Orphans and Archetypes* model places it in, why, and how its
words compare with any other manuscript or tradition.

- `index.html`: place a fragment. Scores, and the four signature views: the tradition hexagon
  (every manuscript placed between the six tradition corners), the archetype barcode (the
  tradition's 200 strongest features, with the ones the fragment attests filled in), the
  similarity rose (one wedge per tradition, pointing to its hexagon corner, with a gallery of
  orphan roses), and the word butterfly (fragment vs. nearest tradition by word tf-idf).
- `compare.html`: word-by-word tf-idf comparison of two witnesses (fragment, manuscript or
  tradition centroid), and for any word, the manuscripts where it carries the most weight.
  This follows the per-word tf-idf comparison of the Neo-Babylonian Dillard study (2023).
- `qtm.js`: JavaScript port of `../orphans/qtm` (sign splitting, "both" feature space,
  sublinear tf-idf, nearest-centroid cosine, abstention margin).
- `data/`: the model exported by `build_data.py`.

## Rebuild the data

```
python3 -m pip install scikit-learn pandas lxml
python3 -m qtm.tlhdig <TLHdig 0.3 release dir> tokens.csv      # run inside ../orphans
python3 build_data.py tokens.csv                                # writes data/*.json
```

The export reuses `../orphans/qtm` and the abstention margin from
`../orphans/results/tlhdig03/report.json`, so the page scores exactly like `run_experiments.py`.
Run on the 2,004 orphans, the browser scores match Python to within 0.002 on average and give the
same verdict for 1,989 of them (99.3%); the rest differ because a few transliterations map to more
than one normalised word form, and the page picks the most frequent one.

## Serve locally

`python3 -m http.server` in this folder, then open http://localhost:8000. The site build copies
this folder into `_site/playground/` (see `resources` in `../_quarto.yml`), so on GitHub Pages it
lives at `/measuring-scribal-literacy/playground/`.
