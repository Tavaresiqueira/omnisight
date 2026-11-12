# OmniSight no Railway

Serviços do monorepo com Django/DRF, PostgreSQL, fila, Chromium/axe-core e frontend
Next exportado. O gateway recebe HTTPS pelo Railway e mantém `/api` na mesma
origem do frontend. Sem migração para outro banco ou substituição por análise HTML
simplificada. O scanner desta revisão ainda usa snapshot isolado; navegação remota
com scripts, imagens/fontes e contraste é uma entrega separada, ainda necessária.

## Ordem e configuração

Conectar apenas o repositório `Tavaresiqueira/omnisight`. Manter a raiz do monorepo
como build context e apontar cada serviço para seu Config File Path abaixo.
O Railway não executa nosso Compose nem aplica seu perfil seccomp automaticamente.

| Serviço | Config File Path | Porta | Visibilidade |
| --- | --- | --- | --- |
| PostgreSQL | PostgreSQL gerenciado pelo Railway | padrão do serviço | privada |
| browser | `/deploy/railway/browser.railway.json` | 9000 | privada |
| api | `/deploy/railway/api.railway.json` | 8000 | privada |
| worker | `/deploy/railway/worker.railway.json` | nenhuma | privada |
| retention | `/deploy/railway/retention.railway.json` | nenhuma | privada |
| web | `/deploy/railway/web.railway.json` | 8080 | domínio HTTPS público |

Criar e validar browser e banco primeiro. Depois api, worker/retention e web.
Uma réplica por serviço inicialmente. Recursos limitados no painel; conferir o
consumo do trial, que não garante um mês completo de execução deste conjunto.
Não habilitar upgrade pago sem autorização do titular.

## Variables

API, worker e retention:

- `DATABASE_URL`: referência à URL **privada** do PostgreSQL do projeto.
- `DJANGO_DEBUG=false`.
- `DJANGO_SECRET_KEY`: segredo aleatório com pelo menos 50 caracteres, estável.
- `DJANGO_ALLOWED_HOSTS`: domínio público de web, `localhost`, `127.0.0.1` e hostname privado da API.
- `CORS_ALLOWED_ORIGINS`: origem HTTPS pública de web.
- `DEMO_LOGIN_ENABLED=false`.
- `TRUST_PROXY_CLIENT_IP=true`: a API é privada e recebe o header exclusivamente pelo gateway.
- `SCAN_RETENTION_DAYS=30` e `ABUSE_RETENTION_DAYS=7`.

Somente API:

- `PORT=8000`.
- `DELETION_LEDGER_PATH=/data/privacy-ledger/deletions.jsonl`.
- `DELETION_LEDGER_KEY`: segredo independente de pelo menos 32 caracteres.
- Anexar volume persistente em `/data`. O Railway fornece `RAILWAY_VOLUME_MOUNT_PATH`.

O entrypoint inicializa a propriedade do diretório do journal, aplica migrações
e executa Gunicorn como UID 10001. Recusa iniciar sem o volume. O API não deve
receber domínio público próprio. Atribuir um domínio somente a web.

Somente worker:

- `BROWSER_SERVICE_URL=http://browser.railway.internal:9000/analyze`.

Somente browser:

- `PORT=9000`, `BROWSER_LISTEN_HOST=::`, `BROWSER_STARTUP_CHECK=true`.
- Não configurar credenciais de banco, cloud ou aplicação nesse serviço.

Antes de ouvir a porta/health, o browser executa uma análise real com o sandbox
Chromium habilitado. Uma falha impede o deploy saudável. Não remover o sandbox
para obter um health verde. O bind IPv6 atende a rede privada do Railway.

Somente web:

- `PORT=8080`, `API_UPSTREAM=api.railway.internal:8000`.

Não colocar secrets em Git, Dockerfiles ou arquivos JSON. Os arquivos de config
selecionam build/start/health; os valores ficam no painel/variables do Railway.

## Gates de liberação

1. Startup do Chromium aprovado no próprio Railway.
2. Migrações, health de API e gateway aprovados.
3. Cadastro/login reais, scan queued → completed, relatório, screenshots desktop/móvel,
   isolamento de organizações e exclusão testados pelo domínio público.
4. Registrar URL final e hash do HTML de PUC e de outra página distinta; conferir
   relatórios diferentes quando os documentos forem diferentes.
5. Verificar journal após redeploy e configurar cópia externa/backup conforme
   `docs/operations/ci-cd.md`. Um volume local sozinho não cobre perda do ambiente.
6. Rever identificação de IP atrás do proxy: `remote_host` é o peer do gateway,
   que pode ser o edge Railway. Não confiar em X-Forwarded-For arbitrário. Limites
   persistentes por usuário, organização, domínio e capacidade continuam ativos.

Configuração local e testes unitários não comprovam execução remota. Registrar o
resultado real destes gates antes de declarar o deploy operacional.
