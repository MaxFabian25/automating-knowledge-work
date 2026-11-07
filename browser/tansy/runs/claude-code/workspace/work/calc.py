import json
from decimal import Decimal, ROUND_HALF_UP
F = json.load(open("/tmp/akw-runs/final-claude/work/figures.json"))
a, b = F["2.3-v1"], F["2.4-v1"]
r = lambda x, q="0.1": Decimal(str(x)).quantize(Decimal(q), ROUND_HALF_UP)
out = {}
out["R1 LTM revenue"] = sum(a["P&L!H6:M6 revenue Oct-25..Mar-26"]) + sum(b["P&L!B6:G6 revenue Apr-26..Sep-26"])
out["R1 LTM EBITDA bei"] = sum(a["P&L!H16:M16 EBITDA bei Oct-25..Mar-26"]) + sum(b["P&L!B16:G16 EBITDA bei Apr-26..Sep-26"])
assert sum(b["P&L!B6:G6 revenue Apr-26..Sep-26"]) == b["P&L!H6 revenue H1 FY2027"]
cur, prev = b["P&L!H6 revenue H1 FY2027"], b["P&L!I6 revenue H1 FY2026"]
out["R2 reported growth %"] = str(r((cur / prev - 1) * 100))
ocur, oprev = cur - b["Revenue by company!H8 Kilcarrow H1 FY2027"], prev - b["Revenue by company!I8 Kilcarrow H1 FY2026"]
out["R2 organic revenue H1 FY2027 / H1 FY2026"] = [ocur, oprev]
out["R2 organic growth %"] = str(r((ocur / oprev - 1) * 100))
c = F["2.8-v1"]
out["R4 leverage recomputed"] = str(r(c["net debt"] / c["covenant EBITDA LTM"], "0.01"))
tot = F["3.1-v1"]["Total revenue (management basis) B18"]
assert tot == a["P&L!N6 FY2026 revenue"]
cust = {k: v for k, v in F["3.1-v1"].items() if not k.startswith("Total")}
cust["Dunstreath Retail Group plc"] = F["Q-06"]["Dunstreath Retail Group plc FY2026 revenue"]
shares = {k: str(r(v / tot * 100)) for k, v in cust.items()}
out["R6 shares %"] = shares
over = {k: v for k, v in cust.items() if v / tot > 0.05}
out["R6 over 5%"] = over
out["R6 combined revenue"] = sum(over.values())
out["R6 combined share %"] = str(r(sum(over.values()) / tot * 100))
e = F["6.2-v1"]; assert e["Damages EUR"] + e["Quantified costs EUR"] == e["Total quantified claim EUR"]
gbp = Decimal(e["Total quantified claim EUR"]) * Decimal(str(F["2.2-v1"]["closing rate GBP per EUR 31 Mar 2026"]))
out["R8 GBP exact"] = str(gbp)
out["R8 GBP 000 rounded"] = str((gbp / 1000).quantize(Decimal("1"), ROUND_HALF_UP))
f = F["4.1-v2"]
out["R9 FTE sum check"] = str(r(f["FTE VF&S"] + f["FTE Monitoring"] + f["FTE Kilcarrow"]))
json.dump(out, open("/tmp/akw-runs/final-claude/work/results.json", "w"), indent=1)
print(json.dumps(out, indent=1))
