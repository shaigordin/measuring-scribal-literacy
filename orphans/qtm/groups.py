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
    # StBoT 73 Table 3, unchanged
    "Kizzuwatna–Lower Land (Hurrian)": HISTORICAL["Kizzuwatna–Lower Land (Hurrian)"],
    "Syro-Mesopotamia (Hurrian)": HISTORICAL["Syro-Mesopotamia (Hurrian)"],
    "Luwian cult centres": HISTORICAL["Luwian cult centres"],
    "Mixed (Hurrian, Syrian, Luwian)": HISTORICAL["Mixed (Hurrian, Syrian, Luwian)"],
    # Miller 2004 (StBoT 46), Strauß 2006, Görke 2010: Laroche's Kizzuwatna block plus Maštigga (CTH 404)
    "Kizzuwatna rituals": list(range(471, 501)) + [404],
    # Christiansen 2006 (StBoT 48: Ambazzi, CTH 391, 429, 463); Bawanypeck 2005 (augurs, CTH 425, 433)
    "Arzawa / western rituals": [391, 425, 429, 433, 463],
    # Klinger 1996 (StBoT 37): Monatsfest and KI.LAM editions, Hattian and Hattian-Hittite texts.
    # From the Portal Konkordanz citations of StBoT 37 (CTH 730 is not cited there).
    "Hattian cult layer": [591, 627] + [c for c in range(725, 747) if c != 730] + [820, 821],
}
# CTH 390-469 texts that no defining study claims: not a reference tradition, placed like orphans
RESIDUE = {"CTH 390–469 residue": [c for c in range(390, 470) if c not in LITERATURE["Arzawa / western rituals"]
                                   and c not in LITERATURE["Kizzuwatna rituals"]]}

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
