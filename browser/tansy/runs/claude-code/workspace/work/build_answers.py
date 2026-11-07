import csv, json
R = json.load(open("/tmp/akw-runs/final-claude/work/results.json"))
H = ["Request","Item","Answer","Unit","Period","Basis","Source","Location","Note"]
rows = []
def add(*a): rows.append(dict(zip(H, a)))
MA = "Monthly management accounts (unaudited, before audit adjustments)"
# Request 1
add(1, "Revenue, last twelve months", str(R["R1 LTM revenue"]), "GBP thousands", "12 months to 30 September 2026 (Oct 2025 to Sep 2026)", MA,
    "2.3 v1; 2.4 v1", "2.3 v1 sheet P&L cells H6:M6 (Oct-25 to Mar-26); 2.4 v1 sheet P&L cells B6:G6 (Apr-26 to Sep-26)",
    "Sum of 12 monthly figures, computed in work/calc.py (33,640 + 34,380). Same result as FY2026 62,090 less H1 FY2026 28,450 plus H1 FY2027 34,380.")
add(1, "EBITDA before exceptional items, last twelve months", str(R["R1 LTM EBITDA bei"]), "GBP thousands", "12 months to 30 September 2026 (Oct 2025 to Sep 2026)", MA,
    "2.3 v1; 2.4 v1", "2.3 v1 sheet P&L cells H16:M16; 2.4 v1 sheet P&L cells B16:G16",
    "Sum of 12 monthly figures (4,740 + 4,520), computed in work/calc.py. Not the same as the covenant 'Consolidated EBITDA as defined' of 9,380 in the compliance certificate (2.8 v1), which adds back further items under the facility definitions. Nor is it audited: the FY2026 audit adjustments in 2.6 v1 (EBITDA -360) are not reflected in the monthly accounts.")

# Request 2
H1 = "Six months to 30 September 2026 (H1 FY2027) vs six months to 30 September 2025 (H1 FY2026)"
add(2, "Revenue growth, as reported", R["R2 reported growth %"], "%", H1, MA,
    "2.4 v1", "2.4 v1 sheet P&L cells H6 (H1 FY2027 34,380) and I6 (H1 FY2026 28,450)",
    "34,380 / 28,450 - 1, computed in work/calc.py. I took 'the same six months of 2025' to mean April to September 2025, which is H1 FY2026.")
add(2, "Revenue growth, organic (group definition)", R["R2 organic growth %"], "%", H1, MA + "; organic as defined in 2.4 v1 Notes",
    "2.4 v1", "2.4 v1 sheet Notes cell A8 (definition); sheet Revenue by company cells H8 and I8 (Kilcarrow 4,020 and 1,880); sheet P&L cells H6 and I6",
    "The group's definition takes out, in both periods, the revenue of any business acquired in the 24 months before the end of the current period. Kilcarrow was acquired on 1 July 2025, within the 24 months to 30 September 2026, so it is excluded from both periods. Organic revenue is 30,360 (34,380 - 4,020) against 26,570 (28,450 - 1,880). Computed in work/calc.py.")
# Request 3
AUD = "Audited, FRS 102; FY2025 as restated in the FY2026 statements (comparable basis)"
note25 = ("These figures differ from 2.1 v1, the FY2025 statements as first reported: revenue 52,400 and operating profit 4,960. I relied on the restated FY2025 comparative in 2.2 v1, "
          "because note 2 restates FY2025 to correct installation revenue that had been recognised ahead of stage of completion (revenue -750, operating profit -410). "
          "That puts FY2025 on the same basis as FY2026.")
add(3, "Audited revenue FY2025 (restated)", "51650", "GBP thousands", "FY2025 (year ended 31 March 2025)", AUD,
    "2.2 v1", "2.2 v1 page 1, consolidated profit and loss account, column 2025 (restated); page 2 note 2", note25)
add(3, "Audited operating profit FY2025 (restated)", "4550", "GBP thousands", "FY2025 (year ended 31 March 2025)", AUD,
    "2.2 v1", "2.2 v1 page 1, consolidated profit and loss account, column 2025 (restated); page 2 note 2", note25)
add(3, "Audited revenue FY2026", "61800", "GBP thousands", "FY2026 (year ended 31 March 2026)", AUD,
    "2.2 v1", "2.2 v1 page 1, consolidated profit and loss account, column 2026",
    "Audited figure. The management accounts show 62,090; the difference is the net installation cut-off adjustment of -290 (2.6 v1, Q-01).")
add(3, "Audited operating profit FY2026", "5630", "GBP thousands", "FY2026 (year ended 31 March 2026)", AUD,
    "2.2 v1", "2.2 v1 page 1, consolidated profit and loss account, column 2026; page 2 note 3",
    "Stated after exceptional acquisition costs of 170 (note 3).")
# Request 4
add(4, "Maximum leverage (net debt to EBITDA) permitted at the 30 September 2026 test date", "3.25", "x", "Test date 30 September 2026",
    "Senior facilities agreement as amended by the letter of 12 August 2026; facility definitions",
    "2.11 v1; Q-07; 2.8 v1", "2.11 v1 page 1, 'Agreed amendment'; Q-07 answer; 2.8 v1 page 1, Leverage row, Requirement column",
    "The documents differ. The senior facilities summary (2.7 v1, dated 20 July 2026) gives 3.00:1. I relied on the executed amendment letter of 12 August 2026 (2.11 v1), which sets 3.25:1 for test dates from 30 September 2026 to 31 March 2027 and 3.00:1 again from 30 June 2027. It is later and executed, and Q-07 confirms that 2.7 predates it. The compliance certificate (2.8 v1) also shows a maximum of 3.25:1.")
add(4, "Leverage reported for the 30 September 2026 test date", "2.84", "x", "Test date 30 September 2026; EBITDA for the twelve months to 30 September 2026",
    "Compliance certificate; covenant definitions (net debt / Consolidated EBITDA as defined)",
    "2.8 v1", "2.8 v1 page 1, Leverage row, Reported column (2.84:1)",
    "Net debt is 26,640 (term loan 22,000 + RCF 6,500 - cash 1,860) and Consolidated EBITDA as defined is 9,380. 26,640 / 9,380 = 2.84, which I re-computed in work/calc.py. The covenant EBITDA is not the management accounts LTM EBITDA of 9,260 (request 1), because it adds back share-based payments and other items the facility permits. Headroom against the 3.25 maximum.")
# Request 5
NA5 = "The Kilcarrow SPA has not been provided (Q-09: awaiting documents, to be released once the Kilcarrow vendors consent to disclosure)."
add(5, "Contingent consideration (earn-out) outstanding for Kilcarrow", "Not answered by the data room: the amount is redacted in the data-room extract of the FY2026 statements (note 4) and the SPA is not available. Missing: the earn-out amount (directors' estimate or SPA terms).",
    "GBP thousands", "At 31 March 2026 (latest disclosure); no later figure in the data room", "Audited FY2026 statements (data-room extract, amount redacted)",
    "2.2 v1; Q-09", "2.2 v1 page 2, note 4 Acquisition; Q-09",
    "Note 4 says only that the directors' estimate is included within accruals of 4,120 in total. That 4,120 is a total for all accruals, not the earn-out, so I have not reported it as the answer. " + NA5)
add(5, "Contingent consideration: when payment falls due", "Not answered by the data room: no payment date is given. The only disclosure is that the earn-out is calculated on Kilcarrow's EBITDA for the year ending 31 March 2027 (FY2027). Missing: SPA payment terms.",
    "n/a", "Earn-out measurement period FY2027 (year ending 31 March 2027)", "Audited FY2026 statements (data-room extract)",
    "2.2 v1; Q-09", "2.2 v1 page 2, note 4 Acquisition; Q-09",
    "I have not estimated a payment date. " + NA5)
add(5, "Deferred consideration outstanding for Kilcarrow", "Not answered by the data room: no deferred consideration is disclosed. Note 4 of the FY2026 statements mentions only cash of 8,280 (EUR 9.6m) paid on completion and the contingent consideration. Missing: the SPA, to confirm whether any deferred consideration exists.",
    "GBP thousands", "At 31 March 2026 (latest disclosure)", "Audited FY2026 statements (data-room extract)",
    "2.2 v1; Q-09", "2.2 v1 page 2, note 4 Acquisition; Q-09",
    "The management presentation (1.2 v1) also describes the price only as initial EUR 9.6m plus an earn-out. " + NA5)
add(5, "Deferred consideration: when payment falls due", "Not answered by the data room: no deferred consideration or payment date is disclosed. Missing: SPA payment terms.",
    "n/a", "n/a", "Audited FY2026 statements (data-room extract)",
    "2.2 v1; Q-09", "2.2 v1 page 2, note 4 Acquisition; Q-09", NA5)
# Request 6
P26 = "FY2026 (year ended 31 March 2026)"
MAC = "Management accounts basis; revenue across all group companies, contracts and project work"
add(6, "Wendmoor Housing Group: FY2026 revenue", "5960", "GBP thousands", P26, MAC, "3.1 v1", "3.1 v1 sheet Top customers cell B6",
    "9.6% of FY2026 revenue of 62,090 (3.1 v1 cell B18).")
add(6, "Larchfold Facilities Management Ltd: FY2026 revenue", "4310", "GBP thousands", P26, MAC, "3.1 v1", "3.1 v1 sheet Top customers cell B7",
    "6.9% of FY2026 revenue of 62,090.")
add(6, "Dunstreath Retail Group plc: FY2026 revenue", "3420", "GBP thousands", P26, MAC, "Q-06; 1.2 v1", "Q-06 answer; 1.2 v1 page 1, 'Trading and customers'",
    "5.5% of FY2026 revenue of 62,090. Dunstreath is not in the top-customer schedule (3.1 v1), which lists only customers still trading with the group. Its contract ended on 31 March 2026, but it was a customer for the whole of FY2026, so it falls within the request. Q-06 and 1.2 v1 both give 3,420 on the management accounts basis.")
add(6, "Corrigal Retail Parks plc: FY2026 revenue", "3240", "GBP thousands", P26, MAC, "3.1 v1", "3.1 v1 sheet Top customers cell B8",
    "5.2% of FY2026 revenue of 62,090.")
add(6, "Combined FY2026 revenue of customers above 5%", str(R["R6 combined revenue"]), "GBP thousands", P26, MAC, "3.1 v1; Q-06", "3.1 v1 sheet Top customers cells B6:B8; Q-06",
    "5,960 + 4,310 + 3,420 + 3,240, computed in work/calc.py.")
add(6, "Combined share of FY2026 revenue of customers above 5%", R["R6 combined share %"], "%", P26, MAC, "3.1 v1; Q-06; 2.3 v1",
    "3.1 v1 sheet Top customers cells B6:B8 and B18; Q-06; 2.3 v1 sheet P&L cell N6",
    "16,930 / 62,090, computed in work/calc.py. The threshold is 5% of 62,090 = 3,104.5. The next-largest customer, Thornacre Care Homes (2,980, 4.8%), is below it. 3.1 v1 says every other continuing customer had less than 2.0%, and Q-06 says no other departed customer had more than 250 of FY2026 revenue.")
# Request 7
CoC = "Senior facilities change-of-control clause (as summarised in 2.7; unchanged by the 12 August 2026 amendment)"
add(7, "Does acquisition of the whole issued share capital need senior lenders' consent?", "Yes. A buyer of all the shares would gain control: 100% of the voting shares, above the 'more than 50%' threshold. The only exception is funds advised by Skerrow Capital Partners. Without the Majority Lenders' consent in advance, the acquisition is a change of control that triggers the lender rights below.",
    "n/a", "Facilities as at 30 September 2026", CoC, "2.7 v1; 2.11 v1; 1.4 v1",
    "2.7 v1 section 'Change of control'; 2.11 v1 page 1 'Agreed amendment'; 1.4 v1 register (view only, noted)",
    "The consent must come from the Majority Lenders, and in advance. 2.11 v1 confirms the change-of-control clause is unchanged by the amendment. 1.4 v1 shows a single class of 1,000,000 ordinary shares (Skerrow funds 80%, management 20%), so buying the whole issued share capital gives 100% of the votes. 2.7 v1 is a summary; the full facilities agreement is not in the data room.")
add(7, "If consent is not obtained: what lenders may do", "Each lender may cancel its commitment and declare its share of all loans immediately due and payable.",
    "n/a", "n/a", CoC, "2.7 v1; 2.11 v1", "2.7 v1 section 'Change of control'",
    "The right belongs to each lender individually, not to the syndicate as a whole. Commitments are a term loan of 22,000 and an RCF of 8,000 (2.7 v1).")
add(7, "If consent is not obtained: period for lenders to act", "Within 30 days after the change of control, by notice from the lender.",
    "n/a", "30 days after the change of control", CoC, "2.7 v1; 2.11 v1", "2.7 v1 section 'Change of control'", "")
# Request 8
add(8, "Ardnacree claim: total quantified claim in the letter of claim", "642500", "EUR", "Letter of claim dated 12 March 2026",
    "Claimant's quantified demand (damages EUR 598,000 + quantified costs EUR 44,500); excludes interest, which is claimed but not quantified",
    "6.2 v1", "6.2 v1 page 1, table row 'Total quantified claim'",
    "The documents differ. The litigation schedule (6.1 v1) shows EUR 598,000, but it records damages only. I relied on the letter itself (6.2 v1) for the exact quantified total, as the request asks.")
add(8, "Ardnacree claim: GBP equivalent at FY2026 audited closing rate", R["R8 GBP 000 rounded"], "GBP thousands", "Closing rate at 31 March 2026",
    "EUR 642,500 x GBP 0.8455 per EUR (closing rate in the FY2026 audited statements)",
    "6.2 v1; 2.2 v1", "6.2 v1 page 1 'Total quantified claim'; 2.2 v1 page 2 note 1 Accounting policies (closing rate)",
    "GBP 543,233.75 rounded to the nearest 1,000 (work/calc.py). I did not use the average rate of 0.8512, because the request asks for the closing rate.")
add(8, "Provision held for the Ardnacree claim", "210", "GBP thousands", "At 31 March 2026", "Audited FY2026 statements",
    "2.2 v1", "2.2 v1 page 2 note 5 Provisions",
    "The directors dispute the claim; the provision is their best estimate of the settlement and associated costs. No proceedings had been issued (Q-04).")
# Request 9
CEN = "Employee census v2; FTE = contracted hours / standard full-time hours; agency workers excluded"
add(9, "Group total FTE employees", "609.8", "FTE", "At 30 September 2026", CEN, "4.1 v2; Q-12", "4.1 v2 sheet Census cell C9",
    "I used census version 2 (19 October 2026). Version 1 is superseded and left out Kilcarrow (Q-12). The three company FTE figures (476.3 + 74.9 + 58.6) add up to 609.8 (work/calc.py). Headcount is a separate measure: 641.")
add(9, "Kilcarrow Fire Protection Limited FTE employees", "58.6", "FTE", "At 30 September 2026", CEN, "4.1 v2; Q-05", "4.1 v2 sheet Census cell C8",
    "Includes Kilcarrow's employed fixed-term staff and excludes agency workers (Q-05). Kilcarrow headcount is 62.")
# Request 10
add(10, "Document 2.2: Audited consolidated financial statements FY2026", "Provided: deliverables/files/2.2-v1-audited-consolidated-financial-statements-fy2026.pdf",
    "n/a", "FY2026 (year ended 31 March 2026)", "Original PDF, current version 1", "2.2 v1", "Document viewer 2.2 v1, Download PDF button",
    "This is the data-room extract: the vendor has redacted the contingent consideration amount (note 4) and says the redaction is not part of the audited annual report.")
add(10, "Document 3.1: Top-customer revenue schedule", "Provided: deliverables/files/3.1-v1-top-customer-revenue-schedule-fy2026-and-six-months-to-30-september-2026.xlsx",
    "n/a", "FY2026 and six months to 30 September 2026", "Original XLSX, current version 1", "3.1 v1", "Document viewer 3.1 v1, Download XLSX button",
    "The schedule leaves out customers that no longer trade with the group, such as Dunstreath (see Q-06).")
add(10, "Document 4.2: Senior management service agreements summary", "Not provided: restricted. 4.2 v1 is marked view only, the viewer offers no download, and the terms of access (paragraph 4) forbid downloading, printing, saving or exporting view-only documents. Missing: an authorised downloadable version, which the vendor would have to release on request through Q&A.",
    "n/a", "Position at 30 September 2026", "View-only HTML, current version 1", "4.2 v1", "Document viewer 4.2 v1, view-only banner; terms of access paragraph 4",
    "The document can be read in the data room's viewer. No copy has been made.")
with open("/tmp/akw-runs/final-claude/deliverables/answers.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=H); w.writeheader(); w.writerows(rows)
print(len(rows), "rows")
