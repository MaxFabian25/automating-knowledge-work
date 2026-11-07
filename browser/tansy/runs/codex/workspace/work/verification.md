# Final source verification — 7 November 2026

Every cited source was opened again in the data room after completing the table. Browser commands used the designated isolated session and allowed-domain restriction. No superseded document was used.

For downloadable sources, `work/verify_sources.py` reopened each viewer, checked its current-version label, clicked Download again, and compared SHA-256 hashes with the original evidence. All eight binary files matched exactly. PDFs were read again with `pdftotext -layout` and their full extracted text matched the saved evidence. Workbooks were read with openpyxl. Results and viewer metadata are in `work/verification-results.json` and `work/verification-files/`. For the PDF viewers, preview requests were temporarily blocked to avoid the observed browser execution-context failure; the block was removed before clicking Download. These are downloadable sources, not view-only documents.

| Source | Figures, version and locations confirmed |
| --- | --- |
| 2.3 v1 | Current. P&L H6:M6 and H16:M16 are October 2025–March 2026 revenue and EBITDA before exceptional items. Full FY2026 management revenue N6 is 62090. Notes A6 confirms consolidation of Kilcarrow from 1 July 2025. |
| 2.4 v1 | Current. P&L B6:G6 and B16:G16 supply April–September 2026 monthly figures. H6/I6 are 34380/28450; Revenue by company H8/I8 are Kilcarrow 4020/1880. Notes A8 defines organic growth by excluding acquired businesses from both periods within a 24-month lookback. All monthly inputs checked against figures.json by verify_figures.py. |
| 2.2 v1 | Current. Page 1 audited P&L: FY2026 revenue 61800, operating profit 5630; restated FY2025 51650 and 4550. Page 2 note 2 explains original 52400 and 4960 and the restatement. Note 1 closing rate is GBP0.8455 per EUR. Note 4 reports completion cash, redacted contingent estimate and total accruals, without outstanding deferred consideration or payment dates. Note 5 provision is GBP210k at 31 March 2026. Re-downloaded original PDF matches delivered file. |
| 2.11 v1 | Current. Page 1 Agreed amendment sets 3.25x for 30 September 2026–31 March 2027 inclusive; returns to 3.00x from 30 June 2027. It leaves other terms, including change of control, unchanged. |
| 2.8 v1 | Current. Page 1 certificate reports leverage 2.84x and maximum 3.25x at 30 September 2026. Net debt 26640 and covenant-defined EBITDA 9380 support the reported ratio; the EBITDA basis permits add-backs. |
| 2.7 v1 | Current, though its covenant summary predates the amendment. Reopened viewer text equals initial evidence. Financial covenants states 3.00x. Change of control states more than 50% voting control, exception for Skerrow-advised funds, advance Majority Lender consent, and individual lenders' cancellation/immediate repayment rights by notice within 30 days after change of control. |
| Q-07 | Reopened Q&A page 1; answer dated 2 November 2026 confirms amendment precedence over the unupdated 2.7 summary. Saved actual article text with URL. |
| Q-09 | Reopened Q&A page 1; still Awaiting documents. SPA and lifting contingent consideration redaction await vendor consent. No consideration amount or due date supplied. |
| 3.1 v1 | Current. Top customers B6:B8: Wendmoor 5960, Larchfold 4310, Corrigal 3240; B18 total management revenue 62090. B9:B15 each below 5%. Notes A5 says schedule covers largest H1 FY2027 continuing customers, excludes ceased customers, and all other continuing customers each contributed below 2% in both periods. Re-downloaded XLSX matches delivered original. |
| Q-06 | Reopened Q&A page 1; Dunstreath FY2026 management revenue 3420, contract ended 31 March 2026, all other ceased customers below 250. Completes the FY2026 concentration population. |
| 6.2 v1 | Current. Page 1 quantified demand lists damages EUR598000, costs EUR44500 and total EUR642500. Interest is unquantified and excluded from that total. |
| 6.1 v1 | Current. Reopened viewer text equals initial evidence. Ardnacree row gives EUR598000 and paragraph expressly identifies damages-only scope. This does not replace the letter's total quantified demand. |
| 4.1 v2 | Current. Census C8/C9 are Kilcarrow FTE 58.6/group FTE 609.8. Notes A5 defines FTE using contracted hours, excludes agency workers and includes complete group scope. |
| Q-05 | Reopened Q&A page 1; confirms Kilcarrow employed fixed-term staff included in v2, agency excluded. |
| Q-12 | Reopened Q&A page 2; confirms v2 complete and v1 omitted Kilcarrow. |
| 4.2 v1 | Reopened viewer, checked current version 1 in header, HTML format and restricted access status. No Download link is available. Only an own-word note about access restrictions is retained in evidence/4.2-v1.md; no document copy or extract was saved. |

`work/verify_text_sources.py` verified HTML sources and re-read Q&A articles. Final audit caught that the initial Q&A CSS text-selector commands had produced empty captures; these were replaced with actual article text obtained through browser snapshot references, consistent with what had been read on screen. The answers did not change.

`python3 -I work/verify_figures.py` checked every LTM source-cell input, growth inputs, customer revenues and denominator against openpyxl values, checked all derived values against answers.csv, and confirmed exactly the two requested permitted originals are in deliverables/files. `work/calculate.py` computes LTM sums, growth rates, customer selection and combined share, and claim currency conversion from work/figures.json.

Final expected derived answers: LTM 68020 revenue and 9260 EBITDA; reported growth 20.8%; organic growth 14.3%; qualifying customers total 16930 and share 27.3%; claim GBP543k. The source explicitly gives FTE totals, so no headcount-to-FTE estimate was made.

## Independent-review resolution — 7 November 2026

Read both review/findings.csv and review/review.md. The reviewer recorded 30 agreements, no disagreements and no missing rows. Resolved both minor notes against fresh room evidence:

- Request 5: reopened current 1.2 v1 in the viewer, used its Download PDF link, and read the original with `pdftotext -layout`. Page 1, Investment overview describes an initial EUR 9.6m plus earn-out. Saved original and URL-prefixed text in evidence/1.2-v1.pdf and evidence/1.2-v1.txt before changing the answer table. Reopened/re-downloaded current 2.2 v1 and reread page 2 note 4, and reopened Q-09, which remains Awaiting documents. Added the 1.2 citation and context to the deferred-consideration row. Retained unavailable balance/dates: no separate deferred element is identified, but the missing SPA prevents confirmation of zero. The contingent balance remains redacted.
- Request 6: reopened current 3.1 v1, re-downloaded the original and confirmed its SHA-256 matches the existing evidence; inspected Top customers B6/B7/B8/B18 with openpyxl. Reopened Q-06 and confirmed Dunstreath 3420 and the other ceased-customer threshold. Reordered individual customers to 5960, 4310, 3420, 3240; retained the combined share of 27.3%.

Reverification of every other cited source was also completed in this follow-up:

| Sources | Fresh check and result |
| --- | --- |
| 2.3 v1; 2.4 v1 | Current headers, Download links and original-file hashes confirmed. Used openpyxl and work/verify_figures.py to check every monthly LTM input and growth input against work/figures.json; answers remain 68020, 9260, 20.8% and 14.3%. Request 1 checked before proceeding; checker passed. Locations remain P&L H6:M6/H16:M16 in 2.3 and B6:G6/B16:G16 in 2.4; growth H6/I6, Revenue by company H8/I8, Notes A8 and 2.3 Notes A6. |
| 2.2 v1 | Current header and re-downloaded original hash confirmed. pdftotext output identical to saved evidence, including page 1 comparable audited results and page 2 notes 1, 2, 4 and 5. Delivered original remains identical. |
| 2.11 v1; 2.8 v1 | Current headers and re-downloaded original hashes confirmed; pdftotext matches evidence. Page 1 amendment permits 3.25x, leaves change-of-control clause unchanged; certificate page 1 reports 2.84x. |
| 2.7 v1; Q-07 | Reopened summary and Q&A. Summary viewer text identical to evidence; Financial covenants and Change of control sections checked. Q-07 reconfirms amendment precedence. |
| 6.2 v1; 6.1 v1 | Current headers checked. Re-downloaded letter and pdftotext matched evidence, page 1 total 642500 EUR including quantified costs; schedule viewer text identical and expressly damages-only. Conversion and provision remain supported by 2.2 notes 1 and 5. |
| 4.1 v2; Q-05; Q-12 | Current v2 header and re-downloaded original hash confirmed; openpyxl Census C8/C9 gives 58.6 and 609.8, Notes A5 confirms complete perimeter. Reopened both Q&A entries to confirm fixed-term employee inclusion and v2 completeness. |
| 4.2 v1 | Reopened and read viewer only; header confirms current version 1, HTML and view-only restriction. No Download control. Opening paragraph directs authorised release through Q&A. Existing own-word evidence note remains accurate; no document copy or extract saved. |

Browser PDF preview failure caused a session reset and loss of the configured download destination. Reaccepted terms, preserved/restored the delivered original, then started a fresh headless session with the required download directory and repeated the affected 3.1/6.2 checks successfully; 4.1 also succeeded. Unrequested originals are outside deliverables/files. The two requested permitted original files alone remain in that folder.

Ran `python3 -I check_answers.py` immediately after each of the two answers.csv changes; both passed (30 rows, all 10 requests, zero failures). Ran `python3 -I work/verify_figures.py` after successful final downloads; all source-cell inputs, derived figures and delivered filenames verified. No numerical answer changed.
