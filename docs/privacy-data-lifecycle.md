# Ciclo de vida dos dados — política técnica do MVP

## Inventário e finalidade

| Dados | Finalidade | Retenção e descarte | Exportação / acesso |
| --- | --- | --- | --- |
| E-mail, nome, tipo de conta e hash de senha | Autenticar e identificar o perfil | Até encerramento autenticado por senha e confirmação; detalhes em docs/account-closure-and-recovery.md | Dados básicos em /api/auth/me/; hash e token nunca fazem parte do relatório |
| Token de autenticação | Autorizar a sessão da API | Até revogação administrativa/encerramento; sair da UI limpa apenas sessionStorage, não revoga o token no servidor | Não exportar como dado do diagnóstico |
| Organização, associação e papel | Isolamento e autorização | Até encerramento explícito do espaço pelo owner, ou encerramento da conta quando for seu único membro e proprietário | /api/auth/me/ e detalhe autorizado da organização |
| Nome e URL normalizada do site | Cadastrar o alvo e iniciar avaliações | Até encerramento do espaço; excluir um scan não remove o cadastro do site | Listagem autenticada de sites |
| Estado, timestamps, correlação e chave de idempotência do scan | Acompanhar trabalho e evitar duplicação | 30 dias após encerramento, por padrão; fallback para data de solicitação em registros legados sem data de encerramento; proprietário pode excluir imediatamente | Lista/detalhe do scan na própria organização |
| Título, URL da página, hash HTML, regras e amostras de seletores/HTML | Explicar e reproduzir barreiras detectadas | Cascata com o scan; amostras limitadas, mas podem conter dados pessoais | Relatório autenticado e download JSON pelo usuário autorizado |
| Capturas JPEG desktop/móvel | Evidência visual limitada ao viewport do snapshot | Cascata com o scan; não há arquivo paralelo no servidor | Incluídas no relatório JSON; cópia baixada fica sob controle de quem exportou |
| HTML completo e folhas CSS coletados | Análise transitória | Não persistidos pelo pipeline: buffers e subprocessos limitados encerram ao fim/timeout; amostras e capturas seguem a política acima | Não há exportação do código completo original |
| HMAC de usuário, organização, hostname e IP + contadores de abuso | Limitar custo e proteger capacidade | Mesma linha reutilizada; exclusão sete dias após expirar a última janela; o mutex global scan_capacity é preservado sem conter PII | Somente métricas agregadas operacionais; sem chaves nos logs/JSON |
| Logs de scan, bloqueio e descarte | Diagnosticar falhas e abuso | Rotação Compose de até 3 arquivos de 10 MB por serviço; não é prazo em dias; configurar prazo no coletor central quando existir | Operador; eventos da aplicação sem URL/HTML/e-mail/IP; correlações podem ser vinculáveis |
| JSON importado da extensão | Visualizar diagnóstico local | Só memória da tela nesta versão; limpar/recarregar remove; arquivo original permanece no dispositivo | Não é enviado à API nem incluído no descarte do servidor |

Os padrões de 30 e sete dias são escolhas iniciais do MVP, configuráveis por `SCAN_RETENTION_DAYS` (1–3650) e `ABUSE_RETENTION_DAYS` (1–365). Não representam prazos legais obrigatórios. Cookies/sessões/tokens da página avaliada não são coletados; scripts da página não executam no modo snapshot. O conteúdo público pode conter dados pessoais: isso também vale para títulos, paths/query strings, seletores, trechos HTML e screenshots. Evitar páginas com dados pessoais desnecessários e não fornecer URLs com segredos. O sistema não alega anonimização dos relatórios.

## Controles implementados

- `DELETE /api/scans/{id}/`: só owner da organização; membro/viewer recebe 403 e outra organização recebe 404. Transação bloqueia a linha antes da exclusão em cascata. A checagem existente de lease/status impede que uma execução atrasada recrie relatório. A coleta já em execução pode continuar em memória até seu prazo de 90 segundos; a exclusão não envia sinal ao processo remoto.
- Confirmação explícita na interface; exclusão não remove o site nem revoga cotas horárias. A chave de idempotência do scan também é descartada: reutilizá-la depois da exclusão pode criar um novo scan, sujeito às cotas.
- `Cache-Control: no-store, private` nas respostas /api, exceto health, reduz armazenamento HTTP de sessões e relatórios. Isso não apaga capturas/cópias já salvas ou dados em uma aba aberta de outro usuário. Não há push de invalidação das abas.
- Download JSON por quem já possui permissão de leitura. Não inclui senha/hash/token da conta. O diagnóstico pode conter evidências pessoais da página; o arquivo exportado não deve ser publicado automaticamente.
- Serviço `retention` no Compose, separado do consumidor de scans e sem rede externa: a cada minuto exclui até 100 scans encerrados e 100 identidades expiradas. Pula linhas bloqueadas por execução concorrente. A exclusão é eventual; indisponibilidade, bloqueios e backlog podem atrasar a aplicação do prazo. Monitorar a execução e elegíveis pendentes.
- Sem IDs de scan no evento de descarte: `retention_sweep scans_deleted=N buckets_deleted=N`. O job não cria um novo histórico contendo dados removidos.

## Operação

Simular: `python manage.py purge_expired_data`. Saída inclui `dryRun: true` e totais elegíveis, sem conteúdo. Executar lote: `python manage.py purge_expired_data --apply --batch-size 100`. Validar serviço: `python manage.py run_retention_worker --once`. Em Compose o loop já está definido, mas a execução real em Docker ainda precisa ser comprovada no CI/ambiente de deploy. Reduzir o prazo configurado torna dados antigos elegíveis no próximo lote; revisar impacto antes de alterar um ambiente com dados reais.

## Limites e pendências de aceite

Há encerramento autenticado de conta/espaço e exportação cadastral com associações; relatórios são exportados separadamente. Contas demo compartilhadas não podem ser encerradas no painel. O detalhe de autorização, preservação de outros proprietários e registro externo de intenções está em docs/account-closure-and-recovery.md.

Backups, snapshots de disco, arquivos exportados e logs centralizados não são apagados por este job. A tarefa de backup deve definir prazo de expiração e um procedimento que reaplique solicitações de exclusão antes de servir uma restauração; o descarte por idade sozinho não resolve scans recentes excluídos manualmente e restaurados de backup. O registro assinado de intenções e a reaplicação foram implementados, com teste de restauração preparado no CI; cópia externa atual e execução real do restore continuam pendentes. Esta limitação precisa constar da política final publicada.

Também permanecem: comunicação da política completa ao usuário, revisão de finalidade/base aplicável, canal de solicitações, validação operacional do job, testes concorrentes PostgreSQL e revisão manual com tecnologia assistiva. Esta documentação é um inventário técnico e não uma declaração de conformidade integral.
