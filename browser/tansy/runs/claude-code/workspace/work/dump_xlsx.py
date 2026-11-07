import sys, openpyxl
for p in sys.argv[1:]:
    print("=====", p)
    wb = openpyxl.load_workbook(p, data_only=False)
    for ws in wb.worksheets:
        print("--- sheet", ws.title, ws.dimensions)
        for row in ws.iter_rows():
            cells = [f"{c.coordinate}={c.value!r}" for c in row if c.value is not None]
            if cells: print("  ".join(cells))
