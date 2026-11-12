# Caminho crítico automatizado

O job `e2e` compila o Next, usa PostgreSQL isolado por execução e inicia o serviço real Playwright/axe. O teste abre a UI, cadastra um desenvolvedor, sai, faz login, cadastra um site, solicita um scan, consome a fila, verifica a regra `image-alt`, abre o relatório, recarrega a página e verifica isolamento entre organizações e a exclusão confirmada pelo proprietário. Screenshots e trace ficam no artefato `critical-journey-evidence`, por sete dias, inclusive em falhas.

A única substituição externa é DNS/coleta HTTP do site de teste por HTML fixo. O consumidor chama o pipeline em processo para essa substituição; o serviço do navegador mantém seu subprocesso real. API, ORM, fila, publicação, axe e interface não usam respostas simuladas. O subprocesso externo do coletor e o isolamento Docker são cobertos separadamente pelos testes existentes e pelo job `compose`.

Execução: instalar requirements da API e do browser, instalar Chromium com `python -m playwright install --with-deps chromium`, compilar web com `NEXT_PUBLIC_API_URL=/api`, iniciar `python apps/browser/server.py` e executar `RUN_E2E_TESTS=1 BROWSER_SERVICE_URL=http://127.0.0.1:9000/analyze python apps/api/manage.py test identity.e2e -v 2`, com `DATABASE_URL` apontando para PostgreSQL descartável.

## Evidência ainda necessária

O ambiente local bloqueia a criação de sockets pelo Chromium. O teste não é considerado aprovado sem execução real do job. Não desativar o sandbox para obter um resultado verde. Comparação entre scans ainda não foi implementada; portanto o aceite original da tarefa E2E, que inclui comparação e pipeline verde, permanece aberto. Instalação real da extensão e avaliação manual assistiva continuam fora deste teste.

Traces contêm apenas contas e dados sintéticos de teste; nunca executar este fluxo com contas reais de produção.
