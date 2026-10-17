"""Reference traditions and orphan definitions.

HISTORICAL follows Table 3 of Gordin, Yavasan & Romach 2025 (StBoT 73: 112),
which groups the Hurrian and Luwian festival CTHs by geographic or cultural
background. Two ritual groups are added because the CTH 470 orphans are ritual
fragments, so a festivals-only reference space would have no ritual
tradition to match them to.
"""

HISTORICAL = {
    "Kizzuwatna–Lower Land (Hurrian)": [628, 699, 700, 711, 712, 713, 719, 722],
    "Syro-Mesopotamia (Hurrian)": [698, 701, 714, 715, 721],
    "Luwian cult centres": [665, 690, 691, 692, 693, 694, 770, 771, 772, 773],
    "Mixed (Hurrian, Syrian, Luwian)": [704, 705, 706, 720],
    # added controls: ritual traditions
    "Kizzuwatna rituals": list(range(471, 501)),
    "Old Anatolian rituals": list(range(390, 470)),
}

# Literature-defined reference traditions (decision 2026-10-16: ground each group in the study
# that argued for it; Laroche's CTH numbers stay the address of every text). See the doc
# "Hittite ritual traditions: baselines and literature" for the sources.
LITERATURE = {
    # StBoT 73 Table 3, Hurrian groups unchanged
    "Kizzuwatna–Lower Land (Hurrian)": HISTORICAL["Kizzuwatna–Lower Land (Hurrian)"],
    "Syro-Mesopotamia (Hurrian)": HISTORICAL["Syro-Mesopotamia (Hurrian)"],
    "Mixed (Hurrian, Syrian, Luwian)": HISTORICAL["Mixed (Hurrian, Syrian, Luwian)"],
    # StBoT 73's "Luwian cult centres" split as the HFR edition modules split it (Hethitische
    # Festrituale, hethport.net/HFR, edition_liste.php, accessed 2026-10-17; decision 2026-10-17):
    # Luwian festivals as HFR lists them (665, 771-773; CTH 770 is not in the module and is left
    # out), Ḫuwaššanna (690-694, Laroche titles), and HFR's Palaic festivals (750-754).
    "Luwian festivals (Ištanuwa, Lallupiya)": [665, 771, 772, 773],
    "Ḫuwaššanna festivals": [690, 691, 692, 693, 694],
    "Palaic festivals": [750, 751, 752, 753, 754],
    # Miller 2004 (StBoT 46), Strauß 2006, Görke 2010: Laroche's Kizzuwatna block plus Maštigga (CTH 404).
    # CTH 500 ("Kizzuwatna ritual fragments", 235 of 399 manuscripts) is a fragment category, not an
    # identified composition: it made the class a generic-ritual attractor, so it is placed, not used
    # (decision 2026-10-17).
    "Kizzuwatna rituals": list(range(471, 500)) + [404],
    # Western (Arzawa) rituals: practitioners whose colophon names Arzawa or Ḫapalla, Ašḫella (394),
    # Alli (402), Paškuwatti (406), Uḫḫamuwa (410) (CTH titles; Mouton 2010, Bawanypeck 2013), and the
    # augur rituals (Bawanypeck 2005, THeth 25: CTH 425, 433), one of which names an augur from Arzawa
    # (Archi 2015, BiOr 72: the augur rituals are held to be western Anatolian, in particular Arzawan).
    # The Ambazzi rituals (CTH 391, 429, 463; Christiansen 2006, StBoT 48) show Luwian influence but
    # no stated link to Arzawa, so they left the group on 2026-10-17 and are placed like orphans.
    "Arzawa / western rituals": [394, 402, 406, 410, 425, 433],
    # Luwian rituals of Puriyanni, Kuwattalla and Šilalluḫi (Yakubovich and Mouton 2023, Luwili, StBoT 72;
    # Mouton and Yakubovich 2021, JLR 19/1): a Lower Land tradition, not Kizzuwatna. Added 2026-10-17.
    "Luwian rituals (Puriyanni, Kuwattalla)": [758, 759, 760, 761, 762, 763],
    # Klinger 1996 (StBoT 37): Monatsfest and KI.LAM editions, Hattian and Hattian-Hittite texts.
    # From the Portal Konkordanz citations of StBoT 37 (CTH 730 is not cited there).
    "Hattian cult layer": [591, 627] + [c for c in range(725, 747) if c != 730] + [820, 821],
}
# CTH 390-469 texts that no defining study claims: not a reference tradition, placed like orphans
# CTH 500 (Kizzuwatna ritual fragments) is placed the same way.
RESIDUE = {"CTH 390–469 residue": [c for c in range(390, 470) if c not in LITERATURE["Arzawa / western rituals"]
                                   and c not in LITERATURE["Kizzuwatna rituals"]],
           "CTH 500 Kizzuwatna fragments": [500]}

GROUPSETS = {"historical": HISTORICAL, "literature": LITERATURE}

# the three CTHs named in the abstract
ABSTRACT = {"CTH 670": [670], "CTH 701": [701], "CTH 832": [832]}


def label_map(groups):
    return {str(c): g for g, cs in groups.items() for c in cs}


def is_orphan(txtid: str, cth: str) -> bool:
    """Orphans are all CTH 470 fragments and all EBo texts. The experiments load only the CTHs they
    use (the reference groups, CTH 470, and the fragment pools CTH 670 and 832), so in practice an
    EBo text counts when TLHdig files it under one of those; see corpus_stats.json for the rest."""
    return cth == "470" or str(txtid).startswith("EBo")
