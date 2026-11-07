from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from openpyxl import load_workbook
import json, hashlib
root=Path(__file__).resolve().parent
def wb(name): return load_workbook(root/'downloads'/name,data_only=True)
def dec(v): return Decimal(str(v))
def total(sheet,row,start,end): return sum(dec(sheet.cell(row,col).value) for col in range(start,end+1))
def rnd(value, places): return str(dec(value).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP))
a=wb('2.3-v1.xlsx'); b=wb('2.4-v1.xlsx'); c=wb('3.1-v1.xlsx'); d=wb('4.1-v2.xlsx')
p=a['P&L']; q=b['P&L']; k=b['Revenue by company']; t=c['Top customers']; census=d['Census']
prior=total(p,6,2,7); current=total(q,6,2,7)
org_current=current-dec(k['H8'].value); org_prior=prior-dec(k['I8'].value)
revenue=dec(t['B18'].value); cutoff=revenue*Decimal('.05')
customers={t.cell(r,1).value:dec(t.cell(r,2).value) for r in range(6,16) if dec(t.cell(r,2).value)>cutoff}
customers['Dunstreath Retail Group plc']=Decimal(3420) # Q-06; 1.2 v1 page 1
combined=sum(customers.values())
netdebt=Decimal(22000)+Decimal(6500)-Decimal(1860) # 2.8 v1 page 1
claim=Decimal(598000)+Decimal(44500) # 6.2 v1 page 1
claim_gbp=claim*Decimal('.8455') # 2.2 v1 page 2 note 1
results={
 'ltm_revenue':str(total(p,6,8,13)+current),
 'ltm_ebitda':str(total(p,16,8,13)+total(q,16,2,7)),
 'ltm_components':{'prior_revenue':str(total(p,6,8,13)),'current_revenue':str(current),'prior_ebitda':str(total(p,16,8,13)),'current_ebitda':str(total(q,16,2,7))},
 'h1_prior_revenue':str(prior),'reported_growth_pct':rnd((current/prior-1)*100,1),
 'organic_current':str(org_current),'organic_prior':str(org_prior),'organic_growth_pct':rnd((org_current/org_prior-1)*100,1),
 'customer_cutoff':str(cutoff),'qualifying_customers':{n:str(v) for n,v in customers.items()},
 'customer_shares_pct':{n:rnd(v/revenue*100,1) for n,v in customers.items()},
 'next_customer_share_pct':rnd(dec(t['B9'].value)/revenue*100,1),
 'combined_customer_revenue':str(combined),'combined_customer_share_pct':rnd(combined/revenue*100,1),
 'net_debt':str(netdebt),'reported_leverage_recomputed':rnd(netdebt/Decimal(9380),2),
 'quantified_claim_eur':str(claim),'claim_gbp':str(claim_gbp),'claim_gbp_thousands_rounded':rnd(claim_gbp/1000,0),
 'group_fte':rnd(sum(dec(census.cell(r,3).value) for r in range(6,9)),1),'kilcarrow_fte':rnd(census['C8'].value,1),
 'group_headcount':sum(census.cell(r,2).value for r in range(6,9)),
 'audited_fy2025_revenue_restatement':str(Decimal(52400)-750),'audited_fy2025_operating_profit_restatement':str(Decimal(4960)-410),
 'audit_revenue_adjustment':str(Decimal(750)-1040),'audit_ebitda_adjustment':str(Decimal(-290)-70),
 'whole_share_acquisition_votes_pct':rnd((Decimal(800000)+200000)/Decimal(1000000)*100,1),
 'file_checks':[]}
for delivered in sorted((root.parent/'deliverables/files').iterdir()):
 downloaded=root/'downloads'/('-'.join(delivered.name.split('-')[:2])+delivered.suffix)
 results['file_checks'].append({'delivered':str(delivered.relative_to(root.parent)),'current_download':str(downloaded.relative_to(root)), 'identical':delivered.read_bytes()==downloaded.read_bytes(),'sha256':hashlib.sha256(downloaded.read_bytes()).hexdigest()})
(root/'calculations.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
