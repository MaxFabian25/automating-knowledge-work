from pathlib import Path
import openpyxl
for p in sorted(Path('deliverables/files').glob('2.[34]-*.xlsx')):
    target=Path('evidence')/(p.name[:6]+'.xlsx')
    p.rename(target)
for p in sorted(Path('evidence').glob('2.[34]-*.xlsx')):
    print(p)
    b=openpyxl.load_workbook(p,data_only=True)
    for s in b:
        print('SHEET',s.title)
        for row in s:
            print(' | '.join(f'{c.coordinate}={c.value}' for c in row if c.value is not None))
