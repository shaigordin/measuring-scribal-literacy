"""Do the parser's workarounds (qtm/tlhdig.py) still hold on a TLHdig release? Counts, per release:

- files the parser cannot read (logged and skipped by parse_release);
- manuscripts present in both an HFR and a TLH folder (parse_release keeps the HFR copy);
- the bracket reading: TLHdig brackets are line-bound (line_start_states). For every line that begins
  inside a bracket (its first milestone of a kind closes it) we count whether the line before left that
  bracket open. If brackets ran on from line to line, this would always be so; every line where it is
  not so needs the line-bound reading. Lines that end with a bracket open are counted too.
- words whose sign marks do not align with the transliteration (from the parser log, passed in).

    python3 check_tlhdig_release.py data/TLHbasisONLINE25_1_ZENODO_Beta_04 data/parse.err results/tlhdig04/release_check.json
"""
import json, re, sys
from collections import Counter
from pathlib import Path

from lxml import etree

from qtm.tlhdig import FOLDER, PAIRS, _MILESTONE, _local


def check(root):
    c, ids = Counter(), {}
    for d in sorted(Path(root).iterdir()):
        m = FOLDER.match(d.name)
        if not m:
            continue
        for f in sorted(d.rglob("*.xml")):
            ids.setdefault(f.stem, set()).add(m.group(2) if m.group(2) == "HFR" else "other")
            try:
                tree = etree.parse(str(f), etree.XMLParser(recover=True, huge_tree=True))
                r = tree.getroot()
                if r is None:
                    raise ValueError("no root")
            except Exception:
                c["files_unreadable"] += 1
                continue
            c["files"] += 1
            prev_end, first, cur = {}, None, None
            for el in r.iter():
                tag = _local(el)
                if tag == "lb":
                    if cur is not None:
                        prev_end = cur
                    c["lines"] += 1
                    cur, first = dict(prev_end), {}
                    continue
                if cur is None or tag not in _MILESTONE:
                    continue
                kind, opens = _MILESTONE[tag]
                if kind not in first:
                    first[kind] = opens
                    if not opens:  # the line begins inside this bracket
                        c[f"{kind}_line_starts_inside"] += 1
                        c[f"{kind}_previous_line_left_open" if prev_end.get(kind) else f"{kind}_previous_line_closed"] += 1
                cur[kind] = opens
            # end state of the last line is not followed by a line: not counted
    both = sum(1 for v in ids.values() if v == {"HFR", "other"})
    out = dict(c)
    out["manuscripts_in_HFR_and_TLH_folders"] = both
    return out


def main(xml, parse_err, out):
    res = check(xml)
    err = Path(parse_err).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"sign marks: (\d+) of (\d+) words not aligned", err)
    res["words_unaligned"], res["words"] = (int(m.group(1)), int(m.group(2))) if m else (None, None)
    res["parser_skipped"] = [l.split(": ", 1)[0][5:] for l in err.splitlines() if l.startswith("skip ")]
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(json.dumps(res, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(*sys.argv[1:4])
