import csv,sys
from pathlib import Path
p=Path('deliverables/answers.csv')
with p.open(newline='') as f:
    reader=csv.DictReader(f)
    fields=reader.fieldnames
    rows=list(reader)
if sys.argv[1]=='5':
    row=next(r for r in rows if r['Item']=='Deferred consideration outstanding')
    row['Source']='2.2 v1; 1.2 v1; Q-09'
    row['Location']='2.2 page 2 note 4 Acquisition; 1.2 page 1 Investment overview; Q-09 answer (Awaiting documents)'
    row['Note']='1.2 describes initial EUR 9.6m plus an earn-out; no separate deferred element is identified. No zero balance inferred without the SPA or payment schedule. The 8280 cash paid at completion in 2.2 is not an outstanding balance.'
elif sys.argv[1]=='6':
    positions=[i for i,r in enumerate(rows) if r['Request']=='6' and r['Unit']=='GBP000']
    customers=sorted((rows[i] for i in positions),key=lambda r:int(r['Answer']),reverse=True)
    for i,r in zip(positions,customers):rows[i]=r
else:raise ValueError('Expected request 5 or 6')
with p.open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields)
    writer.writeheader();writer.writerows(rows)
