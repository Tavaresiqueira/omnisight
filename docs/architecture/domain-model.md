# Modelo de domínio e dados do MVP

**Status:** Aprovado para orientar a implementação

**Data:** 2026-09-16

**Rastreabilidade:** ClickUp `86e2v67hk`; RF-001 a RF-010; RF-015; RF-021; RF-022; RNF-MAN-001 e RNF-MAN-003

## Escopo

Este modelo define os dados mínimos para organizar usuários, sites e scans sem
antecipar banco, ORM ou provedor. O identificador de organização vem sempre da
autorização no servidor, nunca de um campo controlado pelo cliente.

## Entidades e relações

| Entidade | Campos essenciais | Regras de domínio |
| --- | --- | --- |
| Organização | `id`, `nome`, `criada_em` | Limite de propriedade e isolamento de todos os dados do produto. |
| Usuário | `id`, `email`, `criado_em`, `desativado_em` | Identidade única; não possui acesso a uma organização sem associação ativa. |
| Associação | `organizacao_id`, `usuario_id`, `papel`, `criada_em` | Chave única por organização e usuário. Papéis iniciais: `owner`, `member` e `viewer`. |
| Site | `id`, `organizacao_id`, `url_normalizada`, `nome_exibicao`, `criado_em`, `excluido_em` | URL normalizada é única por organização enquanto o site estiver ativo. Só aceita HTTPS. |
| Scan | `id`, `organizacao_id`, `site_id`, `estado`, `chave_idempotencia`, `solicitado_em`, `iniciado_em`, `concluido_em`, `falha_codigo` | Representa uma solicitação imutável de análise com transições de estado controladas. |
| Snapshot | `id`, `scan_id`, `score_geral`, `versao_formula`, `versao_engine`, `versao_regras`, `criado_em` | Resultado agregado único por scan concluído. |
| Achado | `id`, `snapshot_id`, `regra_codigo`, `regra_versao`, `criterio_wcag`, `tipo_validacao`, `severidade`, `confianca`, `estado_resolucao` | Preserva regra e versão usadas, sem inferir conformidade integral. |
| Evento de auditoria | `id`, `organizacao_id`, `ator_usuario_id`, `tipo`, `resultado`, `correlacao_id`, `ocorrido_em` | Registra ação relevante com dados mínimos e sem segredos ou conteúdo de página. |

O [diagrama de classes](uml/class-diagram.puml) continua sendo a visão conceitual
das relações. Este documento acrescenta chaves, invariantes e limites para a
persistência relacional.

## Chaves e índices obrigatórios

| Tabela | Chave ou índice | Motivo |
| --- | --- | --- |
| associações | único em `(organizacao_id, usuario_id)` | Evita associação duplicada. |
| sites | único em `(organizacao_id, url_normalizada)` com `excluido_em` nulo | Evita cadastro duplicado e preserva histórico de exclusão. |
| scans | único em `(organizacao_id, chave_idempotencia)` quando a chave existir | Repetições do cliente não criam scans duplicados. |
| scans | índice em `(organizacao_id, site_id, solicitado_em desc)` | Suporta histórico autorizado e paginação. |
| snapshots | único em `scan_id` | Um resultado agregado por execução. |
| achados | índice em `(snapshot_id, severidade, estado_resolucao)` | Suporta filtros de relatório. |
| eventos_auditoria | índice em `(organizacao_id, ocorrido_em desc)` | Suporta auditoria por organização. |

Toda consulta que alcance `Site`, `Scan`, `Snapshot`, `Achado` ou `Evento de
auditoria` deve começar pelo escopo da organização autorizada. A relação indireta
por `site_id` ou `scan_id` não substitui esse filtro.

## Estados de scan

| Estado | Pode seguir para | Observação |
| --- | --- | --- |
| `queued` | `running`, `cancelled`, `expired` | Trabalho aceito, ainda não executado pelo worker. |
| `running` | `completed`, `failed`, `cancelled`, `expired` | Worker assumiu a execução. |
| `completed` | nenhum | Possui snapshot e achados versionados. |
| `failed` | nenhum | Preserva código de falha seguro e acionável. |
| `cancelled` | nenhum | Cancelamento solicitado antes do resultado final. |
| `expired` | nenhum | Trabalho excedeu prazo de execução ou permanência na fila. |

Estados finais não podem ser reabertos. Uma nova tentativa cria outro scan e
preserva a evidência da execução anterior. O worker deve aplicar a transição de
forma idempotente e registrar o mesmo `correlacao_id` em logs e auditoria.

## Dados de scan e evidências

O scan guarda a URL normalizada, viewport, parâmetros permitidos e versões da
engine, regras e fórmula. Capturas, HTML bruto e recursos de página não são dados
obrigatórios do modelo transacional. Se uma evidência grande for necessária, ela
fica em armazenamento separado, por referência opaca, com expiração e autorização
equivalentes às do scan.

Cookies, tokens, credenciais, conteúdo de formulário e dados pessoais não devem
ser persistidos como evidência padrão. O desenho atende à minimização de dados e à
reprodutibilidade exigida pelo produto sem transformar o scanner em arquivo de
conteúdo de terceiros.

## Exclusão

A exclusão lógica de um site bloqueia novas solicitações e remove o site das
consultas comuns. A exclusão física de scans, snapshots, achados e evidências segue
a política de retenção e mantém apenas o evento mínimo de auditoria justificado.
O modelo não permite exclusão fora da organização autorizada.

## Limites de implementação

Migrations devem implementar estas chaves e índices antes dos endpoints. A escolha
de banco, ORM, fila e storage será registrada em ADR específico antes de adicionar
dependências de runtime.
