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

# the three CTHs named in the abstract
ABSTRACT = {"CTH 670": [670], "CTH 701": [701], "CTH 832": [832]}


def label_map(groups):
    return {str(c): g for g, cs in groups.items() for c in cs}


def is_orphan(txtid: str, cth: str) -> bool:
    """Orphans are all CTH 470 fragments and all EBo texts, wherever TLHdig files them."""
    return cth == "470" or str(txtid).startswith("EBo")
