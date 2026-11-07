#!/usr/bin/env python3
"""Build a made-up virtual data room for one case into dist/.

Usage: python3 -I build.py [--case dev-larkspur] [--out dist]

Reads cases/<case-id>/ (index.json, model.json, series.json, qa.json,
docs/*.html, workbooks/*.json) and writes a static site: HTML pages from
site/, data/index.json and data/qa.json for the JavaScript front end,
content/<doc-id>.html fragments for HTML documents, and files/ with the
downloadable PDF, XLSX and HTML files. PDFs are printed from HTML with
headless Chrome. The answer key and request list are never copied.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
CHROME = "/usr/bin/google-chrome"
PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)(?:\|(\w+))?\s*\}\}")
WHOLE_PLACEHOLDER = re.compile(r"^(-)?\{\{\s*([\w.]+)(?:\|(\w+))?\s*\}\}$")
NUM_INT = '#,##0;(#,##0);"-"'
NUM_DEC1 = "0.0"
NUM_PCT = "0.0%"
NUMBER_FORMATS = {"int": NUM_INT, "dec1": NUM_DEC1, "dec2": "0.00", "dec4": "0.0000", "ratio": '0.00":1"'}


class BuildError(Exception):
    pass


# ---------------------------------------------------------------- case data

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lookup(model, path):
    cur = model
    for part in path.split("."):
        if isinstance(cur, list):
            match = [x for x in cur if isinstance(x, dict) and x.get("key") == part]
            if not match:
                raise BuildError(f"no list item with key {part!r} in {path!r}")
            cur = match[0]
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise BuildError(f"unknown model path {path!r}")
    return cur


def format_value(value, style):
    if style == "raw" or isinstance(value, str):
        return str(value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if style in ("dec1", "dec2", "dec4", "ratio"):
        digits = {"dec1": 1, "dec2": 2, "dec4": 4, "ratio": 2}[style]
        return f"{value:,.{digits}f}" + (":1" if style == "ratio" else "")
    if style == "paren":
        return f"({abs(value):,})"
    if isinstance(value, float):
        return f"{value:,.1f}"
    return f"{value:,}"


def render_text(text, model):
    def sub(m):
        return html.escape(format_value(lookup(model, m.group(1)), m.group(2)), quote=False)
    out = PLACEHOLDER.sub(sub, text)
    if "{{" in out or "}}" in out:
        raise BuildError("unresolved placeholder: " + out[out.find("{{"):][:60])
    return out


TABLE_RE = re.compile(r"<table\b.*?</table>", re.S)
ROW_RE = re.compile(r"<tr\b[^>]*>.*?</tr>", re.S)
CELL_RE = re.compile(r"<(td|th)\b([^>]*)>")


def align_number_headers(fragment):
    """Give header cells class="num" where the body cells of that column are numeric."""
    def fix_table(m):
        table = m.group(0)
        if "<thead" not in table:
            return table
        head, rest = table.split("</thead>", 1)
        numeric = set()
        for row in ROW_RE.findall(rest):
            col = 0
            for tag, attrs in CELL_RE.findall(row):
                span = re.search(r'colspan="(\d+)"', attrs)
                if 'class="num"' in attrs:
                    numeric.add(col)
                col += int(span.group(1)) if span else 1
        counter = iter(range(1000))

        def fix_cell(c):
            i = next(counter)
            if i in numeric and "class=" not in c.group(2):
                return f'<{c.group(1)} class="num"{c.group(2)}>'
            return c.group(0)
        return CELL_RE.sub(fix_cell, head) + "</thead>" + rest
    return TABLE_RE.sub(fix_table, fragment)


def index_key(index):
    return tuple(int(p) for p in index.split("."))


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:180].rstrip("-")


def prepare_documents(case):
    docs = []
    for raw in case["documents"]:
        d = dict(raw)
        d.setdefault("version", 1)
        d.setdefault("status", "current")
        d.setdefault("view_only", False)
        d["id"] = f'{d["index"]}-v{d["version"]}'
        d["folder"] = int(d["index"].split(".")[0])
        ext = d["type"].lower()
        d["file"] = f'{d["id"]}-{slugify(d["title"])}.{ext}'
        if d["view_only"] and d["type"] != "HTML":
            raise BuildError(f'{d["id"]}: only HTML documents can be view only')
        docs.append(d)
    ids = [d["id"] for d in docs]
    if len(ids) != len(set(ids)):
        raise BuildError("duplicate document ids")
    for d in docs:
        if d.get("superseded_by") and d["superseded_by"] not in ids:
            raise BuildError(f'{d["id"]}: superseded_by points at unknown {d["superseded_by"]}')
    docs.sort(key=lambda d: (index_key(d["index"]), d["version"]))
    return docs


def source_name(d):
    multi = d["version"] > 1 or d.get("superseded_by")
    return f'{d["index"]}-v{d["version"]}' if multi else d["index"]


def derive_series(series):
    derived = series.get("derived", {})
    for name, group in series.items():
        if name in ("derived", "_note") or not isinstance(group, dict) or name not in series.get("derive_groups", []):
            continue
        lengths = {len(v) for v in group.values() if isinstance(v, list)}
        if len(lengths) != 1 or not next(iter(lengths), 0):
            raise BuildError(f"series {name}: inconsistent or empty monthly arrays")
        n = lengths.pop()
        for key, parts in derived.items():
            total = [0] * n
            for part in parts:
                sign, ref = (1 if part[0] == "+" else -1), part[1:]
                if ref not in group:
                    raise BuildError(f"series {name}: {key} needs {ref}")
                total = [t + sign * v for t, v in zip(total, group[ref])]
            group[key] = total
    return series


# ---------------------------------------------------------------- HTML pages

DOC_CSS = """
:root { --ink: #1d2433; --muted: #5a6275; --line: #c9cfdb; --accent: #1f4e79; --band: #fff4d6; }
* { box-sizing: border-box; }
body { font: 10.5pt/1.45 "Liberation Sans", Arial, Helvetica, sans-serif; color: var(--ink); margin: 0; }
.banner { background: var(--band); border: 1px solid #e0c46c; padding: 4px 8px; font-size: 8.5pt; font-weight: 600; text-align: center; }
.page { padding: 0 2mm; }
header.doc-head { border-bottom: 2px solid var(--accent); margin: 10px 0 12px; padding-bottom: 6px; }
header.doc-head .ref { color: var(--accent); font-weight: 700; font-size: 9pt; letter-spacing: .02em; }
header.doc-head h1 { font-size: 15pt; margin: 2px 0 2px; }
header.doc-head p { margin: 0; color: var(--muted); font-size: 9pt; }
h2 { font-size: 12pt; margin: 16px 0 6px; color: var(--accent); }
h3 { font-size: 10.5pt; margin: 12px 0 4px; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.5pt; }
caption { text-align: left; font-weight: 600; padding-bottom: 4px; }
th, td { border-bottom: 1px solid var(--line); padding: 4px 6px; text-align: left; vertical-align: top; }
thead th { border-bottom: 2px solid var(--ink); background: #eef1f6; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
tr.total th, tr.total td { font-weight: 700; border-top: 1.5px solid var(--ink); }
table.terms th { width: 28%; background: #f5f7fa; }
.doc-meta { color: var(--muted); font-style: italic; }
.callout { border-left: 4px solid #c07a00; background: #fff8ea; padding: 6px 10px; margin: 10px 0; }
dl dt { font-weight: 700; margin-top: 6px; }
dl dd { margin: 2px 0 6px 0; }
.sign { margin-top: 12px; font-style: italic; }
.cover { padding: 40mm 0 20mm; }
.cover-company { font-size: 20pt; font-weight: 700; color: var(--accent); margin: 0 0 8px; }
.cover-title { font-size: 14pt; margin: 0 0 18px; }
.slide { border: 1px solid var(--line); padding: 10px 14px; margin: 0 0 14px; break-inside: avoid; }
.letterhead { display: flex; justify-content: space-between; border-bottom: 1px solid var(--line); margin-bottom: 12px; }
.org { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 12px 0; }
.org-row { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.org-node { border: 1.5px solid var(--accent); border-radius: 4px; padding: 6px 10px; text-align: center; min-width: 150px; max-width: 220px; font-weight: 700; }
.org-node span { font-weight: 400; font-size: 8.5pt; color: var(--muted); }
.org-node.top { background: #eef1f6; }
@media print {
  @page { size: A4; margin: 12mm 14mm 14mm; }
  .page-break { break-before: page; }
  .slide { min-height: 120mm; }
  .slide + .slide { break-before: page; }
  table { font-size: 9pt; }
  th, td { padding: 3px 6px; }
  table.frame { margin: 0; font-size: inherit; }
  table.frame > thead > tr > td, table.frame > tbody > tr > td { border: 0; padding: 0; }
  thead { display: table-header-group; }
}
"""


def standalone_html(d, fragment, case, for_print):
    """A self-contained document page, used for HTML downloads and PDF printing."""
    head = (
        f'<header class="doc-head"><div class="ref">{html.escape(case["codename"])} &middot; Document {d["index"]} &middot; '
        f'Version {d["version"]}</div><h1>{html.escape(d["title"])}</h1>'
        f'<p>{html.escape(case["company"])} &middot; Uploaded {d["date"]} &middot; Strictly private and confidential</p></header>'
    )
    banner = f'<div class="banner" role="note">{html.escape(case["banner"])}</div>'
    if for_print:
        # The banner sits in a repeating table header so it prints on every page.
        body = (
            '<table class="frame"><thead><tr><td>' + banner + "</td></tr></thead>"
            '<tbody><tr><td><div class="page">' + head + fragment + "</div></td></tr></tbody></table>"
        )
    else:
        body = banner + '<main class="page">' + head + fragment + "</main>"
    return (
        '<!doctype html>\n<html lang="en-GB">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{d["index"]} {html.escape(d["title"])} (v{d["version"]})</title>\n'
        f"<style>{DOC_CSS}</style>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def print_pdfs(jobs, workdir):
    """Print each (html_path, pdf_path) with headless Chrome in a throwaway profile."""
    if not jobs:
        return
    if not Path(CHROME).exists():
        raise BuildError(f"Chrome not found at {CHROME}")
    profile = Path(tempfile.mkdtemp(prefix=workdir.name + "-chrome-", dir=workdir))
    try:
        for src, out in jobs:
            cmd = [
                CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                "--no-default-browser-check", "--disable-extensions", "--disable-sync",
                f"--user-data-dir={profile}", "--no-pdf-header-footer",
                f"--print-to-pdf={out}", src.as_uri(),
            ]
            env = dict(os.environ, TMPDIR=str(ROOT), XDG_CONFIG_HOME=str(workdir), XDG_CACHE_HOME=str(workdir))
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
            if res.returncode != 0 or not out.exists() or out.stat().st_size == 0:
                raise BuildError(f"Chrome failed for {src.name}: {res.stderr[-800:]}")
    finally:
        shutil.rmtree(profile, ignore_errors=True)


# ---------------------------------------------------------------- workbooks

BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
MUTED = Font(italic=True, color="666666")
BANNER_FONT = Font(bold=True, color="7A5A00")
BANNER_FILL = PatternFill("solid", fgColor="FFF4D6")
HEAD_FILL = PatternFill("solid", fgColor="E7ECF3")
TOP_BORDER = Border(top=Side(style="thin"))
HEADER_ROW = 5
FIRST_DATA_ROW = 6


def sheet_heading(ws, title, units, banner):
    ws["A1"] = title
    ws["A1"].font = TITLE
    ws["A2"] = units
    ws["A2"].font = MUTED
    ws["A3"] = banner
    ws["A3"].font = BANNER_FONT
    ws["A3"].fill = BANNER_FILL


def write_header(ws, labels):
    for c, label in enumerate(labels, 1):
        cell = ws.cell(row=HEADER_ROW, column=c, value=label)
        cell.font = BOLD
        cell.fill = HEAD_FILL
        cell.alignment = Alignment(horizontal="left" if c == 1 else "right", wrap_text=True)


def aggregate(values, how):
    if how == "last":
        return values[-1]
    if how == "avg":
        return round(sum(values) / len(values), 1)
    return sum(values)


def monthly_sheet(ws, sh, series, case_dir, banner):
    rows = sh["rows"]
    if isinstance(rows, str) and rows.startswith("@"):
        rows = load_json(case_dir / "workbooks" / rows[1:])
    skip = set(sh.get("skip_rows", []))
    group = series[sh["group"]]
    extras = sh.get("extra_cols", [])
    sheet_heading(ws, sh["title"], sh["units"], banner)
    labels = ["GBP thousands" if "GBP" in sh["units"] else ""] + sh["months"] + [sh["total_label"]]
    labels += [e["label"] for e in extras]
    write_header(ws, labels)
    columns = {}  # key -> list of values in column order (months, total, extras)

    def values_for(key, how):
        vals = list(group[key])
        out = vals + [aggregate(vals, how)]
        for e in extras:
            lo, hi = e["slice"]
            out.append(aggregate(series[e["group"]][key][lo:hi], how))
        return out

    r = FIRST_DATA_ROW
    for spec in rows:
        kind = spec[0]
        if kind == "blank":
            r += 1
            continue
        label = spec[1]
        if kind == "section":
            ws.cell(row=r, column=1, value=label).font = BOLD
            r += 1
            continue
        if kind in ("line", "total"):
            key = spec[2]
            if key in skip:
                continue
            how = spec[3] if len(spec) > 3 else "sum"
            fmt = NUMBER_FORMATS.get(spec[4] if len(spec) > 4 else "int")
            vals = values_for(key, how)
            columns[key] = vals
        elif kind == "pct":
            num, den = columns[spec[2]], columns[spec[3]]
            vals = [round(a / b, 4) if b else None for a, b in zip(num, den)]
            fmt = NUM_PCT
        else:
            raise BuildError(f"unknown row kind {kind}")
        ws.cell(row=r, column=1, value=label)
        for c, v in enumerate(vals, 2):
            cell = ws.cell(row=r, column=c, value=v)
            cell.number_format = fmt
        if kind == "total":
            for c in range(1, len(vals) + 2):
                ws.cell(row=r, column=c).font = BOLD
                ws.cell(row=r, column=c).border = TOP_BORDER
        r += 1
    ws.column_dimensions["A"].width = 38
    for c in range(2, len(labels) + 1):
        ws.column_dimensions[get_column_letter(c)].width = 13 if c <= len(sh["months"]) + 2 else 16
    ws.freeze_panes = ws.cell(row=FIRST_DATA_ROW, column=2)


def table_cell(value, model):
    if value == "":
        return None, None
    if isinstance(value, dict) and "pct" in value:
        a, b = (lookup(model, p) for p in value["pct"])
        return round(a / b, 4), NUM_PCT
    if isinstance(value, str):
        m = WHOLE_PLACEHOLDER.match(value)
        if m:
            v = lookup(model, m.group(2))
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return (-v if m.group(1) else v), NUMBER_FORMATS[m.group(3)] if m.group(3) else (NUM_INT if isinstance(v, int) else NUM_DEC1)
            return html.unescape(render_text(value, model)), None
        if "{{" in value:
            return html.unescape(render_text(value, model)), None
        return value, None
    if isinstance(value, bool):
        return ("Yes" if value else "No"), None
    if isinstance(value, int):
        return value, NUM_INT
    if isinstance(value, float):
        return value, NUM_DEC1
    return value, None


def table_sheet(ws, sh, model, banner):
    sheet_heading(ws, sh["title"], sh["units"], banner)
    write_header(ws, sh["header"])
    widths = [len(str(h)) for h in sh["header"]]
    r = FIRST_DATA_ROW
    for row in sh["rows"]:
        style, cells = (row.get("style"), row["cells"]) if isinstance(row, dict) else (None, row)
        if len(cells) != len(sh["header"]):
            raise BuildError(f'{sh["name"]}: row has {len(cells)} cells, header has {len(sh["header"])}')
        for c, raw in enumerate(cells, 1):
            v, fmt = table_cell(raw, model)
            cell = ws.cell(row=r, column=c, value=v)
            if isinstance(v, str):
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                ws.row_dimensions[r].height = max(ws.row_dimensions[r].height or 15, 15 * ((len(v) + 54) // 55))
            if fmt:
                cell.number_format = fmt
            if style == "total":
                cell.font = BOLD
                cell.border = TOP_BORDER
            widths[c - 1] = max(widths[c - 1], len(str(v)) if v is not None else 0)
        r += 1
    for c, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(c)].width = min(max(w + 2, 10), 60)
    ws.freeze_panes = ws.cell(row=FIRST_DATA_ROW, column=1)


def notes_sheet(ws, sh, banner):
    ws["A1"] = sh["title"]
    ws["A1"].font = TITLE
    ws["A2"] = banner
    ws["A2"].font = BANNER_FONT
    ws["A2"].fill = BANNER_FILL
    for i, line in enumerate(sh["lines"], 4):
        ws.row_dimensions[i].height = max(30, 15 * ((len(line) + 109) // 110))
        ws.cell(row=i, column=1, value=line).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 120


def build_workbook(spec, d, model, series, case_dir, case, out):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sh in spec["sheets"]:
        ws = wb.create_sheet(sh["name"])
        if sh["kind"] == "notes":
            notes_sheet(ws, sh, case["banner"])
        elif sh["kind"] == "monthly":
            monthly_sheet(ws, sh, series, case_dir, case["banner"])
        elif sh["kind"] == "table":
            table_sheet(ws, sh, model, case["banner"])
        else:
            raise BuildError(f'unknown sheet kind {sh["kind"]}')
        if sh["kind"] != "notes":
            last = ws.max_column
            width = sum(ws.column_dimensions[get_column_letter(c)].width for c in range(1, last + 1))
            for row in (1, 2, 3):
                ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last)
                cell = ws.cell(row=row, column=1)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
                usable_width = max(1, int(width / (1.4 if row == 1 else 1.15)))
                ws.row_dimensions[row].height = max(20, 18 * ((len(str(cell.value)) + usable_width - 1) // usable_width))
    wb.properties.title = f'{d["index"]} {d["title"]}'
    wb.properties.creator = case["workbook_creator"]
    wb.properties.subject = case["banner"]
    wb.save(out)
    return [sh["name"] for sh in spec["sheets"]]


# ---------------------------------------------------------------- site

def render_site_page(text, site):
    def sub(m):
        key = m.group(1)
        if not key.startswith("site."):
            raise BuildError(f"site page placeholder must start with site.: {key}")
        return html.escape(str(site[key[5:]]), quote=True)
    out = PLACEHOLDER.sub(sub, text)
    if "{{" in out:
        raise BuildError("unresolved placeholder in site page")
    return out


def build(case_id, out_dir):
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id):
        raise BuildError("invalid case id")
    case_dir = ROOT / "cases" / case_id
    case = load_json(case_dir / "index.json")
    model = load_json(case_dir / "model.json")
    series = derive_series(load_json(case_dir / "series.json"))
    qa = load_json(case_dir / "qa.json")
    docs = prepare_documents(case)

    if out_dir.is_symlink() or out_dir.resolve() != ROOT / "dist":
        raise BuildError(f"refusing to write outside {ROOT / 'dist'}: {out_dir}")
    out_dir = out_dir / case_id
    if out_dir.is_symlink() or out_dir.resolve() != ROOT / "dist" / case_id:
        raise BuildError("case output must be a real child of dist")
    if case.get("case_id") != case_id:
        raise BuildError("case metadata does not match directory")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "data").mkdir(parents=True)
    (out_dir / "content").mkdir()
    (out_dir / "files").mkdir()
    (out_dir / "assets").mkdir()

    site = {
        "terms_key": case_id + "." + case["terms_version"] + ".termsAccepted",
        "banner": case["banner"],
        "room_title": case["room_title"],
        "codename": case["codename"],
        "company": case["company"],
        "terms_version": case["terms_version"],
    }
    for page in sorted((ROOT / "site").glob("*.html")):
        text = page.read_text(encoding="utf-8")
        (out_dir / page.name).write_text(render_site_page(text, site), encoding="utf-8")
    for asset in sorted((ROOT / "site" / "assets").iterdir()):
        shutil.copyfile(asset, out_dir / "assets" / asset.name)
    # Keep every page, document and download out of search results. A noindex header, not a robots.txt Disallow, so the
    # chat apps' user-triggered fetchers can still reach the site.
    shutil.copyfile(ROOT / "site" / "_headers", out_dir / "_headers")

    work = Path(tempfile.mkdtemp(prefix=case_id + "-build-", dir=ROOT))
    try:
        pdf_jobs = []
        for d in docs:
            if d["type"] in ("HTML", "PDF"):
                src = case_dir / "docs" / f"{source_name(d)}.html"
                fragment = align_number_headers(render_text(src.read_text(encoding="utf-8"), model))
                if d["type"] == "HTML":
                    (out_dir / "content" / f'{d["id"]}.html').write_text(fragment, encoding="utf-8")
                    d["content"] = f'content/{d["id"]}.html'
                    if not d["view_only"]:
                        (out_dir / "files" / d["file"]).write_text(
                            standalone_html(d, fragment, case, for_print=False), encoding="utf-8")
                else:
                    tmp_html = work / f'{d["id"]}.html'
                    tmp_html.write_text(standalone_html(d, fragment, case, for_print=True), encoding="utf-8")
                    pdf_jobs.append((tmp_html, out_dir / "files" / d["file"]))
            elif d["type"] == "XLSX":
                spec = load_json(case_dir / "workbooks" / f"{source_name(d)}.json")
                d["sheets"] = build_workbook(spec, d, model, series, case_dir, case, out_dir / "files" / d["file"])
                d["pages"] = None
            else:
                raise BuildError(f'{d["id"]}: unknown type {d["type"]}')
        print_pdfs(pdf_jobs, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    for d in docs:
        if d["type"] == "PDF":
            d["pages"] = len(PdfReader(out_dir / "files" / d["file"]).pages)
        if d["view_only"]:
            d["file"] = None
        if d["type"] != "HTML":
            d.pop("content", None)
        d.pop("customer", None)

    public = {
        "room_title": case["room_title"],
        "codename": case["codename"],
        "company": case["company"],
        "banner": case["banner"],
        "folders": case["folders"],
        "documents": docs,
    }
    (out_dir / "data" / "index.json").write_text(json.dumps(public, indent=1, ensure_ascii=False), encoding="utf-8")
    qa_public = {k: v for k, v in qa.items() if not k.startswith("_")}
    (out_dir / "data" / "qa.json").write_text(json.dumps(qa_public, indent=1, ensure_ascii=False), encoding="utf-8")
    return docs


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--case", default="dev-larkspur")
    ap.add_argument("--out", default=str(ROOT / "dist"))
    args = ap.parse_args()
    try:
        docs = build(args.case, Path(args.out))
    except BuildError as e:
        print(f"build failed: {e}", file=sys.stderr)
        return 1
    by_type = {}
    for d in docs:
        by_type[d["type"]] = by_type.get(d["type"], 0) + 1
    current = sum(1 for d in docs if d["status"] == "current")
    print(f"built {len(docs)} index entries ({current} current, {len(docs) - current} superseded): "
          + ", ".join(f"{n} {t}" for t, n in sorted(by_type.items())))
    print(f"output: {Path(args.out) / args.case}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
