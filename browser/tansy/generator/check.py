#!/usr/bin/env python3
"""Check a built data room against its case sources.

Usage: python3 -I check.py [--case dev-larkspur]

Verifies that every indexed document exists in dist/, that Q&A references
point at real documents, that every answer-key fact appears in the cited
document (XLSX cells are read with openpyxl, HTML and PDF as text), that the
figures reconcile as cases/<case>/reconciliations.json describes, and that
the site keeps its rules (banner on every page, no external requests, answer
key and request list never served). Exits non-zero on any failure.
"""

import argparse
import html
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

import openpyxl
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
HEADER_ROW = 5
TOLERANCE = 0.005


class Report:
    def __init__(self):
        self.failures = []
        self.passes = {}

    def ok(self, section):
        self.passes[section] = self.passes.get(section, 0) + 1

    def fail(self, section, message):
        self.failures.append(f"[{section}] {message}")

    def check(self, section, condition, message):
        if condition:
            self.ok(section)
        else:
            self.fail(section, message)
        return condition


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_jsonc(path):
    text = Path(path).read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|[^:\"])//[^\n]*", r"\1", text)
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    return json.loads(text)


# ---------------------------------------------------------------- text

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        self.parts.append(" ")

    def handle_endtag(self, tag):
        self.parts.append(" ")

    def handle_data(self, data):
        self.parts.append(data)


def normalise(text):
    text = html.unescape(text)
    text = text.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    text = re.sub("[\\s\u00a0\u202f\u2009]+", " ", text)
    return text.strip()


def html_text(markup):
    p = TextExtractor()
    p.feed(markup)
    return normalise("".join(p.parts))


def pdf_text(path):
    reader = PdfReader(path)
    return normalise(" ".join(page.extract_text() or "" for page in reader.pages))


def number_pattern(text):
    """Match a number only where it is not part of a longer number."""
    return re.compile(r"(?<![\d,.])" + re.escape(text) + r"(?![\d]|,\d|\.\d)")


def contains(haystack, needle):
    needle = normalise(needle)
    if re.fullmatch(r"[\d,.()]+", needle):
        return bool(number_pattern(needle).search(haystack))
    return needle in haystack


def default_text(value):
    if isinstance(value, float):
        return f"{value:,.2f}" if value != round(value, 1) else f"{value:,.1f}"
    if isinstance(value, int):
        return f"{value:,}" if value > 0 else (f"({abs(value):,})" if value < 0 else "-")
    return str(value)


def displayed_cell(cell):
    value, fmt = cell.value, cell.number_format
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return str(value) if value is not None else ""
    if fmt == '#,##0;(#,##0);"-"':
        return f"{value:,.0f}" if value > 0 else (f"({abs(value):,.0f})" if value < 0 else "-")
    formats = {"0.0": (1, ""), "0.00": (2, ""), "0.0000": (4, ""), '0.00":1"': (2, ":1"), "0.0%": (1, "%")}
    if fmt in formats:
        digits, suffix = formats[fmt]
        return f"{value * (100 if suffix == '%' else 1):.{digits}f}{suffix}"
    raise KeyError(f"unsupported displayed numeric format {fmt!r} at {cell.coordinate}")


# ---------------------------------------------------------------- the built room

class Room:
    def __init__(self, case_dir):
        self.case_dir = case_dir
        self.case = load_json(case_dir / "index.json")
        self.model = load_json(case_dir / "model.json")
        self.qa = load_json(case_dir / "qa.json")
        self.public = load_json(DIST / "data" / "index.json")
        self.public_qa = load_json(DIST / "data" / "qa.json")
        self.docs = {d["id"]: d for d in self.public["documents"]}
        self._text = {}
        self._books = {}

    def resolve(self, index, version=None):
        if version is None:
            current = [d for d in self.docs.values() if d["index"] == index and d["status"] == "current"]
            if len(current) != 1:
                raise KeyError(f"no single current version of {index}")
            return current[0]
        doc = self.docs.get(f"{index}-v{version}")
        if doc is None:
            raise KeyError(f"no document {index} version {version}")
        return doc

    def text(self, doc):
        if doc["id"] not in self._text:
            if doc["type"] == "HTML":
                self._text[doc["id"]] = html_text((DIST / doc["content"]).read_text(encoding="utf-8"))
            elif doc["type"] == "PDF":
                self._text[doc["id"]] = pdf_text(DIST / "files" / doc["file"])
            else:
                raise KeyError(f'{doc["id"]} is {doc["type"]}; read it as cells')
        return self._text[doc["id"]]

    def book(self, doc):
        if doc["id"] not in self._books:
            self._books[doc["id"]] = openpyxl.load_workbook(DIST / "files" / doc["file"], data_only=True)
        return self._books[doc["id"]]

    def qa_text(self, qid):
        entry = [e for e in self.public_qa["entries"] if e["id"] == qid]
        if not entry:
            raise KeyError(f"no Q&A entry {qid}")
        e = entry[0]
        return normalise(" ".join(str(e.get(k) or "") for k in ("question", "answer")))

    def cell(self, term, displayed=False):
        doc = self.resolve(term["xlsx"], term.get("version"))
        ws = self.book(doc)[term["sheet"]]
        headers = {}
        for c in range(1, ws.max_column + 1):
            v = ws.cell(row=HEADER_ROW, column=c).value
            if v is not None:
                headers[str(v)] = c
        key_col = headers[term["key_col"]] if term.get("key_col") else 1
        rows = [r for r in range(HEADER_ROW + 1, ws.max_row + 1) if ws.cell(row=r, column=key_col).value == term["row"]]
        if len(rows) != 1:
            raise KeyError(f'{doc["id"]} {term["sheet"]}: {len(rows)} rows labelled {term["row"]!r}')
        cols = term.get("cols") or [term["col"]]
        total = 0
        for col in cols:
            if col not in headers:
                raise KeyError(f'{doc["id"]} {term["sheet"]}: no column {col!r}')
            cell = ws.cell(row=rows[0], column=headers[col])
            v = cell.value
            if displayed:
                expected = term.get("text", default_text(v)) if len(cols) == 1 else default_text(v)
                actual = displayed_cell(cell)
                if actual != expected:
                    raise KeyError(f"{doc['id']} {ws.title}!{cell.coordinate}: displays {actual!r}, expected {expected!r} (format {cell.number_format!r})")
            if len(cols) == 1:
                return v
            total += v
        return total

    def value(self, term):
        """Return the number a term stands for, after checking it is really there."""
        if "const" in term:
            return term["const"]
        if "xlsx" in term:
            return self.cell(term, displayed=True)
        if "workbook" in term:
            doc = self.resolve(term["workbook"], term.get("version"))
            text = normalise(" ".join(displayed_cell(c) for row in self.book(doc)[term["sheet"]] for c in row if c.value is not None))
            if not contains(text, str(term["value"])):
                raise KeyError(f"missing workbook text {term['value']!r}")
            return term["value"]
        if "doc" in term:
            doc = self.resolve(term["doc"], term.get("version"))
            needle = term.get("text") or default_text(term["value"])
            if not contains(self.text(doc), needle):
                raise KeyError(f'{needle!r} not found in {doc["id"]}')
            return term["value"]
        if "qa" in term:
            needle = term.get("text") or default_text(term["value"])
            if not contains(self.qa_text(term["qa"]), needle):
                raise KeyError(f'{needle!r} not found in Q&A {term["qa"]}')
            return term["value"]
        if "model" in term:
            cur = self.model
            for part in term["model"].split("."):
                cur = cur[int(part)] if isinstance(cur, list) else cur[part]
            return cur
        raise KeyError(f"unknown term {term}")


def describe(term):
    if "xlsx" in term:
        col = term.get("col") or "+".join(term.get("cols", []))
        return f'{term["xlsx"]}!{term["sheet"]}[{term["row"]}][{col}]'
    if "doc" in term:
        return f'{term["doc"]}' + (f' v{term["version"]}' if term.get("version") else "") + f' "{term.get("text") or default_text(term["value"])}"'
    if "qa" in term:
        return f'{term["qa"]} "{term.get("text") or term["value"]}"'
    return json.dumps(term)


def close(a, b):
    return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= TOLERANCE


# ---------------------------------------------------------------- checks

def check_documents(room, rep):
    s = "documents"
    case_ids = []
    for raw in room.case["documents"]:
        case_ids.append(f'{raw["index"]}-v{raw.get("version", 1)}')
    rep.check(s, sorted(case_ids) == sorted(room.docs), "dist index and case index list different documents")
    for doc in room.docs.values():
        if doc["type"] == "HTML":
            rep.check(s, (DIST / doc["content"]).is_file(), f'{doc["id"]}: content fragment missing')
        if doc["view_only"]:
            rep.check(s, doc["file"] is None, f'{doc["id"]}: view-only document has a download file')
            stray = list((DIST / "files").glob(f'{doc["id"]}-*'))
            rep.check(s, not stray, f'{doc["id"]}: view-only document has a file in dist/files: {stray}')
        else:
            path = DIST / "files" / (doc["file"] or "")
            rep.check(s, bool(doc["file"]) and path.is_file() and path.stat().st_size > 0, f'{doc["id"]}: file missing')
        if doc["type"] == "PDF":
            pages = len(PdfReader(DIST / "files" / doc["file"]).pages)
            rep.check(s, pages == doc["pages"], f'{doc["id"]}: index says {doc["pages"]} pages, PDF has {pages}')
        if doc["type"] == "XLSX":
            names = room.book(doc).sheetnames
            rep.check(s, names == doc["sheets"], f'{doc["id"]}: sheet list differs from the index')
        if doc["status"] != "current":
            rep.check(s, doc.get("superseded_by") in room.docs, f'{doc["id"]}: superseded without a valid replacement')
    for index in {d["index"] for d in room.docs.values()}:
        current = [d for d in room.docs.values() if d["index"] == index and d["status"] == "current"]
        rep.check(s, len(current) == 1, f"{index}: {len(current)} current versions")
    current = [d for d in room.docs.values() if d["status"] == "current"]
    rep.check(s, len(current) > 15, "fewer than 16 current documents, so the index would not paginate")
    superseded = [d for d in room.docs.values() if d["status"] != "current"]
    rep.check(s, len(superseded) == sum(d.get("status", "current") != "current" for d in room.case["documents"]), "superseded count differs from case")
    view_only = [d for d in room.docs.values() if d["view_only"]]
    rep.check(s, len(view_only) == sum(d.get("view_only", False) for d in room.case["documents"]), "view-only count differs from case")


def check_qa(room, rep):
    s = "q&a"
    entries = room.public_qa["entries"]
    ids = [e["id"] for e in entries]
    rep.check(s, len(ids) == len(set(ids)), "duplicate Q&A ids")
    rep.check(s, len(entries) > 10, "10 or fewer Q&A entries, so the Q&A view would not paginate")
    indexes = {d["index"] for d in room.docs.values()}
    for e in entries:
        rep.check(s, e["status"] in room.public_qa["statuses"], f'{e["id"]}: unknown status {e["status"]}')
        rep.check(s, e["topic"] in room.public_qa["topics"], f'{e["id"]}: unknown topic {e["topic"]}')
        rep.check(s, bool(e["refs"]), f'{e["id"]}: no referenced documents')
        for ref in e["refs"]:
            rep.check(s, ref in indexes, f'{e["id"]}: reference {ref} is not a document in the index')
        if e["status"] == "Answered":
            rep.check(s, bool(e["answer"]) and bool(e["answered"]), f'{e["id"]}: answered without an answer or date')
        rep.check(s, not e.get("answered") or e["answered"] >= e["asked"], f'{e["id"]}: answered before it was asked')


def revised_evidence(case_dir, request_id, fact):
    """Match reviewed wording/filename revisions without rewriting frozen answers."""
    path = case_dir / "evidence-revisions.json"
    if not path.exists():
        return fact
    matches = [r for r in load_json(path)["revisions"]
               if r["request"] == request_id and r["original"] == fact]
    if len(matches) > 1:
        raise ValueError("duplicate evidence revision")
    if not matches:
        return fact
    revised = dict(fact)
    if "file" in fact:
        revised["file"] = matches[0]["replacement"]
    elif "doc" in fact and isinstance(fact["value"], str):
        revised["text"] = matches[0]["replacement"]
    else:
        raise ValueError("evidence revisions must be document wording or filenames")
    return revised


def check_answer_key(room, rep):
    s = "answer key"
    key = load_json(room.case_dir / "answer-key.json")
    requests_md = (room.case_dir / "request-list.md").read_text(encoding="utf-8")
    numbered = re.findall(r"^(\d+)\. \*\*", requests_md, flags=re.M)
    rep.check(s, numbered == [str(i) for i in range(1, 11)], "request list does not have requests 1 to 10")
    rep.check(s, [r["id"] for r in key["requests"]] == list(range(1, 11)), "answer key does not cover requests 1 to 10")
    for req in key["requests"]:
        rid = f'request {req["id"]}'
        for src in req["sources"]:
            try:
                if "qa" in src:
                    room.qa_text(src["qa"])
                else:
                    doc = room.resolve(src["index"], src.get("version"))
                    rep.check(s, doc["status"] == "current", f'{rid}: cites superseded {doc["id"]}')
                rep.ok(s)
            except KeyError as e:
                rep.fail(s, f"{rid}: source {src}: {e}")
        values = {}
        for fact in req["facts"]:
            fact = revised_evidence(room.case_dir, req["id"], fact)
            try:
                if "file" in fact:
                    doc = room.resolve(fact["index"], fact.get("version"))
                    good = doc["file"] == fact["file"] and (DIST / "files" / fact["file"]).is_file()
                    rep.check(s, good, f'{rid}: file {fact["file"]} is not the download for {doc["id"]}')
                    continue
                got = room.value(fact)
                if "xlsx" in fact:
                    rep.check(s, close(got, fact["value"]), f'{rid}: {describe(fact)} is {got!r}, key says {fact["value"]!r}')
                else:
                    rep.ok(s)
                values[fact["label"]] = got
            except KeyError as e:
                rep.fail(s, f'{rid}: fact {fact["label"]!r}: {e}')
        for d in req.get("derived", []):
            try:
                result = derive(d, values)
                rep.check(s, close(result, d["value"]), f'{rid}: derived {d["label"]!r} computes to {result}, key says {d["value"]}')
                values[d["label"]] = result
            except KeyError as e:
                rep.fail(s, f'{rid}: derived {d["label"]!r} needs fact {e}')
        trap = req.get("superseded_trap")
        if trap:
            old = room.resolve(trap["doc"], trap["version"])
            new = room.resolve(trap["doc"])
            rep.check(s, old["status"] != "current", f'{rid}: trap document {old["id"]} is not superseded')
            rep.check(s, contains(room.text(old), trap["text"]), f'{rid}: {trap["text"]!r} not in superseded {old["id"]}')
            rep.check(s, not contains(room.text(new), trap["text"]), f'{rid}: {trap["text"]!r} also in current {new["id"]}')
        if "qualifying" in req:
            cutoff = date.fromisoformat(req["cutoff"])
            by_key = {c["key"]: c for c in room.model["customers"]}
            expect = sorted(
                d["index"] for d in room.docs.values()
                if d["status"] == "current" and raw_customer(room, d) and by_key[raw_customer(room, d)]["coc"]
                and date.fromisoformat(by_key[raw_customer(room, d)]["expiry_iso"]) <= cutoff)
            rep.check(s, expect == sorted(req["qualifying"]), f'{rid}: model says {expect}, key says {req["qualifying"]}')


def raw_customer(room, doc):
    for raw in room.case["documents"]:
        if raw["index"] == doc["index"] and raw.get("version", 1) == doc["version"]:
            return raw.get("customer")
    return None


def derive(d, values):
    args = d["args"]
    op = d["op"]
    if op == "sum":
        return sum(values[a] for a in args)
    if op == "sum_signed":
        return sum(-values[a[1:]] if a.startswith("-") else values[a] for a in args)
    if op == "diff":
        return values[args[0]] - values[args[1]]
    if op == "pct_change":
        return round((values[args[0]] / values[args[1]] - 1) * 100, d.get("decimals", 1))
    if op == "ratio_pct":
        return round(values[args[0]] / values[args[1]] * 100, d.get("decimals", 1))
    if op == "count":
        return sum(1 for a in args if a in values)
    if op == "product":
        return values[args[0]] * values[args[1]]
    if op == "thousands":
        return round(values[args[0]] / 1000)
    raise KeyError(f"unknown op {op}")


def check_reconciliations(room, rep):
    s = "reconciliations"
    spec = load_json(room.case_dir / "reconciliations.json")
    for chk in spec["checks"]:
        try:
            target = room.value(chk["equals"])
            if "ratio_pct" in chk:
                a, b = (room.value(t) for t in chk["ratio_pct"])
                got = round(a / b * 100, chk.get("decimals", 1))
            else:
                got = sum(t.get("sign", 1) * room.value(t) for t in chk["terms"])
            if not rep.check(s, close(got, target), f'{chk["name"]}: terms give {got}, expected {target}'):
                continue
        except (KeyError, TypeError) as e:
            rep.fail(s, f'{chk["name"]}: {e}')




BANNER_FILES = ("*.html",)


def check_site(room, rep):
    s = "site"
    banner = room.case["banner"]
    pages = sorted(DIST.glob("*.html"))
    rep.check(s, {p.name for p in pages} >= {"index.html", "room.html", "doc.html", "qa.html", "404.html"}, "a site page is missing")
    for page in pages + sorted((DIST / "files").glob("*.html")):
        rep.check(s, banner in page.read_text(encoding="utf-8"), f"{page.relative_to(DIST)}: banner missing")
    for doc in room.docs.values():
        if doc["type"] == "PDF":
            rep.check(s, normalise(banner) in room.text(doc), f'{doc["id"]}: banner missing from PDF text')
        if doc["type"] == "XLSX":
            for ws in room.book(doc).worksheets:
                found = any(c.value == banner for row in ws.iter_rows(max_row=4) for c in row)
                rep.check(s, found, f'{doc["id"]} sheet {ws.title}: banner missing')
    room_html = (DIST / "room.html").read_text(encoding="utf-8")
    for doc in room.docs.values():
        rep.check(s, doc["title"] not in room_html, f'room.html contains document title {doc["title"]!r} without JavaScript')
    external = re.compile(r"(https?:)?//[a-z0-9.-]+\.[a-z]{2,}", re.I)
    for path in DIST.rglob("*"):
        if path.suffix in (".html", ".js", ".css", ".json") and path.is_file():
            hits = external.findall(path.read_text(encoding="utf-8"))
            rep.check(s, not hits, f"{path.relative_to(DIST)}: external reference")
    for name in ("answer-key.json", "request-list.md", "reconciliations.json", "model.json", "design.md", "review-1.md", "name-checks.json", "evidence-revisions.json"):
        rep.check(s, not list(DIST.rglob(name)), f"{name} is inside dist/")
    key_text = (room.case_dir / "answer-key.json").read_text(encoding="utf-8")
    marker = json.loads(key_text)["requests"][0]["pitfalls"][0]
    leaked = [p for p in DIST.rglob("*") if p.is_file() and p.suffix in (".html", ".json", ".js") and marker in p.read_text(encoding="utf-8")]
    rep.check(s, not leaked, f"answer-key text found in {leaked}")
    cfg_path = ROOT / room.case["deployment_config"]
    cfg = load_jsonc(cfg_path)
    rep.check(s, cfg.get("name") == room.case["deployment_name"], "wrangler.jsonc name")
    rep.check(s, cfg.get("compatibility_date") == "2026-11-01", "wrangler.jsonc compatibility_date")
    assets = cfg.get("assets", {})
    rep.check(s, (ROOT / assets.get("directory", "-")).resolve() == DIST.resolve(), "wrangler.jsonc assets.directory")
    rep.check(s, assets.get("not_found_handling") == "404-page", "wrangler.jsonc not_found_handling")


def check_case_constraints(room, rep):
    key = load_json(room.case_dir / "answer-key.json")
    public_texts = {}
    for doc in room.docs.values():
        if doc["type"] == "XLSX":
            for ws in room.book(doc):
                public_texts[f"{doc['id']} {ws.title}"] = normalise(" ".join(
                    displayed_cell(c) for row in ws for c in row if c.value is not None))
        else:
            public_texts[doc["id"]] = room.text(doc)
    for path in DIST.rglob("*"):
        if path.is_file() and path.suffix in (".json", ".js", ".css", ".html"):
            public_texts[str(path.relative_to(DIST))] = html_text(path.read_text())
    for value in key.get("derivable_only", []):
        hits = [name for name, text in public_texts.items()
                if contains(text, value) or contains(text, value.replace(",", ""))]
        rep.check("case constraints", not hits, f"derivable-only {value} appears in {hits}")
    names = load_json(room.case_dir / "name-checks.json")
    combined = " ".join(public_texts.values())
    for entry in names.get("accepted", []):
        rep.check("case constraints", normalise(entry["name"]) in combined,
                  f"case name absent from public artifacts: {entry['name']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", default="dev-larkspur")
    args = ap.parse_args()
    global DIST
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.case):
        ap.error("invalid case id")
    DIST = ROOT / "dist" / args.case
    case_dir = ROOT / "cases" / args.case
    if not (DIST / "data" / "index.json").is_file():
        print("dist/ is not built; run python3 -I build.py first", file=sys.stderr)
        return 2
    room = Room(case_dir)
    rep = Report()
    for section in (check_documents, check_qa, check_answer_key, check_reconciliations, check_site, check_case_constraints):
        try:
            section(room, rep)
        except Exception as e:  # report and carry on so one broken section does not hide the rest
            rep.fail(section.__name__, f"crashed: {type(e).__name__}: {e}")
    for section, n in rep.passes.items():
        print(f"PASS {section}: {n} checks")
    for f in rep.failures:
        print(f"FAIL {f}")
    total = sum(rep.passes.values()) + len(rep.failures)
    print(f"{'OK' if not rep.failures else 'FAILED'}: {total - len(rep.failures)} of {total} checks passed")
    return 1 if rep.failures else 0


if __name__ == "__main__":
    sys.exit(main())
