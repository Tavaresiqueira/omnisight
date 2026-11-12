"""Private service: no published port, DB bindings, cloud credentials or egress."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

MAX_INPUT=4*1024*1024+65536

def execute(payload):
    if not isinstance(payload,dict) or not {'html'}<=set(payload) or set(payload)-{'html','stylesheets'} or not isinstance(payload['html'],str) or len(payload['html'].encode())>2*1024*1024:
        raise ValueError('HTML inválido.')
    styles=payload.get('stylesheets',[])
    if not isinstance(styles,list) or len(styles)>3 or any(not isinstance(css,str) or len(css.encode())>262144 for css in styles):
        raise ValueError('Folhas de estilo inválidas.')
    env={key:os.environ[key] for key in ['PATH','HOME','TMPDIR','PLAYWRIGHT_BROWSERS_PATH','CHROMIUM_EXECUTABLE'] if key in os.environ}
    process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('runner.py'))],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,env=env,start_new_session=True)
    try:
        stdout,_=process.communicate(json.dumps(payload,ensure_ascii=False).encode(),timeout=40)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.communicate()
        raise TimeoutError('Tempo limite do navegador excedido.')
    if process.returncode or len(stdout)>1024*1024:
        raise ValueError('O navegador não concluiu a análise.')
    return json.loads(stdout)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        self.send_response(200 if self.path=='/health' else 404);self.end_headers()
    def do_POST(self):
        if self.path!='/analyze':self.send_error(404);return
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=MAX_INPUT:raise ValueError('Tamanho inválido.')
            result=execute(json.loads(self.rfile.read(length)))
            body=json.dumps(result).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        except (ValueError,TimeoutError):
            self.send_error(422,'Análise indisponível')

if __name__=='__main__':HTTPServer(('0.0.0.0',9000),Handler).serve_forever()
