# Solicitações de scan — primeira entrega

- `POST /api/sites/{siteId}/scans/`: exige autenticação e `Idempotency-Key` ASCII de 16–128 caracteres. Aceita somente `viewport: desktop` ou corpo vazio. Retorna 202.
- A chave é única por organização. Repeti-la para o mesmo site retorna a mesma solicitação; reutilizá-la para outro site retorna 409.
- `GET /api/scans/{scanId}/`: consulta restrita à organização autenticada.
- Estados persistidos: queued, running, completed, failed, cancelled. `completed` segue o nome do contrato OpenAPI atual, equivalente ao sucesso descrito no backlog.
- Transições usam atualização condicional para impedir duas reivindicações da mesma solicitação. Até três tentativas; somente falhas podem voltar à fila.

## Limites desta etapa

A tabela persiste a fila, mas ainda não existe consumidor, scheduler de recuperação ou motor de acessibilidade conectado. Nenhum resultado é fabricado; uma solicitação permanece queued até que um worker a processe. O worker futuro deve validar novamente o destino com a proteção SSRF no momento de cada acesso e usar isolamento de rede/processo. A recuperação de trabalhos abandonados e testes concorrentes em PostgreSQL ainda são necessários antes de fechar a tarefa de fila no ClickUp.
