import csv,json
from pathlib import Path
import openpyxl
f=json.loads(Path('work/figures.json').read_text())
b3=openpyxl.load_workbook('evidence/2.3-v1.xlsx',data_only=True)
b4=openpyxl.load_workbook('evidence/2.4-v1.xlsx',data_only=True)
for name,row in [('revenue',6),('ebitda',16)]:
 actual=[b3['P&L'].cell(row,c).value for c in range(8,14)]+[b4['P&L'].cell(row,c).value for c in range(2,8)]
 assert f['ltm'][name]==actual,name
assert f['growth']=={'current':b4['P&L']['H6'].value,'prior':b4['P&L']['I6'].value,'kilcarrow_current':b4['Revenue by company']['H8'].value,'kilcarrow_prior':b4['Revenue by company']['I8'].value}
bc=openpyxl.load_workbook('evidence/3.1-v1.xlsx',data_only=True)
assert f['customers']['total']==bc['Top customers']['B18'].value==b3['P&L']['N6'].value
for row in range(6,16):
 assert f['customers']['revenues'][bc['Top customers'].cell(row,1).value]==bc['Top customers'].cell(row,2).value
r=json.loads(Path('work/calculated.json').read_text())
rows=list(csv.DictReader(Path('deliverables/answers.csv').open()))
assert [x['Answer'] for x in rows if x['Request']=='1']==[str(r['ltm']['revenue']),str(r['ltm']['ebitda'])]
assert [x['Answer'] for x in rows if x['Request']=='2']==[r['growth']['reported'],r['growth']['organic']]
assert next(x['Answer'] for x in rows if x['Item']=='Combined share of customers above 5%')==r['customers']['share']
assert next(x['Answer'] for x in rows if x['Item']=='Claim translated at FY2026 closing rate')==r['claim_gbp000']
assert set(x.name for x in Path('deliverables/files').iterdir())=={'2.2-v1-audited-consolidated-financial-statements-fy2026.pdf','3.1-v1-top-customer-revenue-schedule-fy2026-and-six-months-to-30-september-2026.xlsx'}
print('All source-cell inputs, derived answer values and delivered filenames verified.')
