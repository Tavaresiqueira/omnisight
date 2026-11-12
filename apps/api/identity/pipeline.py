"""Bounded crawl and private browser contract, with no database dependencies."""
import hashlib
import math
import base64
import binascii
import json
import os
import sys
from urllib.request import Request, urlopen
from identity.crawler import crawl
from identity.stylesheets import collect_stylesheets
MAX_REPORT_BYTES = 1024 * 1024

def validate_analysis(result):
    if not isinstance(result,dict) or result.get('engine')!='axe-core' or result.get('engineVersion')!='4.13.0' or result.get('mode')!='offline-html':
        raise ValueError('Contrato do analisador incompatível.')
    checks=result.get('checks')
    if not isinstance(checks,list) or len(checks)>500:
        raise ValueError('Lista de verificações inválida.')
    for check in checks:
        if not isinstance(check,dict) or check.get('status') not in {'issue','review','clear','na'} or type(check.get('count')) is not int or check['count']<0:
            raise ValueError('Verificação inválida.')
        if any(not isinstance(check.get(key),str) or len(check[key])>8192 for key in ['id','title','impact','help']):
            raise ValueError('Metadados da verificação inválidos.')
        criteria=check.get('criteria');examples=check.get('examples')
        if not isinstance(criteria,list) or len(criteria)>30 or any(not isinstance(c,str) or len(c)>64 for c in criteria):
            raise ValueError('Referências da verificação inválidas.')
        if not isinstance(examples,list) or len(examples)>5:
            raise ValueError('Amostras da verificação inválidas.')
        for example in examples:
            if not isinstance(example,dict) or any(not isinstance(example.get(key),str) or len(example[key])>limit for key,limit in [('selector',1000),('html',400),('summary',1500)]):
                raise ValueError('Evidência inválida.')
    if not isinstance(result.get('title'),str) or not isinstance(result.get('limitations'),list) or any(not isinstance(v,str) for v in result['limitations']):
        raise ValueError('Metadados do snapshot inválidos.')

    if 'visual' in result:
        visual=result['visual']
        if not isinstance(visual,list) or len(visual)!=2:
            raise ValueError('Capturas visuais inválidas.')
        for capture in visual:
            if not isinstance(capture,dict) or capture.get('name') not in {'desktop','mobile'} or not isinstance(capture.get('checks'),list) or len(capture['checks'])>4:
                raise ValueError('Medições visuais inválidas.')
            if 'accessibilityChecks' in capture:
                validate_analysis({'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','title':'viewport','limitations':[],'checks':capture['accessibilityChecks']})
            viewport=capture.get('viewport')
            if not isinstance(viewport,dict) or any(type(viewport.get(k)) is not int or not 1<=viewport[k]<=2000 for k in ['width','height']):
                raise ValueError('Viewport inválido.')
            for check in capture['checks']:
                if not isinstance(check,dict) or check.get('status') not in {'clear','review'} or type(check.get('count')) is not int or check['count']<0 or any(not isinstance(check.get(k),str) or len(check[k])>4000 for k in ['id','title','criterion','help']) or not isinstance(check.get('examples'),list) or len(check['examples'])>5:
                    raise ValueError('Apontamento visual inválido.')
            for check in capture['checks']:
                for example in check['examples']:
                    if not isinstance(example,dict) or not isinstance(example.get('selector'),str) or len(example['selector'])>1000 or not isinstance(example.get('rect'),dict) or any(type(example['rect'].get(key)) not in (int,float) or not math.isfinite(example['rect'][key]) for key in ['x','y','width','height']):
                        raise ValueError('Geometria de evidência inválida.')
            image=capture.get('screenshot')
            if image is not None:
                if not isinstance(image,dict) or image.get('mime')!='image/jpeg' or not isinstance(image.get('dataBase64'),str) or len(image['dataBase64'])>293336:
                    raise ValueError('Imagem inválida.')
                try:decoded=base64.b64decode(image['dataBase64'],validate=True)
                except (ValueError,binascii.Error) as error:raise ValueError('Imagem inválida.') from error
                if len(decoded)>220000 or not decoded.startswith(b'\xff\xd8\xff'):
                    raise ValueError('Imagem não é JPEG.')


def analyze_page(body,stylesheets=None):
    # Trusted internal service URL, never supplied by the visitor.
    endpoint=os.environ.get('BROWSER_SERVICE_URL','http://browser:9000/analyze')
    request=Request(endpoint,data=json.dumps({'html':body.decode('utf-8',errors='replace'),'stylesheets':stylesheets or []},ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urlopen(request,timeout=45) as response:
        raw=response.read(MAX_REPORT_BYTES+1)
    if len(raw)>MAX_REPORT_BYTES:
        raise ValueError('Resposta do analisador excedeu o limite.')
    result=json.loads(raw)
    validate_analysis(result)
    return result


def collect_and_analyze(url):
    # Single page first: avoids multiplying browser cost and lease duration.
    pages=crawl(url,max_pages=1,max_depth=0,timeout=30)
    reports=[]
    for page in pages:
        css,coverage=collect_stylesheets(page.body,page.final_url)
        result=analyze_page(page.body,css)
        result['styleCoverage']=coverage
        reports.append({'url':page.final_url,'htmlSha256':hashlib.sha256(page.body).hexdigest(),**result})
    return {'schemaVersion':1,'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','pages':reports,'coverage':{'pageLimit':1,'externalResources':True,'resourcePolicy':'bounded-same-host-css-only','pageScripts':False,'completeWcagAudit':False}}


if __name__ == '__main__':
    url=json.loads(sys.stdin.buffer.read(8192))['url']
    result=collect_and_analyze(url)
    raw=json.dumps(result,ensure_ascii=False).encode()
    if len(raw)>MAX_REPORT_BYTES:
        raise ValueError('Relatório excedeu o limite.')
    sys.stdout.buffer.write(raw)
