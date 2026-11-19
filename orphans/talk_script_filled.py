"""Update ShG's final short script to the filled-data numbers (results/talk_numbers.md)."""
import copy, re, sys
import docx

SRC, OUT = sys.argv[1], sys.argv[2]
d = docx.Document(SRC)
P = d.paragraphs

def setp(i, text, expect=None):
    p = P[i]
    if expect:
        assert expect in p.text, (i, expect, p.text[:80])
    base = p.runs[0]
    for r in p.runs[1:]:
        r._element.getparent().remove(r._element)
    parts = re.split(r"(\*[^*]+\*)", text)
    base.text = ""
    first = True
    for part in parts:
        if not part:
            continue
        ital = part.startswith("*")
        t = part.strip("*") if ital else part
        if first:
            base.text, base.italic, first = t, (True if ital else None), False
        else:
            r = copy.deepcopy(base._element)
            p._element.append(r)
            run = p.runs[-1]
            run.text, run.italic = t, (True if ital else None)

def sub(i, old, new):
    t = P[i].text
    assert old in t, (i, old, t[:100])
    keep = [(r.text, r.italic) for r in P[i].runs]
    ital = {x for x, it in keep if it}
    nt = t.replace(old, new)
    for w in sorted(ital, key=len, reverse=True):
        nt = nt.replace(w, f"*{w}*") if f"*{w}*" not in nt else nt
    setp(i, nt)

setp(8, "KBo 57.54, acts as a warning about computational placements that rest on restorations.", "41.22")
sub(12, "add more than eleven hundred manuscripts (1,110)", "add more than eleven hundred manuscripts (1,151)")
sub(12, "hold close to 3,000 manuscripts (2,944)", "hold just over 3,000 manuscripts (3,034)")
sub(12, "The median CTH 470 fragment has 9 legible words and the median EBo fragment has 3.", "The median CTH 470 fragment has 10 legible words and the median EBo fragment has 4.")
sub(17, "1,766 orphans", "2,023 orphans")
sub(22, "It counts forty-nine surviving words", "It counts fifty surviving words")
sub(34, "weighs 1.9", "weighs 2.0")
sub(36, "That bar is 0.028.", "That bar is 0.026.")
sub(36, "leads by 0.12.", "leads by 0.11.")
sub(37, "for KBo 44.52, AZU, dai and SÍSKUR.", "for KBo 44.52, dai, AZU and SÍSKUR.")
sub(45, "Each of 1,350 reference manuscripts", "Each of 1,634 reference manuscripts")
sub(45, "82 percent return to their own tradition, against 29 percent for always guessing the largest tradition and 17 percent with shuffled labels.",
    "83 percent return to their own tradition, against 27 percent for always guessing the largest tradition and 16 percent with shuffled labels.")
setp(47, "The festivals that HFR separates are also kept apart by the texts themselves: the Ḫuwaššanna festivals reach 92 percent, those of Ištanuwa and Lallupiya 79. Even the two smallest ritual groups, the western rituals and the Luwian rituals, reach 88 and 81 percent. The tradition to which KBo 44.52 probably belongs, the Syro-Mesopotamian, finds its own manuscripts two times out of three.", "HFR separates")
setp(48, "One step lies behind these numbers. The model reads the words that TLHdig has analysed, and the current release leaves many words without an analysis, among them all the Luwian rituals of Puriyanni and Kuwattalla, CTH 758 to 763. So we fill these gaps: a word without an analysis takes the analysis of the same spelling elsewhere in TLHdig, and a Luwian word takes its lemma from *eDiAna*, the online dictionary of the minor Anatolian languages. This adds about 95,000 words, and the Luwian rituals grow from 10 to 57 reference manuscripts.", "one limit")
sub(50, "56 of 78 compositions", "72 of 94 compositions")
sub(50, "all 18 copies hidden", "all 30 copies hidden")
sub(57, "Vocabulary alone returns 66 percent", "Vocabulary alone returns 67 percent")
sub(57, "even better, 81 percent", "even better, 79 percent")
sub(58, "do this in 17 percent of cases, the Hattian layer in 12, the Kizzuwatna rituals in 3,", "do this in 18 percent of cases, the Hattian layer in 12, the Kizzuwatna rituals in 1,")
sub(58, "against 29 for guessing", "against 27 for guessing")
sub(59, "we took the 203 words", "we took the 273 words")
sub(59, "45 percent with the spelling, 50 without.", "50 percent with the spelling, 54 without.")
setp(62, "Some contrasts are clear. The Hattian cult layer writes fewer logograms and more *plene* writing, which may reflect the date of its Old Hittite manuscripts as much as the tradition. The Palaic festivals add many phonetic complements. Ḫuwaššanna uses more Akkadograms and determinatives; the Luwian rituals fewer Akkadograms and determinatives, and the Kizzuwatna rituals fewer determinatives.", "Some contrasts")
sub(65, "at 0.30.", "at 0.31.")
setp(66, "The lead is 0.11. The threshold is 0.026. The fragment is placed, by more than four times the margin it needs.", "The lead is")
sub(70, "47 percent of the similarity but only 11 percent of the decision.", "47 percent of the similarity but only 12 percent of the decision.")
sub(70, "they carry less than a quarter.", "they carry just over a quarter.")
sub(73, "27 matches; the next tradition has 11.", "28 matches; the next tradition has 12.")
setp(80, "Now for a mischief orphan: KBo 57.54, a small fragment from old excavation debris in the area of Temple I, filed under CTH 470. Using the restored text, it is placed with the Luwian rituals of Puriyanni and Kuwattalla, with a lead more than three times the threshold.", "mischief")
setp(81, "The deciding word is the practitioner, the Old Woman, MUNUS ŠU.GI. Both times only the determinative MUNUS survives, in line 7′ only in part, and the editor restores ŠU.GI after it. Counting only what is visible on the tablet leaves 11 of its 13 words, and the lead falls below the threshold; the nearest tradition even changes, to the Syro-Mesopotamian rituals. So, the fragment cannot be decisively placed.", "deciding formula")
setp(82, "The restoration may well be right. But a placement that rests on it only finds the parallel that the editor of the text had in mind. Nor is it a single case: 14 orphans are placed with the Luwian rituals only when restorations count, and every one of them has a restored Old Woman. This is why the main results count only what is on the tablet. And it is a general point: across the orphans, 87 percent keep the same nearest tradition when restorations are removed. What we lose is confidence, more than direction.", "may well be right")
sub(84, "Our data hold 1,110 of them.", "Our data hold 1,151 of them.")
sub(84, "with a median of three legible words", "with a median of four legible words")
sub(89, "Of the 55 reference manuscripts in which takarmu is visible, 47 are", "Of the 62 reference manuscripts in which takarmu is visible, 54 are")
sub(90, "And 32 more festival fragments", "And 37 more festival fragments")
sub(92, "which out of 16,604 manuscripts", "which out of 19,197 manuscripts")
setp(93, "Two pass all three criteria: KBo 44.140 and a Palaic festival tablet, DBH 46/2.139. Both share “he drinks once, he breaks one *takarmu*-bread”. KBo 44.140 is a New Hittite festival tablet from building A on Büyükkale, filed under CTH 669.", "passes all three")
sub(101, "home to 380 of 1,766 orphans", "home to 457 of 2,023 orphans")
d.save(OUT)
print("ok")
