"""Checks the deliverables of a data-room request-list task.

It checks the table's shape; that each request in task.json has a row; that the required columns are filled; that
percentages have one decimal place and ratios two; that every cited document version exists and is current in the
data room's own index and every Q&A reference exists; that each source has saved evidence, in a file named for exactly
that document version or Q&A entry; that no view-only document has been copied into the workspace; and that every
delivered file opens as the type its name says. It knows nothing about the right answers. Run it with
`python3 -I check_answers.py`; it exits non-zero on any failure.
"""

import csv
import html
import json
import re
import sys
import urllib.request
import zipfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASK = json.loads((ROOT / "task.json").read_text(encoding="utf-8"))
ROOM = TASK["room"].rstrip("/")
REQUESTS = set(TASK["requests"])
HEADER = ["Request", "Item", "Answer", "Unit", "Period", "Basis", "Source", "Location", "Note"]
REQUIRED = ["Item", "Answer", "Unit", "Period", "Basis", "Source", "Location"]
TABLE = ROOT / "deliverables" / "answers.csv"
FILES = ROOT / "deliverables" / "files"
EVIDENCE = ROOT / "evidence"
DOC_REF = re.compile(r"^(\d+\.\d+) v(\d+)$")
QA_REF = re.compile(r"^Q-\d+$")
NOTE_SUFFIXES = {".md", ".txt"}


def fetch(path, parse=True):
    # The data room's host refuses Python's default client name.
    request = urllib.request.Request(ROOM + path, headers={"User-Agent": "request-list-check/2"})
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read()
    return json.loads(body) if parse else body.decode("utf-8")


def entries(data, *keys):
    if isinstance(data, list):
        return data
    for key in keys:
        if isinstance(data.get(key), list):
            return data[key]
    raise ValueError(f"unexpected JSON shape with keys {sorted(data)}")


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def long_lines(markup):
    parser = Text()
    parser.feed(markup)
    text = html.unescape(" ".join(parser.parts))
    pieces = re.split(r"(?<=[.;:])\s+|\s{2,}", " ".join(text.split()))
    return [piece.strip() for piece in pieces if len(piece.strip()) >= 40]


def evidence_for(stem):
    # Exactly this version: "2.1-v1.txt" or "2.1-v1-notes.md", never "2.1-v10.txt".
    pattern = re.compile(rf"^{re.escape(stem)}(?:[.\-_].*)?$")
    return [p for p in EVIDENCE.rglob("*") if p.is_file() and pattern.match(p.name)] if EVIDENCE.exists() else []


def opens(path):
    suffix = path.suffix.lower()
    head = path.read_bytes()[:8]
    if path.stat().st_size == 0:
        return "is empty"
    if suffix == ".pdf":
        if not head.startswith(b"%PDF"):
            return "isn't a PDF"
        try:
            from pypdf import PdfReader
            return None if len(PdfReader(path).pages) > 0 else "has no pages"
        except Exception as error:
            return f"doesn't open as a PDF ({error.__class__.__name__})"
    if suffix in (".xlsx", ".xlsm"):
        try:
            import openpyxl
            book = openpyxl.load_workbook(path, read_only=True)
            return None if book.sheetnames else "has no sheets"
        except (zipfile.BadZipFile, Exception) as error:
            return f"doesn't open as a workbook ({error.__class__.__name__})"
    if suffix in (".html", ".htm"):
        return None if b"<" in path.read_bytes()[:2048] else "isn't HTML"
    return None


def main():
    failures = []
    if not TABLE.exists():
        print(f"FAIL {TABLE.relative_to(ROOT)} doesn't exist")
        return 1
    with TABLE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0] != HEADER:
        failures.append(f"the header row must be exactly {','.join(HEADER)}")
        rows = [HEADER]
    records = []
    for number, row in enumerate(rows[1:], start=2):
        if not any(cell.strip() for cell in row):
            continue
        if len(row) != len(HEADER):
            failures.append(f"row {number}: {len(row)} columns, not {len(HEADER)}")
        records.append((number, dict(zip(HEADER, row))))

    index = entries(fetch("/data/index.json"), "documents")
    documents = {(d["index"], int(d["version"])): d for d in index}
    questions = {q["id"] for q in entries(fetch("/data/qa.json"), "entries", "questions", "qa")}

    answered = set()
    for number, record in records:
        where = f"row {number}"
        request = record.get("Request", "").strip()
        if not request.isdigit() or int(request) not in REQUESTS:
            failures.append(f"{where}: Request must be one of {sorted(REQUESTS)}, not {request!r}")
            continue
        answered.add(int(request))
        for column in REQUIRED:
            if not record.get(column, "").strip():
                failures.append(f"{where}: {column} is empty (write n/a where it doesn't apply)")
        unit, answer = record.get("Unit", "").strip().lower(), record.get("Answer", "").strip()
        if unit in ("%", "percent", "per cent") and not re.fullmatch(r"-?\d+\.\d", answer):
            failures.append(f"{where}: a percentage needs one decimal place, not {answer!r}")
        if unit in ("x", "times", "ratio") and not re.fullmatch(r"-?\d+\.\d\d(?::1)?", answer):
            failures.append(f"{where}: a ratio needs two decimal places, not {answer!r}")
        for source in filter(None, (part.strip() for part in record.get("Source", "").split(";"))):
            if QA_REF.match(source):
                if source not in questions:
                    failures.append(f"{where}: {source} isn't in the data room's Q&A")
                stem = source
            elif match := DOC_REF.match(source):
                key = (match[1], int(match[2]))
                if key not in documents:
                    failures.append(f"{where}: {source} isn't in the data room's index")
                elif documents[key]["status"] != "current":
                    failures.append(f"{where}: {source} is {documents[key]['status']}, not current")
                stem = f"{match[1]}-v{match[2]}"
            else:
                failures.append(f"{where}: write the source as '2.4 v1' or 'Q-07', not {source!r}")
                continue
            found = evidence_for(stem)
            if not found:
                failures.append(f"{where}: no evidence saved for {source} (expected evidence/{stem}.txt or similar)")
            elif all(p.stat().st_size == 0 for p in found):
                failures.append(f"{where}: the evidence for {source} is empty")

    for request in sorted(REQUESTS - answered):
        failures.append(f"request {request} has no row")

    # View-only documents may be read and noted, never copied: evidence for one is a note in your own words.
    workspace_text = {}
    for path in ROOT.rglob("*"):
        if path.is_file() and ".git" not in path.parts and path.stat().st_size < 5_000_000:
            workspace_text[path] = path.read_bytes().decode("utf-8", "ignore")
    for doc in index:
        if not doc.get("view_only"):
            continue
        stem = f'{doc["index"]}-v{doc["version"]}'
        for path in evidence_for(stem):
            if path.suffix.lower() not in NOTE_SUFFIXES:
                failures.append(f"{path.relative_to(ROOT)}: {doc['index']} is view only, so keep a .md or .txt note, not a {path.suffix} copy")
        if not doc.get("content"):
            continue
        lines = long_lines(fetch("/" + doc["content"], parse=False))
        if not lines:
            continue
        for path, text in workspace_text.items():
            flat = " ".join(html.unescape(text).split())
            copied = sum(1 for line in lines if line in flat)
            if copied >= 5 or copied >= 0.4 * len(lines):
                failures.append(f"{path.relative_to(ROOT)}: holds {copied} of {len(lines)} passages of view-only document "
                                f"{doc['index']}; note the facts you need in your own words instead")

    delivered = sorted(p for p in FILES.rglob("*") if p.is_file()) if FILES.exists() else []
    if not delivered:
        failures.append("deliverables/files/ is empty")
    for path in delivered:
        problem = opens(path)
        if problem:
            failures.append(f"{path.relative_to(ROOT)} {problem}")

    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{len(records)} rows, requests answered: {sorted(answered)}, {len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
