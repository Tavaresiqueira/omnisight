"""Render only an inert offline snapshot. Page scripts/resources never run."""
import json
import os
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright
from visual_capture import capture_visual

ENGINE_VERSION='4.13.0'
AXE=Path(__file__).parent/'vendor'/'axe.min.js'
SNAPSHOT='https://snapshot.invalid/'
CSP="default-src 'none'; script-src 'none'; style-src 'unsafe-inline'; img-src 'none'; font-src 'none'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"

def analyze(html, stylesheets=None):
    if not isinstance(html,str) or len(html.encode())>2*1024*1024:
        raise ValueError('HTML inválido ou maior que 2 MiB.')
    with sync_playwright() as p:
        executable=os.environ.get('CHROMIUM_EXECUTABLE')
        browser=p.chromium.launch(headless=True,chromium_sandbox=True,**({'executable_path':executable} if executable else {}))
        try:
            context=browser.new_context(viewport={'width':1280,'height':800},accept_downloads=False,service_workers='block',locale='pt-BR')
            def route(request):
                if request.request.url==SNAPSHOT and request.request.is_navigation_request():
                    request.fulfill(status=200,content_type='text/html; charset=utf-8',headers={'Content-Security-Policy':CSP},body=html)
                else:
                    request.abort('blockedbyclient')
            context.route('**/*',route)
            page=context.new_page();page.set_default_timeout(15000)
            page.goto(SNAPSHOT,wait_until='domcontentloaded')
            for css in stylesheets or []:
                page.add_style_tag(content=css)
            # DevTools injection of trusted, bundled engine; source scripts remain CSP-blocked.
            page.evaluate(AXE.read_text())
            page.evaluate('(locale) => axe.configure({locale})',json.loads(AXE.with_name('pt_BR.json').read_text()))
            def audit():
                value=page.evaluate(Path(__file__).with_name('axe_scan.js').read_text())
                if value['engineVersion']!=ENGINE_VERSION:
                    raise ValueError('Versão da engine incompatível.')
                return value
            captures=capture_visual(page,audit)
            result={'engine':'axe-core','engineVersion':ENGINE_VERSION,'browserVersion':browser.version,'mode':'offline-html','title':page.title(),'checks':captures[0]['accessibilityChecks']}

            if result['engineVersion']!=ENGINE_VERSION:
                raise ValueError('Versão da engine incompatível.')
            result['limitations']=['Snapshot isolado: CSS inline e folhas fornecidas pelo coletor; scripts, imagens, fontes e imports externos bloqueados.','Contraste não avaliado neste modo. Testes de teclado, zoom, alvos e estados exigem revisão na página real.','Ausência de achados não comprova conformidade WCAG.']
            result['visual']=captures
            return result
        finally:
            browser.close()

if __name__=='__main__':
    raw=sys.stdin.buffer.read(4*1024*1024+65536)
    payload=json.loads(raw)
    result=analyze(payload['html'],payload.get('stylesheets',[]))
    encoded=json.dumps(result,ensure_ascii=False).encode()
    if len(encoded)>1024*1024:
        raise ValueError('Relatório maior que 1 MiB.')
    sys.stdout.buffer.write(encoded)
