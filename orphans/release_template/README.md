# $title

Version $version, $date. Shai Gordin (Ariel University). Licence CC BY 4.0.
Built from TLHdig Beta Version $tlhdig (Müller, Prechel, Rieken and Schwemer 2026, doi:[$tlhdig_doi](https://doi.org/$tlhdig_doi)).
Code: <$code_url> (folder `orphans/`). Online tool: <https://shaigordin.github.io/text-orphans/>.

## What this is

Laroche's catalogue (CTH) leaves thousands of Hittite fragments in residual bins: CTH 470 (ritual
fragments), 500 (Kizzuwatna ritual fragments), 670 (festival fragments), 832 (fragments of various
content) and the CTH 390–469 rituals that no study groups. For each of these texts and for every EBo
fragment ($texts texts) the dataset gives:

- the nearest of ten reference traditions, and whether its lead is large enough to place the fragment;
- the five nearest compositions (CTH numbers) and the twenty nearest manuscripts among $pool TLHdig
  texts, with three checks for a possible duplicate or join;
- the share of the fragment's words in ten word categories.

## Two datasets: without and with restorations

$versions_table

Use **`without_restorations/`** for claims about a fragment. With restorations counted, a fragment can
look close to the very text its editor restored it from. Comparing the two shows which results rest on
restored signs: $placed_both fragments are placed in both datasets, $placed_same of them in the same
tradition.

## How a fragment is placed

Each text becomes a list of counts of its words (the lemma of TLHdig's word analysis) and of the sign
sequences (one to three signs) inside its words, weighted by tf-idf. Words that TLHdig $tlhdig leaves
without an analysis take the analysis of the same spelling elsewhere in TLHdig, or, for Cuneiform
Luwian, the lemma of eDiAna (2026; CC BY-SA 4.0). Every filled word names its source, the TLHdig line or
the eDiAna entry, in the column `fill_source` of the reproducible token table. Each tradition is the
average of its reference manuscripts (17 or more words). A fragment goes to the most similar tradition (cosine similarity) only if it leads the
runner-up by at least the margin. The margin is calibrated on pieces cut from reference manuscripts,
so that about $precision of placed pieces land in their own tradition; below it the fragment is left
unplaced.

$traditions_table

## Files

Each folder holds the same files; `datapackage.json` describes every column.

| File | Content |
|---|---|
| `fragments.csv` | One row per text: nearest traditions and similarities, margin, placement, open-set checks, nearest compositions and manuscripts, word-category shares. Texts with fewer than 5 analysed words have `status = too_small` and no results. |
| `nearest_manuscripts.csv` | One row per fragment and each of its 20 nearest manuscripts, with a word barcode and the three match checks (half the words shared, every shared word spelled the same, a shared two-word phrase). |
| `traditions.csv` | The ten reference traditions, their CTH numbers, reference manuscripts and defining studies. |
| `compositions.csv` | The compositions (CTH numbers) used for the nearest compositions. |
| `summary.json` | The counts quoted in this README. |

## Limits

- A placement means "nearest of these ten traditions". A fragment of a tradition outside the reference
  is still drawn to the most similar one; the open-set columns flag fragments that fit none well.
- Fragments with fewer than about ten words are rarely placed.
- The match checks find duplicates far better than joins: of $kd_n duplicate pairs recorded in the
  Konkordanz, the duplicate is among the twenty nearest manuscripts in $kd_top20 (median rank
  $kd_median); of $kj_n proposed joins, $kj_top20. A candidate is a lead to check on the tablets.
- Word categories are assigned by rules from TLHdig's word analyses; the word lexicon remains to be
  verified manually.

## How to cite

Gordin, Shai. 2026. *$title*. Version $version. Zenodo. Please cite TLHdig $tlhdig as well.

## How to rebuild

```
git clone $code_url
cd measuring-scribal-literacy/orphans
python3 -m pip install -r requirements.txt     # Python 3.13
bash reproduce.sh                              # downloads TLHdig $tlhdig (checksum-verified) and rebuilds everything
```

## References

$references
