# Limites de abuso

## Política inicial

| Operação / escopo | Limite |
| --- | --- |
| API, por IP | 120 requisições/minuto |
| Login e demo, por IP e operação | 10 tentativas/minuto |
| Cadastro de conta, por IP | 5 tentativas/hora |
| Cadastro de site, por usuário | 20 tentativas/hora |
| Novos scans e retries, por usuário | 10/hora |
| Novos scans e retries, por organização | 30/hora |
| Novos scans e retries, por hostname de destino | 5/hora, compartilhados entre organizações e caminhos |
| Novos scans e retries, por IP | 30/hora |
| Scans na fila ou executando | 3 por organização; 10 no total |

São janelas fixas iniciadas no primeiro acesso. Podem ocorrer rajadas na virada da janela; os limites de capacidade continuam ativos. Hostname não agrega todos os subdomínios de um domínio registrável. Esses valores são conservadores para o MVP e precisam ser calibrados com teste de carga.

`identity.abuse` usa linhas únicas com bloqueios transacionais PostgreSQL. A admissão usa um mutex persistente global para conferir capacidade e debitar todos os escopos na mesma transação da criação/retry. Recusa não cria trabalho nem debita parcialmente outras cotas. Repetir uma chave de idempotência existente não debita cota de scans, mas continua sujeito ao limite HTTP. Cancelar não devolve cotas horárias; libera a capacidade pendente. Recuperação de leases pelo worker é a continuação de um trabalho já admitido, limitada às três tentativas existentes.

O SQLite serve ao desenvolvimento sequencial; a garantia concorrente deve ser validada pelo teste PostgreSQL no CI. Há um teste concorrente de admissão e testes de 429, reset de janela, idempotência, retry e isolamento entre organizações.

## Identidade e fronteira de rede

Sem proxy confiável, o IP vem de `REMOTE_ADDR`. `X-Forwarded-For` não é usado. Em Compose, somente Caddy publica portas; ele sobrescreve `X-OmniSight-Client-IP` e a API confia nesse cabeçalho com `TRUST_PROXY_CLIENT_IP=true`. Não publicar a API diretamente com essa opção ativa. Atrás de outro proxy/CDN, adaptar e testar a cadeia de confiança antes de ativar; caso contrário os clientes podem compartilhar a cota do proxy. Identidades dos contadores são HMAC-SHA256 com o segredo da aplicação; logs e métricas não expõem IP, URL, e-mail ou digest.

O serviço browser continua privado. Estes limites são proteção de aplicação/custo, não proteção volumétrica DDoS. Requisições recusadas por autenticação/permissão podem terminar antes do throttle DRF. Proteção de tráfego, tamanho de corpo e conexões no gateway deve ser avaliada antes de acesso público amplo.

## Operação e alertas

As recusas retornam HTTP 429, código `RATE_LIMITED` e `Retry-After` em segundos. Capacidade usa espera indicativa de 30 segundos; não promete vaga após esse prazo. Tentativas inválidas de login e cadastro também consomem cota, antes da validação do corpo.

Cada recusa gera evento WARNING `rate_limit_exceeded scope=... retry_after=...`, sem dados da página. `python manage.py abuse_metrics --alert-threshold 5` produz JSON agregado das janelas ativas e retorna código de erro com `ABUSE_ALERT` quando qualquer escopo tiver ao menos cinco recusas. O comando é operacional, não uma rota pública. Executar periodicamente pelo monitor e alertar no código de saída; para alertas de curta duração, contar os eventos WARNING (por exemplo, cinco eventos em cinco minutos). O monitor/notificador ainda não está provisionado: não existe alerta enviado automaticamente nesta entrega.

Os contadores reutilizam a mesma linha por escopo/identidade e reiniciam contagem na expiração, sem histórico de eventos. O serviço retention remove identidades sete dias após expirar a última janela, conforme docs/privacy-data-lifecycle.md. Não remover o mutex `scan_capacity` enquanto APIs estiverem em operação. Alterar `SECRET_KEY` reinicia identidades das cotas; tratar como operação controlada.
