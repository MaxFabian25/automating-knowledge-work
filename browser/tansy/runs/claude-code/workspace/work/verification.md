# Verification (2026-11-07)

How I checked: I opened each cited source again in the data room's viewer (agent-browser session tansy-final-claude-29b2f3) and confirmed that the header reads "Version N (current)". For every downloadable source I clicked the viewer's Download button a second time, saved the copy to work/verify/, and compared it byte for byte (`cmp`) with the file saved under evidence/. All were identical, so every figure and cell reference taken from the evidence copy also matches what the data room serves now. I deleted the copies after the comparison. I read the view-only documents (1.4, 4.2) in the viewer only.

| Source | Viewer version | Re-download identical | Figures / locations confirmed |
|---|---|---|---|
| 2.3 v1 | Version 1 (current) | yes | P&L H6:M6 revenue 5,420…6,100; H16:M16 EBITDA 750…792; N6 62,090 |
| 2.4 v1 | Version 1 (current) | yes | P&L B6:G6, B16:G16, H6 34,380, I6 28,450; Revenue by company H8 4,020, I8 1,880; Notes A8 organic definition |
| 2.2 v1 | Version 1 (current) | yes | p1 P&L: revenue 61,800 / 51,650 restated; operating profit 5,630 / 4,550; p2 note 1 closing rate 0.8455; note 4 earn-out redacted; note 5 provision 210 (page split checked with pdftotext -f/-l) |
| 2.7 v1 | Version 1 (current) | yes | Change-of-control section; covenant 3.00:1 (superseded by 2.11) |
| 2.8 v1 | Version 1 (current) | yes | Leverage 2.84:1 reported, maximum 3.25:1; net debt 26,640; covenant EBITDA 9,380 |
| 2.11 v1 | Version 1 (current) | yes | 3.25:1 for test dates 30 Sep 2026 to 31 Mar 2027; change-of-control clause unchanged |
| 1.2 v1 | Version 1 (current) | yes | Dunstreath FY2026 revenue 3,420 |
| 1.4 v1 | Version 1 (current), view only | n/a (view only) | Re-read in viewer: 1,000,000 shares, one class, Skerrow 80% / management 20% |
| 3.1 v1 | Version 1 (current) | yes | Top customers B6 5,960, B7 4,310, B8 3,240, B9 2,980, B18 62,090 |
| 6.2 v1 | Version 1 (current) | yes | Total quantified claim EUR 642,500 (damages 598,000 + costs 44,500) |
| 4.1 v2 | Version 2 (current); v1 is superseded | yes | Census C8 58.6 (Kilcarrow), C9 609.8 (total) |
| 4.2 v1 | Version 1 (current), view only | n/a: no download button | View-only banner present; no download offered |
| Q-05, Q-06, Q-07, Q-09, Q-12 | Q&A page (pages 1 and 2) | n/a | Answer text re-read on the Q&A page and matches evidence/Q-xx.txt |

Deliverable files: deliverables/files/2.2-v1-…fy2026.pdf and 3.1-v1-….xlsx are byte-identical to evidence/2.2-v1.pdf and evidence/3.1-v1.xlsx, which are byte-identical to the fresh downloads.
I derived every figure with work/calc.py from work/figures.json (results in work/results.json) and wrote the table with work/build_answers.py.
`python3 -I check_answers.py`: 31 rows, 0 failures.

## Re-check after independent review (2026-11-07)

The reviewer (review/findings.csv, review/review.md) agreed with all 31 rows, so I changed no answers. To settle the two remaining gaps, I went back into the data room and accepted the terms again:
- I fetched the current `data/index.json` and `data/qa.json` through the browser session (saved in work/recheck/) and compared them with work/index.json and work/qa.json. Both are identical: no new documents or versions, and no new Q&A answers.
- Q-09 still shows "Awaiting documents" on the rendered Q&A page. The SPA has not been added and the 2.2 note 4 redaction is still in place, so request 5 stays unanswered.
- The 4.2 v1 viewer still shows "Version 1 (current)" and "View only. This document cannot be downloaded or printed.", and there is no download link among the page's controls. Request 10 stays recorded as restricted.
