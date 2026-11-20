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
- the share of the fragment's words in $n_categories word categories.

## Which texts are in it

Only texts whose tradition is unknown. The ten traditions have $tradition_n manuscripts in TLHdig
$tlhdig. These are the texts that the defining studies assign to a tradition, and they are not in the
dataset. Of them, $reference_n have at least 17 counted words, and only these build the ten tradition
profiles. The reason is that a short piece shows too few words to stand for a tradition: a profile
built from a handful of words mostly reflects chance. The 17-word minimum is the one used in Gordin,
Yavasan and Romach 2025 (StBoT 73). The shorter manuscripts of the traditions still take part as
candidates among the nearest manuscripts. `traditions.csv` gives both numbers for each tradition.

Every text in the dataset is compared with the ten profiles in the same way. Its CTH bin says only
where the text comes from; it plays no part in the placement.

$bins_table

EBo pieces filed under CTH 670 or 832 are counted in those bins.

A few tablets carry words that TLHdig files under two CTH numbers ($split_n scored texts, for example
$split_example). As in the paper, such a tablet is scored on its part filed under the CTH numbers the
experiments read, and its word-category shares describe that part; `n_words_analysed` counts the whole
tablet.

**Orphans** are a smaller group inside this dataset: all CTH 470 fragments and all EBo pieces. They are
the test set of the paper and the Mainz talk. Of the $orphans_scored orphans with at least five words,
$orphans_placed are placed (without restorations). They are part of the $placed_all placed fragments
above, with the same placement.

## Two datasets: without and with restorations

$versions_table

Use **`without_restorations/`** for claims about a fragment. With restorations counted, a fragment can
look close to the very text its editor restored it from. Comparing the two shows which results rest on
restored signs: $placed_both fragments are placed in both datasets, $placed_same of them in the same
tradition.

## How a fragment is placed

The method is Quantitative Tradition Mapping (QTM). Each text becomes a list of counts of its words (the lemma of TLHdig's word analysis) and of the sign
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
| `fragments.csv` | One row per text: nearest traditions and similarities, margin, placement, open-set checks, nearest compositions and manuscripts, word-category shares. Texts with fewer than 5 analysed words have `status = too_small` and empty result columns, including the word-category shares. |
| `nearest_manuscripts.csv` | One row per fragment and each of its 20 nearest manuscripts, with a word barcode and the three match checks (half the words shared, every shared word spelled the same, a shared two-word phrase). |
| `traditions.csv` | The ten reference traditions, their CTH numbers, reference manuscripts and defining studies. |
| `compositions.csv` | The compositions (CTH numbers) used for the nearest compositions. |
| `summary.json` | The counts quoted in this README. |

The folder `lexicon/` holds the word lists behind the word categories, the same for both datasets:
`gloss_lexicon.tsv` (German gloss, its class, token count, an example lemma) and `sense_rules.csv`
(the context rules, with their evidence and dictionary references).

## Limits

- A placement means "nearest of these ten traditions". A fragment of a tradition outside the reference
  is still drawn to the most similar one; the open-set columns flag fragments that fit none well.
- Fragments with fewer than about ten words are rarely placed.
- The match checks find duplicates far better than joins: of $kd_n duplicate pairs recorded in the
  Konkordanz, the duplicate is among the twenty nearest manuscripts in $kd_top20 (median rank
  $kd_median); of $kj_n proposed joins, $kj_top20. A candidate is a lead to check on the tablets.
- Word categories are assigned by rules from TLHdig's automatic word analyses. Nouns and adjectives
  are classed by their German gloss in a lexicon of $n_glosses glosses (`lexicon/gloss_lexicon.tsv`).
  Where a gloss has more than one meaning (Horn: a musician's horn or the moon's horn), one of
  $n_rules context rules (`lexicon/sense_rules.csv`) chooses the meaning from the line. Each rule names
  its dictionary reference (HEG, CHD, CAD, CDA) and the examples it rests on. An independent check
  against Open German WordNet covers $wn_coverage of the glosses and agrees with the lexicon on $wn_agree of
  them (kappa $wn_kappa). The word lexicon remains to be verified manually.

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
