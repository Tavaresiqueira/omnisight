# Evidências do pipeline - 11/11/2026

## Implementado

- Consumer real de fila persistida: CAS, lease UUID, recuperação após expiração,
  teto de três tentativas e fencing de publicação.
- Cancel/retry/read/list/report com isolamento por organização; viewer não inicia
  nem cancela execuções. Snapshot publicado uma única vez na mesma transação que
  conclui o scan. A classe de modelo rejeita atualização pelo caminho save.
- Coleta pelo crawler SSRF existente, uma página; pipeline de coleta/análise em
  subprocess de 90 s (inclui DNS), sem secrets de DB/AWS no ambiente do filho.
- Serviço separado de navegador com Playwright 1.62.0 e axe-core 4.13.0 vendorizado.
  Snapshot offline + CSP: scripts do site e recursos externos bloqueados.
- UI para solicitar, acompanhar, cancelar, repetir e ver resultado salvo; sem
  porcentagem de progresso fictícia, sem sequestrar foco ao atualizar status.
- Build estático para frontend; Compose e CloudFormation para piloto AWS.

## Evidências locais

Executar:
```
python apps/api/manage.py test identity.tests -v 1
python apps/api/manage.py makemigrations --check --dry-run
python -m unittest discover -s apps/browser/tests -v
npm run test:web
NEXT_PUBLIC_API_URL=/api npm run build --workspace @omnisight/web -- --webpack
```

O teste PostgreSQL de dois consumers concorrentes não é executado sobre SQLite.
Os dois testes de Chromium requerem `RUN_BROWSER_TESTS=1`: não os contar como
aprovados quando estiverem skipped. Uma tentativa real de Chromium falhou neste
host com `socket() failed: Operation not permitted`; não foi desativado sandbox
no código. Docker e AWS CLI não estão disponíveis aqui.

O CI preparado executa PostgreSQL, Chromium sandbox, build Compose, healthcheck e
fixtures dentro do container de browser. Não foi disparado um workflow remoto.
Ficam pendentes E2E com API/worker/DB/serviço real no mesmo fluxo, acessibilidade
manual, carga/custo, operação de backup/restore e rate limit/abuso.

## Relação com o backlog

- 86e2v67wq - fila: implementação ampliada; concorrência PostgreSQL no CI pendente.
- 86e2v68ee - isolamento: configuração e fixtures; host Docker real pendente.
- 86e2v68h2 - engine: adaptador e versão; fixtures de Chromium pendentes.
- 86e2v6cww - snapshots: publicação atômica/read-only na aplicação e testes locais.
- 86e2v6amg - estados no frontend: testes de componentes; E2E pendente.
- 86e2v6fgh - infraestrutura: template piloto e Compose; provisionamento pendente.

Nada disso implica validação de conformidade completa WCAG ou rollout em produção.
