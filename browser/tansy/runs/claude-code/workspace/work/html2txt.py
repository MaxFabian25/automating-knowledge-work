import sys, html, re
from html.parser import HTMLParser
class T(HTMLParser):
    def __init__(s): super().__init__(); s.out=[]; s.skip=False
    def handle_starttag(s,t,a):
        if t in('script','style'): s.skip=True
        if t in('p','tr','li','h1','h2','h3','div','br','table','section'): s.out.append('\n')
        if t in('td','th'): s.out.append(' | ')
    def handle_endtag(s,t):
        if t in('script','style'): s.skip=False
    def handle_data(s,d):
        if not s.skip: s.out.append(d)
for p in sys.argv[1:]:
    t=T(); t.feed(open(p,encoding='utf-8').read())
    txt=re.sub(r'[ \t]+',' ',''.join(t.out)); txt=re.sub(r'\n\s*\n+','\n',txt)
    print('=========', p); print(txt.strip())
