# Made-up virtual data room

A static test fixture: a virtual data room of the kind investment bankers open for buyers in a company sale. Agents are asked to answer a buyer's request list from it with a browser. Every company, person and figure in it is fictional, and every page says so.

The development case is `dev-larkspur` ("Project Larkspur"): the sale of Quillmoor Holdings Limited, a made-up UK cold-chain logistics group. The published case is `pub-tansy` ("Project Tansy"), the sale of Vennacott Holdings Limited, a made-up fire-safety and security-systems services group. Its financial year ends on 31 March.

## Build, check and serve

Requires Python 3 with `openpyxl` and `pypdf`, and Google Chrome at `/usr/bin/google-chrome` (used headless to print the PDFs). Nothing is installed.

```sh
python3 -I build.py --case dev-larkspur
python3 -I check.py --case dev-larkspur
python3 -I build.py --case pub-tansy
python3 -I check.py --case pub-tansy
python3 -I -m http.server 8000 --directory dist/pub-tansy
# Open http://127.0.0.1:8000/; stop the server when finished.
```

Both scripts take `--case <case-id>`. `build.py` deletes and rewrites only `dist/<case-id>/` each run, preserving other built cases. The `--out` argument accepts only this project’s real `dist` directory; case IDs and symlinks are guarded before deletion. Chrome runs with temporary files and a profile inside this directory, cleaned afterwards.

<redacted: a note on the author's local Python install>

To deploy as a Cloudflare Worker with static assets, build first and then run `wrangler deploy` with `wrangler.jsonc` (name `akw-data-room-dev`; serves `dist/dev-larkspur/`, with `404.html` for unknown paths). `wrangler.pub-tansy.jsonc` names `akw-data-room` and serves `dist/pub-tansy/`. Build the matching case first. The build never deploys.

## What the site does

- `index.html`: terms of access. Ticking the box and pressing **Enter data room** stores acceptance in `sessionStorage`; every other page sends you back here until you accept, then returns you to the page you asked for.
- `room.html`: the document index, loaded by JavaScript from `data/index.json` (the HTML alone lists no documents). Folder tree, search, filters for folder, type and date range, sorting by index or date, 15 rows a page, and superseded versions hidden unless **Show superseded versions** is ticked. Filter state is kept in the URL.
- `doc.html?id=<index>-v<version>` (or `?id=<index>` for the current version): the viewer. HTML documents render in the page; PDF and XLSX documents show a Download button (PDFs also get an inline preview where the browser supports it; spreadsheets list their sheets only). View-only documents have no download. Superseded versions say so and link to the current one.
- `qa.html`: the Q&A module from `data/qa.json`, filtered by status and topic, 10 entries a page.

Dates in the filters are typed as DD/MM/YYYY or YYYY-MM-DD; text fields are used because automated keyboards cannot fill Chrome's native date pickers. Pages work at 390 px and 1366 px wide.

## What is where

```
build.py                  generator: cases/<id>/ -> dist/<id>/
check.py                  verification of dist/<id>/ against the case
wrangler.jsonc            Cloudflare Worker config (static assets)
site/                     page templates, CSS and JavaScript copied into dist/<id>/
cases/dev-larkspur/
  index.json              document index: folders, titles, types, dates, versions, view-only flags
  model.json              the case's facts (GBP thousands unless stated); documents pull them in with {{path}} placeholders
  series.json             monthly management accounts, budget and KPI series, and the rules for derived lines
  qa.json                 Q&A entries
  docs/*.html             sources for HTML documents and for PDFs (printed from HTML)
  workbooks/*.json        sheet layouts for the XLSX files
  reconciliations.json    cross-document reconciliations that check.py runs
  request-list.md         the buyer's ten requests (never served)
  answer-key.json         answers, sources, facts to verify and likely mistakes (never served)
  name-checks.json        web searches run to confirm the names are not real companies
dist/<id>/                build output (not committed)
```

## How Larkspur reconciles

- FY2025 revenue: £48,952k in the management accounts (2.3) and the top-customer schedule (3.1), less a £312k Hollowbeck rebate accrual booked at audit, gives the audited £48,640k (2.2). Document 2.6 explains the difference.
- FY2024 management and audited revenue agree at £44,180k.
- FY2026 year to date: 3.1 ties to the £39,870k in 2.4.
- Adjusted EBITDA: version 2 of the bridge (2.5) gives £6,912k. Superseded version 1 also added back the rebate, giving £7,224k. The bridge's £240k rent normalisation is the Daventry rent increase between lease schedules 5.1 v1 and v2.
- Capex by year (2.8) equals fixed-asset additions in the audited accounts. Debt balances (2.9) equal the audited balance sheet.

`check.py` runs 113 Larkspur reconciliations and model identities, reading XLSX cells with openpyxl and PDF text with pypdf.

## Tansy checks and authoring conventions

Tansy has 31 current documents, one superseded census and twelve Q&A entries. Documents 1.4 and 4.2 are view only. The private design, review, request list, answer key, model, name checks and reconciliations are never copied into the built site.

Case metadata owns the codename, company, banner, terms version, workbook creator and deployment configuration. Terms acceptance is scoped to the case ID and terms version. Monthly derivation runs only for the case’s explicit `series.json` `derive_groups`; every group must have equal-length arrays.

HTML/PDF placeholders support `|dec1`, `|dec2`, `|dec4` and `|ratio` (two decimals plus `:1`). Workbook placeholders accept the same formats and remain numeric cells. Monthly row format names use the same vocabulary. `check.py` verifies extracted PDF/HTML text and XLSX displayed text from explicit supported number formats, in addition to stored values. Answer-key facts can set `text` for an exact display assertion, and `workbook` plus `sheet` for prose in a Notes sheet. Derived answers are checked by arithmetic from these cited inputs, not by searching for the answer in the room.

Tansy’s reconciliations cover monthly P&L identities, company and stream revenue totals, quarterly Kilcarrow contributions, audit/restatement bridges, customer totals and census versions. The 13.8% pitfall is calculated from the actual April–June 2026 Kilcarrow cells. The original Larkspur model checks have moved into its case-owned reconciliation specification.

After building both cases, run `python3 -I test_generator.py` for focused regression checks of displayed precision, non-food series and the output guard.
