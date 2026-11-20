# Orphans and Archetypes: closest traditions, compositions and duplicate or join candidates for the unplaced fragments of the Hittite corpus (TLHdig 0.4)

Version 2.1.0, 2026-11-20. Shai Gordin (Ariel University). Licence CC BY 4.0.
Built from TLHdig Beta Version 0.4 (Müller, Prechel, Rieken and Schwemer 2026, doi:[10.5281/zenodo.24373727](https://doi.org/10.5281/zenodo.24373727)).
Code: <https://github.com/shaigordin/measuring-scribal-literacy> (folder `orphans/`). Online tool: <https://shaigordin.github.io/text-orphans/>.

## What this is

Laroche's catalogue (CTH) leaves thousands of Hittite fragments in residual bins: CTH 470 (ritual
fragments), 500 (Kizzuwatna ritual fragments), 670 (festival fragments), 832 (fragments of various
content) and the CTH 390–469 rituals that no study groups. For each of these texts and for every EBo
fragment (11,440 texts) the dataset gives:

- the nearest of ten reference traditions, and whether its lead is large enough to place the fragment;
- the five nearest compositions (CTH numbers) and the twenty nearest manuscripts among 19,417 TLHdig
  texts, with three checks for a possible duplicate or join;
- the share of the fragment's words in 11 word categories.

## Which texts are in it

Only texts whose tradition is unknown. The ten traditions have 2,627 manuscripts in TLHdig
0.4. These are the texts that the defining studies assign to a tradition, and they are not in the
dataset. Of them, 1,643 have at least 17 counted words, and only these build the ten tradition
profiles. The reason is that a short piece shows too few words to stand for a tradition: a profile
built from a handful of words mostly reflects chance. The 17-word minimum is the one used in Gordin,
Yavasan and Romach 2025 (StBoT 73). The shorter manuscripts of the traditions still take part as
candidates among the nearest manuscripts. `traditions.csv` gives both numbers for each tradition.

Every text in the dataset is compared with the ten profiles in the same way. Its CTH bin says only
where the text comes from; it plays no part in the placement.

| Laroche bin | Texts | Placed |
|---|---|---|
| CTH 470 fragments of rituals | 1,927 | 424 |
| CTH 500 fragments of Kizzuwatna rituals | 481 | 182 |
| CTH 670 fragments of festivals | 3,560 | 1,365 |
| CTH 832 fragments of various content | 4,272 | 226 |
| CTH 390-469 rituals no study groups | 1,043 | 267 |
| EBo filed under other CTH numbers | 157 | 15 |

EBo pieces filed under CTH 670 or 832 are counted in those bins.

**Orphans** are a smaller group inside this dataset: all CTH 470 fragments and all EBo pieces. They are
the test set of the paper and the Mainz talk. Of the 2,023 orphans with at least five words,
515 are placed (without restorations). They are part of the 2,479 placed fragments
above, with the same placement.

## Two datasets: without and with restorations

| Folder | What counts | Texts scored (5+ words) | Placed | Margin | Held-out accuracy |
|---|---|---|---|---|---|
| `without_restorations/` | Signs visible on the tablet, damaged ones included; a restored word only where the same word survives at least half-preserved elsewhere in the same text | 8,027 | 2,479 | 0.024 | 83% |
| `with_restorations/` | The edition as printed: restored signs count as written | 8,112 | 3,857 | 0.016 | 84% |

Use **`without_restorations/`** for claims about a fragment. With restorations counted, a fragment can
look close to the very text its editor restored it from. Comparing the two shows which results rest on
restored signs: 2,400 fragments are placed in both datasets, 2,395 of them in the same
tradition.

## How a fragment is placed

The method is Quantitative Tradition Mapping (QTM). Each text becomes a list of counts of its words (the lemma of TLHdig's word analysis) and of the sign
sequences (one to three signs) inside its words, weighted by tf-idf. Words that TLHdig 0.4 leaves
without an analysis take the analysis of the same spelling elsewhere in TLHdig, or, for Cuneiform
Luwian, the lemma of eDiAna (2026; CC BY-SA 4.0). Every filled word names its source, the TLHdig line or
the eDiAna entry, in the column `fill_source` of the reproducible token table. Each tradition is the
average of its reference manuscripts (17 or more words). A fragment goes to the most similar tradition (cosine similarity) only if it leads the
runner-up by at least the margin. The margin is calibrated on pieces cut from reference manuscripts,
so that about 80% of placed pieces land in their own tradition; below it the fragment is left
unplaced.

| Tradition | CTH | Manuscripts in TLHdig | Reference manuscripts (without / with restorations) | Most-cited study |
|---|---|---|---|---|
| Arzawa / western rituals | 394, 402, 406, 410, 425, 433 | 43 | 32 / 34 | Mouton 2010 (JCS 62) |
| Hattian cult layer | 591, 627, 725–729, 731–746, 820–821 | 868 | 437 / 478 | Klinger 1996 (StBoT 37) |
| Kizzuwatna rituals | 404, 471–499 | 296 | 211 / 226 | Miller 2004 (StBoT 46) |
| Kizzuwatna–Lower Land (Hurrian) | 628, 699–700, 711–713, 719, 722 | 384 | 303 / 325 | Wegner and Salvini 1991 (ChS I/4) |
| Luwian festivals (Ištanuwa, Lallupiya) | 665, 771–773 | 71 | 48 / 53 | Starke 1985 (StBoT 30) |
| Luwian rituals (Puriyanni, Kuwattalla) | 758–763 | 145 | 58 / 82 | Yakubovich and Mouton 2023 (StBoT 72,1) |
| Mixed (Hurrian, Syrian, Luwian) | 704–706, 720 | 286 | 193 / 202 | Wegner 2002 (ChS I/3-2) |
| Palaic festivals | 750–754 | 60 | 30 / 34 | Steitler 2017 (StBoT 62) |
| Syro-Mesopotamian (Hurrian) | 698, 701, 714–715, 721 | 217 | 149 / 167 | Salvini and Wegner 1986 (ChS I/2) |
| Ḫuwaššanna festivals | 690–694 | 257 | 182 / 194 | Yoshida 1996 (THeth 22) |

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
- The match checks find duplicates far better than joins: of 332 duplicate pairs recorded in the
  Konkordanz, the duplicate is among the twenty nearest manuscripts in 224 (median rank
  4); of 19 proposed joins, 7. A candidate is a lead to check on the tablets.
- Word categories are assigned by rules from TLHdig's automatic word analyses. Nouns and adjectives
  are classed by their German gloss in a lexicon of 5,494 glosses (`lexicon/gloss_lexicon.tsv`).
  Where a gloss has more than one meaning (Horn: a musician's horn or the moon's horn), one of
  39 context rules (`lexicon/sense_rules.csv`) chooses the meaning from the line. Each rule names
  its dictionary reference (HEG, CHD, CAD, CDA) and the examples it rests on. An independent check
  against Open German WordNet covers 30% of the glosses and agrees with the lexicon on 68% of
  them (kappa 0.61). The word lexicon remains to be verified manually.

## How to cite

Gordin, Shai. 2026. *Orphans and Archetypes: closest traditions, compositions and duplicate or join candidates for the unplaced fragments of the Hittite corpus (TLHdig 0.4)*. Version 2.1.0. Zenodo. Please cite TLHdig 0.4 as well.

## How to rebuild

```
git clone https://github.com/shaigordin/measuring-scribal-literacy
cd measuring-scribal-literacy/orphans
python3 -m pip install -r requirements.txt     # Python 3.13
bash reproduce.sh                              # downloads TLHdig 0.4 (checksum-verified) and rebuilds everything
```

## References

Articles are cited as in the Konkordanz (journal and volume).

- Carruba, O. 1966. *Das Beschwörungsritual für die Göttin Wišurijanza*. StBoT 2.
- Carruba, Onofrio. 1970. *Das Palaische: Texte, Grammatik, Lexikon*. StBoT 10.
- eDiAna. 2026. *eDiAna: Digital Philological-Etymological Dictionary of the Minor Ancient Anatolian Corpus Languages*. Ludwig-Maximilians-Universität München, https://www.ediana.gwi.uni-muenchen.de (accessed November 2026). CC BY-SA 4.0.
- Ehelolf, H. 1932. *Mitteilungen der Deutschen Orient-Gesellschaft zu Berlin* 70.
- Goetze, A. 1964. *Journal of Cuneiform Studies* 18.
- Gordin, Shai, Emma Yavasan and Avital Romach. 2025. Matters of Genre, Style and Orthography: Hittite Scribal Habits through the Stylometric Lens. In Susanne Görke, Adam Kryszeń, Gerfrid G. W. Müller and Charles W. Steitler (eds), *The Tablets and Their Scribes: The Palaeography of Hittite Cuneiform and Writing Practices in Hittite Anatolia*. StBoT 73. Wiesbaden: Harrassowitz, 107–123.
- Groddek, D. 2025. Fs van den Hout (not in the Konkordanz's list of abbreviations).
- Groddek, D. 2026. FsTaracha (not in the Konkordanz's list of abbreviations).
- Groddek, Detlev, and Alwin Kloekhorst. 2006. *Hethitische Texte in Transkription: KBo 35*. DBH 19.
- Haas, Volkert. 1994. *Geschichte der hethitischen Religion*. Handbuch der Orientalistik I/15. Leiden: Brill.
- Jakob-Rost, Liane. 1972. *Das Ritual der Malli aus Arzawa gegen Behexung (KUB XXIV 9+)*. THeth 2. Heidelberg: Winter.
- Klinger, Jörg. 1996. *Untersuchungen zur Rekonstruktion der hattischen Kultschicht*. StBoT 37. Wiesbaden: Harrassowitz.
- Košak, Silvin. 2026. *Konkordanz der hethitischen Keilschrifttafeln*. hethiter.net/: hetkonk, https://hethport.net/hetkonk/ (pages accessed November 2026).
- Kümmel, Hans Martin. 1967. *Ersatzrituale für den hethitischen König*. StBoT 3.
- Laroche, Emmanuel. 1971. *Catalogue des textes hittites*. Paris: Klincksieck.
- Mainzer Fotoarchiv. hethiter.net/: fotarch, https://hethport.net/fotarch/.
- Meriggi, P. 1960. *Revue hittite et asianique* XVIII/66-67.
- Miller, Jared L. 2004. *Studies in the Origins, Development and Interpretation of the Kizzuwatna Rituals*. StBoT 46. Wiesbaden: Harrassowitz.
- Mouton, Alice. 2010. Sorcellerie hittite. *Journal of Cuneiform Studies* 62: 105–125.
- Müller, Gerfrid, Doris Prechel, Elisabeth Rieken and Daniel Schwemer. 2026. *Thesaurus Linguarum Hethaeorum digitalis (TLHdig) Beta Version 0.4*. Zenodo. doi:10.5281/zenodo.24373727.
- Otten, Heinrich, and Vladimir Souček. 1969. *Ein althethitisches Ritual für das Königspaar*. StBoT 8.
- Reyhan, E. 2025. *Archivum Anatolicum* 19/2.
- Rieken, Elisabeth, and Daniel Schwemer. 2026. *Corpus der hethitischen Festrituale (HFR)*. Akademie der Wissenschaften und der Literatur Mainz, hethiter.net/: HFR, https://hethport.net/HFR/.
- Rost, L. 1953. *Mitteilungen des Instituts für Orientforschung* 1.
- Roth, Theresa. 2021. *Religiöse Kommunikation im Umbrischen und Hethitischen: Fachsprachlichkeit in Ritualtexten und Gebeten*. BSIEL 23.
- Salvini, Mirjo, and Ilse Wegner. 1986. *Die Rituale des AZU-Priesters*. ChS I/2. Roma: Multigrafica.
- Sasseville, D. 2023. FsKosyan (not in the Konkordanz's list of abbreviations).
- Sasseville, D., and I. Yakubovich. 2021. *Zeitschrift für vergleichende Sprachforschung* 131.
- Sasseville, David. 2020. *Anatolian Verbal Stem Formation: Luwian, Lycian and Lydian*. BSIEL 21.
- Starke, Frank. 1985. *Die keilschrift-luwischen Texte in Umschrift*. StBoT 30. Wiesbaden: Harrassowitz.
- Steitler, Charles W. 2017. *The Solar Deities of Bronze Age Anatolia: Studies in Texts of the Early Hittite Kingdom*. StBoT 62. Wiesbaden: Harrassowitz.
- Torri, Giulia. 2022. *The Haus am Hang at Ḫattuša. A Late Hittite State Scriptorium and Its Tablet Collections*. StBoT 67.
- Vieyra, M. 1965. *Revue d'Assyriologie et d'Archéologie orientale* 59.
- Waal, Willemijn. 2015. *Hittite Diplomatics: Studies in Ancient Document Format and Record Management*. StBoT 57. Wiesbaden: Harrassowitz.
- Wegner, Ilse, and Mirjo Salvini. 1991. *Die hethitisch-hurritischen Ritualtafeln des (ḫ)išuwa-Festes*. ChS I/4. Roma: Multigrafica.
- Wegner, Ilse. 2002. *Hurritische Opferlisten aus hethitischen Festbeschreibungen. Teil II: Texte für Teššub, Ḫebat und weitere Gottheiten*. ChS I/3-2. Roma.
- Yakubovich, Ilya, and Alice Mouton. 2023. *Luwili: Hittite-Luwian Ritual Texts Attributed to Puriyanni, Kuwattalla and Šilalluḫi (CTH 758–763)*. StBoT 72. Wiesbaden: Harrassowitz.
- Yoshida, Daisuke. 1996. *Untersuchungen zu den Sonnengottheiten bei den Hethitern: Schwurgötterliste, helfende Gottheit, Feste*. THeth 22. Heidelberg: Winter.
