import subprocess,re,json
from pathlib import Path
BASE='https://akw-data-room.maxfabian31.workers.dev'
CMD=['agent-browser','--session','tansy-final-codex-12cffe','--allowed-domains','akw-data-room.maxfabian31.workers.dev']
def b(*args):return subprocess.run(CMD+list(args),capture_output=True,text=True,check=True).stdout
for stem in ['2.7-v1','6.1-v1']:
 url=BASE+'/doc.html?id='+stem
 b('open',url);b('wait','--text','Version 1 (current)')
 text=b('get','text','main')
 assert len(text)>300
 original=Path('evidence/'+stem+'.txt').read_text().split('\n',1)[1]
 assert original==text,stem
 Path('work/verification-files/'+stem+'-viewer.txt').write_text(url+'\n'+text)
 print(stem,'current; text identical',flush=True)
b('open',BASE+'/qa.html');b('wait','--text','Q-07')
snap=b('snapshot')
for ref in ['Q-05','Q-06','Q-07','Q-09']:
 match=re.search(r'article "'+ref+r'.*?\[ref=(\w+)\]',snap)
 assert match,ref
 text=b('get','text','@'+match[1]);assert len(text)>100,ref
 Path('evidence/'+ref+'.txt').write_text(BASE+'/qa\n'+text)
 print(ref,text,flush=True)
b('click','button[aria-label="Page 2"]')
snap=b('snapshot');match=re.search(r'article "Q-12.*?\[ref=(\w+)\]',snap)
text=b('get','text','@'+match[1]);assert len(text)>100
Path('evidence/Q-12.txt').write_text(BASE+'/qa?page=2\n'+text)
print('Q-12',text,flush=True)
