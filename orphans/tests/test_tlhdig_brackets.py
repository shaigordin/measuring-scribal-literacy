"""Brackets in TLHdig are line-bound (qtm.tlhdig.line_start_states). Run: python3 -m pytest tests"""
from lxml import etree

from qtm.tlhdig import parse_file

DOC = """<AOxml><body><div1><text><docID>Test 1</docID>
<lb lnr="1'"/> <w trans="tuḫḫuš~"><laes_in/>túḫ-ḫu<laes_fin/>-u<del_in/>š-</w>
<lb lnr="2'"/> <w trans="watarnaḫḫan">w<del_in/>a<del_fin/>-a<corr c="!"/>-tar-na-<laes_in/>aḫ-ḫa-an<laes_fin/></w> <w trans="ḫarzi">ḫar-zi</w> <w><del_in/></w>
<lb lnr="3'"/> <w trans="nankan">na-an-kán</w> <w trans="kuit">ku-it</w>
<lb lnr="4'"/> <w><space c="78"/></w> <w trans="taraškezi">tar<del_fin/>-aš-ke-ez-zi</w> <w trans="nu">nu</w>
<lb lnr="5'"/> <w trans="ammuk">am-<laes_in/>mu-uk</w>
<lb lnr="6'"/> <w trans="ḫarmi">ḫar-<del_in/>mi<del_fin/></w>
<lb lnr="7'"/> <w><space c="20"/></w> <w trans="paiši">pa<del_fin/>-i-ši</w>
</text></div1></body></AOxml>"""


def rows(tmp_path):
    f = tmp_path / "t.xml"
    f.write_text(DOC, encoding="utf8")
    return {r[5]: r[10] for r in parse_file(f, "000", "TEST")}  # word -> status


def test_open_bracket_does_not_run_into_next_line(tmp_path):
    st = rows(tmp_path)
    assert st["tuḫḫuš~"] == "DDD"           # ⸢túḫ-ḫu⸣-u[š- at the end of line 1 ...
    assert st["watarnaḫḫan"] == "DPPPDDD"   # ... does not make w[a] of line 2 wholly restored: w[a]-a!-tar-na-⸢aḫ-ḫa-an⸣
    assert st["nankan"] == "PPP"            # line 3 has no brackets: preserved, though line 2 ends open
    assert st["kuit"] == "PP"


def test_line_beginning_with_closing_bracket(tmp_path):
    st = rows(tmp_path)
    assert st["taraškezi"] == "RPPPP"       # [x x tar]-aš-ke-ez-zi: the line starts inside the bracket
    assert st["nu"] == "P"


def test_half_brackets_are_line_bound_too(tmp_path):
    st = rows(tmp_path)
    assert st["ammuk"] == "PDD"
    assert st["ḫarmi"] == "PR"


def test_closing_bracket_after_a_closed_line(tmp_path):
    st = rows(tmp_path)
    assert st["paiši"] == "RPP"             # line 6 closes its bracket; line 7 still starts inside one: [x pa]-i-ši
