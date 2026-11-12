"""Bounded viewport evidence. No full-page capture or screenshot-based AI claims."""
import base64
from pathlib import Path

VIEWPORTS=[('desktop',1280,800),('mobile',390,844)]

def capture_visual(page,audit=None):
    captures=[]
    for name,width,height in VIEWPORTS:
        page.set_viewport_size({'width':width,'height':height})
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        metrics=page.evaluate(Path(__file__).with_name('visual.js').read_text())
        analysis=audit() if audit is not None else None
        raw=page.screenshot(type='jpeg',quality=50,full_page=False,animations='disabled',timeout=10000)
        item={'name':name,**metrics,'screenshot':None}
        if len(raw)<=220000:
            item['screenshot']={'mime':'image/jpeg','dataBase64':base64.b64encode(raw).decode()}
        else:
            item['screenshotWarning']='Captura omitida por exceder 220 kB.'
        if analysis is not None:
            item['accessibilityChecks']=analysis['checks']
        captures.append(item)
    return captures
