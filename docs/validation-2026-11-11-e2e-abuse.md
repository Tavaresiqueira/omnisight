# Validação — E2E e limites de abuso

## Implementado

- Jornada automatizada de cadastro, logout/login, site, fila, análise real axe, snapshot persistido, recarregamento e isolamento entre organizações. Fixture substitui somente coleta externa; consumo chama pipeline em processo para permitir fixture determinística. Job dedicado, screenshots e trace no CI.
- Contadores no banco por usuário, organização, hostname e IP; limites de login/cadastro e HTTP; admissão atômica de novos scans/retries e capacidade global/por organização.
- HTTP 429 com Retry-After; replay idempotente sem débito de scan; métricas sem identificadores e comando com código de saída para monitoramento.
- UI apresenta mensagem em português em vez do código RATE_LIMITED. Os dois testes dessa regressão falharam antes da correção e passaram depois.

## Evidência local

| Verificação | Resultado |
| --- | --- |
| Django: identity.tests + identity.e2e | 80 descobertos, 76 passaram, 4 pulados |
| Frontend Vitest | 17 passaram |
| Build Next e TypeScript | Passou, exportação estática |
| Migrações | Sem alterações faltantes após gerar 0005 |
| YAML: CI, Compose e contrato runtime | Sintaxe válida |
| Diff | Sem erros de whitespace |

Os quatro testes pulados são: concorrência da fila preexistente, dois testes novos de admissão concorrente (todos exigem PostgreSQL) e a jornada E2E. Também houve tentativa explícita de E2E com RUN_E2E_TESTS=1 e Chromium do sistema: falhou antes da jornada com `socket() failed: Operation not permitted`. Não se trata de evidência de aprovação da aplicação. Sandbox permaneceu ativo.

## Gates abertos

1. Executar jobs api/e2e/compose em host com PostgreSQL, Docker e Chromium com sandbox e obter pipeline verde. Nenhum pipeline remoto foi executado nesta entrega.
2. Implementar comparação de scans para completar o aceite original da tarefa E2E; a funcionalidade ainda não existe.
3. Conectar os eventos/métricas ao monitor/notificador do ambiente. O comando de alerta existe, mas notificações automáticas não estão provisionadas.
4. Validar proxy/IP com Caddy e medir carga/custo antes de calibrar limites em produção. YAML válido não comprova inicialização dos containers.
5. Definir retenção/limpeza dos contadores pseudonimizados na tarefa de privacidade.

As duas tarefas ficam em andamento até a evidência operacional correspondente. Aplicar a migração 0005 antes de iniciar a API atualizada. Nenhum deploy ou push remoto realizado.
