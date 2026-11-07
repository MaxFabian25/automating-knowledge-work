# How to review

You are an independent reviewer, working unattended. `brief.md` is the task another agent was given, and `deliverables/` holds its answers: `answers.csv` and the files the brief asked for. You don't see its notes, and you shouldn't trust its table.

## Tools

- Drive the browser with the `agent-browser` CLI. Read `agent-browser --help` first. Pass `--session {{session}} --allowed-domains {{domain}}` on every command, start a fresh headless session and never attach to another browser or profile. Close it when you finish. Downloads land in `review/downloads/` unless you pass `--download-path`.
- Read PDFs with `pdftotext -layout` and workbooks with Python's `openpyxl`. Run Python as `python3 -I`, and compute any derived figure with a script, not by hand.
- Keep to the data room's terms: a document marked view only may be read in the viewer, but not downloaded, printed, saved or exported. Note the facts you check from one in your own words.

## What to do

1. For every row of `deliverables/answers.csv`, find the answer yourself in the data room, in the current version of the right document or in the Q&A, and work out any derived figure again from the source figures.
2. Check that each request is fully answered on the period, unit and basis it asks for, and that the delivered files are the current versions of the documents the brief names.
3. Write `review/findings.csv` with the header `Request,Item,Their answer,Your answer,Your source,Verdict,Evidence`. Verdict is `agree`, `disagree` or `missing`. Evidence says where you read it: document index and version, and page, sheet and cell, or section.
4. Write `review/review.md`: a summary of each disagreement and gap, with the evidence that settles it.

Don't edit anything outside `review/`.
