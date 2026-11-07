import json
from pathlib import Path
f=json.loads(Path('work/figures.json').read_text())
r={}
if 'ltm' in f:
    r['ltm']={k:sum(v) for k,v in f['ltm'].items()}
if 'growth' in f:
    g=f['growth']; r['growth']={'reported':f"{(g['current']/g['prior']-1)*100:.1f}",'organic':f"{((g['current']-g['kilcarrow_current'])/(g['prior']-g['kilcarrow_prior'])-1)*100:.1f}"}
if 'customers' in f:
    g=f['customers']; selected={k:v for k,v in g['revenues'].items() if v/g['total']>0.05}
    r['customers']={'selected':selected,'sum':sum(selected.values()),'share':f"{sum(selected.values())/g['total']*100:.1f}"}
if 'claim' in f:
    from decimal import Decimal, ROUND_HALF_UP
    g=f['claim']; r['claim_gbp000']=str((Decimal(str(g['eur']))*Decimal(str(g['gbp_per_eur']))/1000).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
Path('work/calculated.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
