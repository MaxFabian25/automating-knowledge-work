"""Tests score.py against hand-made Tansy answer tables: a correct one, and one mistake at a time.

Usage: python3 -I test_score.py <score-key.json>
"""

import contextlib
import csv
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score  # noqa: E402

HEADER = ["Request", "Item", "Answer", "Unit", "Period", "Basis", "Source", "Location", "Note"]
CORRECT = [
    [1, "Revenue", "68,020", "GBP thousands", "Twelve months to 30 September 2026", "Management accounts", "2.3 v1; 2.4 v1", "P&L", ""],
    [1, "EBITDA before exceptional items", "9,260", "GBP thousands", "Twelve months to 30 September 2026", "Management accounts", "2.3 v1; 2.4 v1", "P&L", ""],
    [2, "Revenue growth as reported", "20.8", "%", "H1", "Management accounts", "2.4 v1", "P&L", ""],
    [2, "Organic revenue growth", "14.3", "%", "H1", "Management accounts", "2.4 v1", "Notes", ""],
    [3, "Revenue", "61,800", "GBP thousands", "FY2026", "Audited", "2.2 v1", "p. 3", ""],
    [3, "Operating profit", "5,630", "GBP thousands", "FY2026", "Audited", "2.2 v1", "p. 3", ""],
    [3, "Revenue", "51,650", "GBP thousands", "FY2025 (restated)", "Audited", "2.2 v1", "p. 3", "Restated"],
    [3, "Operating profit", "4,550", "GBP thousands", "FY2025 (restated)", "Audited", "2.2 v1", "p. 3", ""],
    [4, "Maximum leverage permitted", "3.25", "x", "Test date 30 September 2026", "Facility", "2.11 v1", "para 2", ""],
    [4, "Leverage reported", "2.84", "x", "Test date 30 September 2026", "Certificate", "2.8 v1", "p. 1", ""],
    [5, "Contingent consideration outstanding", "Not disclosed in the data room", "GBP thousands", "n/a", "n/a", "2.2 v1; Q-09", "note", ""],
    [6, "Wendmoor Housing Group", "5,960", "GBP thousands", "FY2026", "Management accounts", "3.1 v1", "Top customers", ""],
    [6, "Larchfold Facilities Management Ltd", "4,310", "GBP thousands", "FY2026", "Management accounts", "3.1 v1", "Top customers", ""],
    [6, "Dunstreath Retail Group plc", "3,420", "GBP thousands", "FY2026", "Management accounts", "Q-06", "Q&A", "Lost customer"],
    [6, "Corrigal Retail Parks plc", "3,240", "GBP thousands", "FY2026", "Management accounts", "3.1 v1", "Top customers", ""],
    [6, "Combined share of FY2026 revenue", "27.3", "%", "FY2026", "Management accounts", "3.1 v1; Q-06", "", ""],
    [7, "Lender consent", "Yes; Majority Lenders' consent needed", "n/a", "n/a", "Facility", "2.7 v1", "Change of control", ""],
    [8, "Total quantified claim", "€642,500", "EUR", "Letter of claim", "Claimed", "6.2 v1", "p. 1", ""],
    [8, "Claim at the closing rate", "543", "GBP thousands", "31 March 2026 rate", "Converted", "6.2 v1; 2.2 v1", "", ""],
    [8, "Provision for the claim", "210", "GBP thousands", "31 March 2026", "Audited", "2.2 v1", "Provisions", ""],
    [9, "Total FTE", "609.8", "FTE", "30 September 2026", "Census", "4.1 v2", "Summary", ""],
    [9, "Kilcarrow FTE", "58.6", "FTE", "30 September 2026", "Census", "4.1 v2", "Summary", ""],
    [10, "Document 4.2", "Not sent: view only", "n/a", "n/a", "n/a", "4.2 v1", "Viewer", "Ask the vendor to release it"],
]


def run(key, rows, files=None):
    with tempfile.TemporaryDirectory() as tmp:
        table = Path(tmp, "answers.csv")
        with table.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            writer.writerows(rows)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            hits, total, pending = score.score(key, table, files)
        return hits, total, out.getvalue()


def edit(rows, request, item_word, column, value):
    changed = [list(r) for r in rows]
    for r in changed:
        if r[0] == request and item_word.lower() in r[1].lower():
            r[HEADER.index(column)] = value
    return changed


def main():
    key = json.loads(Path(sys.argv[1]).read_text())
    dist = Path(key["dist"])
    index = json.loads((dist / "data/index.json").read_text())
    names = {d["id"]: d["file"] for d in index["documents"] if d.get("file")}
    files = Path(tempfile.mkdtemp())
    for doc in key["files"]["required"]:
        shutil.copyfile(dist / "files" / names[doc], files / names[doc])

    hits, total, out = run(key, CORRECT, files)
    pending = sum(len(m["points"]) for m in key["manual"])
    results = [("correct table scores every mechanical check", hits == total - pending, out)]

    def expect_drop(name, rows, word, use_files=files):
        h, t, o = run(key, rows, use_files)
        results.append((name, h < hits and word in o, o))

    swapped = edit(edit(CORRECT, 4, "maximum", "Answer", "2.84"), 4, "reported", "Answer", "3.25")
    expect_drop("swapped covenant values fail", swapped, "Maximum leverage")
    expect_drop("a wrong sign fails", edit(CORRECT, 1, "revenue", "Answer", "-68,020"), "LTM revenue")
    expect_drop("too coarse a figure fails", edit(CORRECT, 2, "organic", "Answer", "14"), "Organic growth")
    expect_drop("the superseded census fails", edit(CORRECT, 9, "total", "Source", "4.1 v1"), "Group FTE")
    extra = CORRECT + [[6, "Thornacre Care Homes Ltd", "2,980", "GBP thousands", "FY2026", "Management accounts", "3.1 v1", "", ""]]
    expect_drop("an extra qualifying customer fails the set", extra, "customers over 5%")
    without = [r for r in CORRECT if "Dunstreath" not in r[1]]
    expect_drop("leaving out the lost customer fails", without, "Dunstreath")
    restated = edit(edit(CORRECT, 3, "revenue", "Answer", "52,400"), 3, "revenue", "Period", "FY2025")
    expect_drop("FY2025 as first reported fails", [r for r in restated if not (r[0] == 3 and r[4] == "FY2025" and r[2] != "52,400")] + [r for r in CORRECT if r[0] == 3 and "2026" in r[4]], "FY2025 revenue")
    expect_drop("a missing file fails", CORRECT, "file 3.1-v1", None)

    alt = edit(CORRECT, 4, "maximum", "Source", "Q-07")
    h, t, o = run(key, alt, files)
    results.append(("an alternative valid citation passes", h == hits, o))
    mentioned = CORRECT + [[6, "Thornacre Care Homes Ltd (below 5%)", "2,980", "GBP thousands", "FY2026", "", "3.1 v1", "", "Not over 5%"]]
    h, t, o = run(key, mentioned, files)
    results.append(("a customer named as below the threshold doesn't fail the set", h == hits, o))
    h, t, o = run(key, edit(CORRECT, 1, "revenue", "Answer", "68,020 (62,090 - 28,450 + 34,380)"), files)
    results.append(("a pitfall value shown as an input flags without failing", h == hits and "FLAG" in o, o))
    copy_dir = Path(tempfile.mkdtemp())
    shutil.copytree(files, copy_dir, dirs_exist_ok=True)
    shutil.copyfile(dist / "content" / "4.2-v1.html", copy_dir / "senior-management.html")
    expect_drop("a copy of the view-only document fails", CORRECT, "terms breach", copy_dir)

    failed = 0
    for name, ok, out in results:
        print(("PASS " if ok else "FAIL ") + name)
        if not ok:
            failed += 1
            print("   " + out.replace("\n", "\n   ")[:1500])
    shutil.rmtree(files)
    shutil.rmtree(copy_dir)
    print(f"{len(results) - failed} of {len(results)} scorer tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
