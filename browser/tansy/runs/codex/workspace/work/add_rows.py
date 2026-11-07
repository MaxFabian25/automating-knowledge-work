import csv,json,sys
from pathlib import Path
p=Path('deliverables/answers.csv')
with p.open('a',newline='') as out:
    w=csv.writer(out)
    if p.stat().st_size==0:w.writerow(['Request','Item','Answer','Unit','Period','Basis','Source','Location','Note'])
    w.writerows(json.loads(Path(sys.argv[1]).read_text()))
