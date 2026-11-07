import subprocess,time,hashlib,re,json,sys
from pathlib import Path
import openpyxl
BASE='https://akw-data-room.maxfabian31.workers.dev'
CMD=['agent-browser','--session','tansy-final-codex-12cffe','--allowed-domains','akw-data-room.maxfabian31.workers.dev']
def browser(*args):
 r=subprocess.run(CMD+list(args),capture_output=True,text=True,check=True)
 return r.stdout
checks={
'2.3-v1':('xlsx','evidence/2.3-v1.xlsx',{'P&L':['H6','M6','N6','H16','M16'],'Notes':['A6']}),
'2.4-v1':('xlsx','evidence/2.4-v1.xlsx',{'P&L':['B6','G6','H6','I6','B16','G16'],'Revenue by company':['H8','I8'],'Notes':['A8']}),
'2.2-v1':('pdf','deliverables/files/2.2-v1-audited-consolidated-financial-statements-fy2026.pdf',None),
'2.11-v1':('pdf','evidence/2.11-v1.pdf',None),
'2.8-v1':('pdf','evidence/2.8-v1.pdf',None),
'3.1-v1':('xlsx','evidence/3.1-v1.xlsx',{'Top customers':['B6','B7','B8','B18'],'Notes':['A5']}),
'6.2-v1':('pdf','evidence/6.2-v1.pdf',None),
'4.1-v2':('xlsx','evidence/4.1-v2.xlsx',{'Census':['C8','C9'],'Notes':['A5']})}
out=Path('work/verification-files');out.mkdir(exist_ok=True)
results={}
for stem,(ext,original,cells) in checks.items():
 if len(sys.argv)>1 and stem not in sys.argv[1:]:continue
 expected=hashlib.sha256(Path(original).read_bytes()).hexdigest()
 url=BASE+'/doc.html?id='+stem
 if ext=='pdf':browser('network','route','**/*.pdf','--abort')
 browser('open',url)
 browser('wait','--text',f'Version {stem.split("-v")[1]} (current)')
 main=browser('get','text','main')
 (out/(stem+'-viewer.txt')).write_text(url+'\n'+main)
 if ext=='pdf':browser('network','unroute','**/*.pdf')
 names=re.findall(r'[\w.-]+\.'+ext,main)
 filename=next(n for n in names if n.startswith(stem+'-'))
 p=Path('deliverables/files')/filename
 if p.exists():
  # Preserve exact delivered original during independent re-download.
  p.rename(out/(filename+'.prior'))
 browser('click',f'a[href$=".{ext}"]')
 for _ in range(100):
  if p.exists():break
  time.sleep(.1)
 if not p.exists():raise RuntimeError('Download missing '+filename)
 actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=expected:raise RuntimeError('Changed binary '+stem)
 if stem in ('2.2-v1','3.1-v1'):
  fresh=out/filename
  fresh.write_bytes(p.read_bytes())
 else:
  fresh=out/filename;p.rename(fresh)
 result={'version':'current','url':url,'sha256_matches_initial_evidence':True,'filename':filename}
 if cells:
  b=openpyxl.load_workbook(fresh,data_only=True)
  result['cells']={s:{c:b[s][c].value for c in cs} for s,cs in cells.items()}
 else:
  txt=subprocess.run(['pdftotext','-layout',str(fresh),'-'],capture_output=True,text=True,check=True).stdout
  (out/(stem+'-pdf.txt')).write_text(url+'\n'+txt)
  result['pdf_text_matches_initial']=txt==Path('evidence/'+stem+'.txt').read_text().split('\n',1)[1]
  assert result['pdf_text_matches_initial']
 results[stem]=result
 print(stem, 'current, re-downloaded original matches evidence',flush=True)
 Path('work/verification-results.json').write_text(json.dumps(results,indent=2)+'\n')
