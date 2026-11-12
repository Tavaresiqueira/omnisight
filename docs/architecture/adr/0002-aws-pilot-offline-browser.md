# ADR 0002 - Piloto AWS, fila durável e navegador offline

Data: 2026-11-11. Estado: implementação preparada, validação de infraestrutura pendente.

## Contexto e decisão

Retomar o monorepo Django REST + Next.js. Uma VM Lightsail com Docker Compose é
o alvo inicial de baixo custo. PostgreSQL atende autenticação, organizações,
sites, fila e snapshots. O frontend é exportado estaticamente; Caddy fornece
HTTPS e encaminha /api ao Django. A VM é um piloto de nó único, sem alta disponibilidade.
Cloudflare Workers/D1 exigiria adaptar o backend e não é o alvo desta entrega.

## Execução

1. A API autentica a organização e cria scan idempotente.
2. Um consumer com concorrência 1 assume o scan por CAS e recebe um UUID de lease.
3. O crawler SSRF-safe busca uma página HTTPS; nenhuma busca remota ocorre na API
   de resultados. O cadastro ainda valida DNS no processo da API.
4. O worker envia somente HTML ao serviço de navegador em rede Docker interna.
5. O navegador executa axe-core 4.13.0 sobre snapshot offline, sem scripts do
   alvo, CSS externo, imagens, frames, downloads ou acesso à rede pelo documento.
6. Resultado até 1 MiB é publicado atomicamente com a conclusão do scan.
7. Sem lease válida, o worker não pode publicar. Lease expira em 180 s; jobs
   abandonados são retomados, até três tentativas. Erros de execução são falhas
   explícitas; retry pelo usuário também respeita o limite.

O banco funciona como fila durável de baixo volume: nenhum broker adicional.
O consumer verifica a fila a cada 2 s. Falhas do DB interrompem o processo e o
restart do container o retoma. Não há promessa de entrega exatamente uma vez:
o processamento pode repetir, mas a publicação de snapshot é única e cercada
pela lease. Terminal completed equivale ao succeeded do backlog.

## Fronteiras e limites

- A API e o consumer têm acesso ao banco, nesta implantação reduzida. Isso é uma
  exceção explícita ao canal autenticado de menor privilégio previsto no ADR 0001;
  separar credenciais/permissões do consumer é um gate para ambiente de maior risco.
- O serviço de browser recebe zero secrets de DB/AWS. Não publica portas. Sua rede
  é internal e não é a rede do DB. O documento é servido em origem sintética, com
  CSP restritiva e abort de toda requisição não sintética.
- Chromium sandbox permanece obrigatório. O container usa pwuser não root,
  perfil seccomp do Playwright v1.62.0, sem capabilities, memória 768 MiB, 1 CPU,
  256 PIDs, /tmp efêmero. Nunca contornar falha de sandbox com --no-sandbox.
- Browser subprocess tem 40 s; serviço 45 s no cliente; crawl até 30 s. O pipeline
   inteiro roda em subprocess separado com limite de 90 s, inclusive DNS. Lease de
  180 s cobre esse fluxo de uma página. Full-site crawling não foi ativado.
- Nem HTML completo nem mensagens brutas de erro são persistidos. Evidências
  limitadas podem conter informações do alvo e exigem política de retenção.
- Snapshot não é auditoria completa: sem estilos externos, contraste fica
  desabilitado, sem classificação de aprovação. Interação, teclado, zoom,
  alvos e comportamento dinâmico continuam pendentes na página real.

## Validação e rollout

Testes locais: API/worker, publicação, fronteira do serviço, frontend e build.
CI preparado para PostgreSQL, Chromium com sandbox e build/smoke Compose.
Esses jobs só são evidência após execução bem-sucedida no ambiente de CI.
Não houve criação de recursos AWS, build de imagem ou implantação neste ambiente.
Antes de ativar produção: executar os gates, revisar conta/créditos, domínio,
backups/restore, limites de concorrência/abuso e isolamento no host real.
