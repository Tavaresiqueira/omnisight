# Validação de retenção e exclusão — 11/11/2026

Branch: feature/reliable-scans-aws. Commits: eea5846 (API, limpeza e testes), a5dc7b6 (interface/exportação e jornada), cbbbb38 (inventário).

## Resultado local

- Django `identity.tests identity.e2e`: 90 descobertos, 84 aprovados e seis pulados. Cinco exigem PostgreSQL (fila, admissão e descarte concorrentes); um exige a jornada com navegador real. O impedimento de Chromium observado na etapa anterior permanece; não houve nova execução bem-sucedida de browser/CI.
- Vitest: 20 aprovados.
- Build Next/TypeScript: aprovado.
- Migrações: nenhuma mudança de esquema adicional necessária.
- YAML Compose/contrato runtime e diff: válidos.

Os oito testes de privacidade falharam antes da implementação e passaram depois. Cobrem exclusão em cascata, permissão de owner, isolamento entre organizações, tentativa tardia de publicação, retenção de terminais, preservação de ativos/mutex, lote limitado, simulação antes de aplicar e cache HTTP. A confirmação da UI também falhou antes da implementação; agora há testes para confirmação, ocultação por papel e exportação autenticada com liberação do objeto temporário.

## Operação e pendências

O Compose inclui o serviço retention, sem saída para a Internet, com lotes limitados a cada minuto. A inicialização real do serviço em Docker ainda não foi validada. E2E inclui exclusão pela interface, mas permanece pendente de execução no CI. Não houve deploy, push remoto ou remoção de dados reais nesta entrega.

Encerramento de conta/organização, exclusão pós-restauração de backups, política completa publicada e revisão manual assistiva continuam abertos. Inventário e detalhes de operação: docs/privacy-data-lifecycle.md. Não tratar a tarefa de privacidade como integralmente concluída.
