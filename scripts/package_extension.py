"""Build the unpackable extension and dashboard downloads using only stdlib."""
import json
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'apps/extension';VENDOR=ROOT/'apps/browser/vendor';PUBLIC=ROOT/'apps/web/public'
PUBLIC.mkdir(parents=True,exist_ok=True)
manifest=json.loads((SOURCE/'manifest.json').read_text())
assert manifest['permissions']==['activeTab','scripting']
locale=json.loads((VENDOR/'pt_BR.json').read_text())
with zipfile.ZipFile(PUBLIC/'omnisight-extension.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in sorted(SOURCE.iterdir()):
  if path.is_file() and path.name!='tests.mjs':archive.write(path,path.name)
 for name in ['axe.js','AXE-LICENSE','README.md']:archive.write(VENDOR/name,'vendor/'+name)
 # Preserve one engine instance across repeated clicks in the same isolated world.
 archive.writestr('vendor/axe.min.js','if (!globalThis.axe) {\n'+(VENDOR/'axe.min.js').read_text()+'\n}\n')
 archive.writestr('vendor/locale.js','if (!globalThis.__omnisightRunning) axe.configure({locale:'+json.dumps(locale,ensure_ascii=False)+'});\n')
(PUBLIC/'extensao-instalacao.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Instalar OmniSight</title><body style="font:16px/1.8 system-ui;max-width:760px;margin:40px auto;padding:20px;background:#f3f5f8;color:#101625"><h1>Extensão OmniSight experimental</h1><p>Para Chrome ou Edge de computador. Não é uma publicação na loja e não funciona no Chrome do iPhone.</p><ol><li>Baixe e extraia <a href="/omnisight-extension.zip">o ZIP da extensão</a>.</li><li>Abra chrome://extensions ou edge://extensions.</li><li>Ative Modo do desenvolvedor e selecione Carregar sem compactação.</li><li>Escolha a pasta extraída que contém manifest.json.</li><li>Abra seu site, entre normalmente e clique no ícone OmniSight.</li><li>Baixe o JSON e importe no dashboard.</li></ol><p>A análise usa o estado atual da aba, sem navegar automaticamente para outras rotas. Não há envio automático de dados ao servidor. Evidências HTML são opcionais e podem conter dados pessoais.</p><p>Versão experimental: instalação e análise real em Chrome/Edge ainda precisam de validação. Resultados automáticos não certificam conformidade WCAG.</p></body></html>''')
print(PUBLIC/'omnisight-extension.zip')
