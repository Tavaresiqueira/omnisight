# Validação de encerramento e recuperação — 11/11/2026

Branch: feature/reliable-scans-aws. Commits principais: b3763ba (backend e registro), 3d56e3a (painel), 1d40bfc (backup/restore e CI), bc06618 (política), 66653f8 (assinaturas).

## Evidência local

| Verificação | Resultado |
| --- | --- |
| API identity.tests | 102 descobertos; 97 passaram; cinco testes PostgreSQL pulados |
| Frontend | 23 passaram |
| Build Next e TypeScript | Passou |
| Migrações | Nenhuma mudança de esquema adicional |
| Scripts bash e YAML CI/Compose/contrato | Sintaxe válida |
| Diff | Sem erros de whitespace |

Nove testes iniciais do ciclo de conta falharam antes da implementação. Os 11 testes atuais passam e cobrem senha/confirmação, permissões de owner, bloqueio de único owner com membros, preservação de coowner, cascata, exportação sem segredos, conta sem organização, indisponibilidade do registro, replay idempotente, adulteração, escrita concorrente do arquivo e rejeição de cauda incompleta. Guardas dos scripts são testados separadamente: sem --apply, nome de produção ou connection string injetada no nome são recusados; falha no dump não vira sucesso pela saída zero do processo seguinte e remove o arquivo incompleto.

## Limites de evidência e operação

- A jornada E2E com Chromium continua pendente do CI (o ambiente bloqueou sockets na etapa anterior). Não houve nova execução real bem-sucedida de navegador.
- Não há PostgreSQL/age/Docker disponíveis para comprovar backup criptografado e restauração real localmente. O job restore-drill faz esse percurso com duas bases descartáveis e registra evidência; ainda não foi executado remotamente.
- Timer/serviços, upload remoto e alertas não foram ativados. RPO de até 24h e RTO de uma hora são metas propostas, não medições ou garantias.
- Registro de exclusões precisa de chave separada de pelo menos 32 caracteres e volume persistente. Sem configuração válida a API recusa exclusões com 503. Cópia externa atual e checkpoint independente ainda precisam ser configurados; perda total do host continua um gate aberto.
- Encerramento em espaço compartilhado só se aplica com senha e confirmação do nome. Exportação da conta contém cadastro e associações; relatórios são baixados separadamente. Reset completo de senha e transferência de owner pela interface permanecem pendentes.
- Nenhum deploy, push, backup de dados reais ou encerramento de conta real foi realizado.

Política e procedimento: docs/account-closure-and-recovery.md. As tarefas de privacidade/backup permanecem em andamento para validação operacional e storage externo.
