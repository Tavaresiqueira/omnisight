# Encerramento e recuperação sem ressuscitar exclusões

## Fluxos disponíveis

- `POST /api/auth/account/close/`, com senha atual e confirmação exata `ENCERRAR MINHA CONTA`: remove usuário, tokens e espaços em que ele é o único membro e proprietário, em cascata com sites/scans/relatórios. Espaços com outro owner ficam preservados. Se houver outros membros e nenhum outro owner, a operação responde 409 antes de qualquer exclusão: resolver esse espaço explicitamente primeiro. Transferência de propriedade ainda não tem interface nesta versão.
- `POST /api/organizations/{id}/`, com senha atual e confirmação exata do nome: owner pode encerrar o espaço inteiro, inclusive os dados compartilhados, preservando as contas pessoais dos membros. Outros papéis recebem 403 e outra organização recebe 404. Encerrar o último espaço deixa a conta ativa, com organization/role nulos; a interface permite exportar/encerrar a conta, sem inventar um novo espaço automaticamente.
- `GET /api/auth/account/export/`: cadastro básico e associações da própria conta, sem hash de senha, token ou dados pessoais dos demais membros. Os relatórios autorizados continuam sendo exportados individualmente no painel de scans. Não há exportação monolítica de toda a organização.
- Painel em “Privacidade e conta”: confirmação escrita, senha e reconhecimento do impacto. Contas demo compartilhadas não podem ser encerradas pelo painel. Cinco tentativas de encerramento por usuário/minuto e dez/IP/minuto limitam a verificação de senha. Sair da aplicação ainda limpa somente a sessão local; encerramento da conta revoga seus tokens no banco.

## Registro de intenções independente do banco

Antes de apagar manualmente scan, organização ou conta, a API grava uma intenção confirmada em JSONL, faz fsync no arquivo e diretório e só depois conclui a transação SQL. Campos: versão, tipo, UUID do alvo, horário, assinatura anterior e HMAC-SHA256. Não guarda e-mail, nome, URL, senha ou token. UUID e horário ainda são metadados vinculáveis e exigem acesso restrito. O registro é separado do dump PostgreSQL e não deve ser restaurado a partir da mesma cópia antiga do banco.

Configurar chave aleatória independente `DELETION_LEDGER_KEY` com ao menos 32 caracteres e caminho persistente `DELETION_LEDGER_PATH`. Em Compose a API usa volume `deletion-ledger`, diretório 0700 e arquivo novo 0600; só ela recebe a chave. O journal utiliza lock de arquivo entre processos, assinatura encadeada e limite de 8 MiB; arquivo incompleto, alterado, indisponível ou sem chave bloqueia novas exclusões com 503. Planejar rotação antes de atingir esse limite, preservando todas as gerações e checkpoints enquanto houver backups que possam conter seus alvos. Não truncar o arquivo.

A gravação antecede o commit: se o banco falhar depois do fsync, a intenção permanece e a reaplicação poderá concluir aquele pedido confirmado. Esse comportamento favorece privacidade e deve constar do procedimento operacional. Purgas automáticas por idade não geram intenção individual; a retenção é reaplicada após restaurar.

### Limite crítico de durabilidade

Volume no mesmo servidor não é cópia fora do servidor. O código atual não envia o journal a storage externo antes de confirmar a exclusão. Para resistência à perda total do host é necessário configurar armazenamento independente e garantir que o checkpoint contemple todas as exclusões confirmadas. Replicação periódica pode perder pedidos mais recentes; não prometer proteção contra esse cenário enquanto esse gate estiver aberto.

A cadeia detecta modificação/remoção interna, mas um prefixo antigo ainda tem assinaturas válidas. Por isso o replay exige `--expected-sha256`, obtido de um checkpoint atual mantido independentemente do banco e do arquivo restaurados. Não recalcular o checkpoint de uma cópia suspeita e tratá-lo como autoridade. O journal e a chave devem sobreviver pelo menos ao backup mais antigo recuperável, incluindo cópias remotas; definir prazo e rotação com o operador.

## Backup criptografado

`deploy/backup/backup.sh` usa cliente PostgreSQL 16, `pg_dump --format=custom` e `age` por pipe, sem dump plaintext em disco. A máquina de backup precisa apenas do destinatário público age. Guardar a identidade privada de recuperação separadamente. `pipefail` impede sucesso falso quando dump falha. Arquivo incompleto é removido; depois de sucesso gera SHA-256 e descarta somente arquivos locais backup-*.age e sidecars desse diretório mais antigos que `BACKUP_RETENTION_DAYS` (padrão sete dias). Checksum detecta corrupção acidental; não substitui assinatura/autenticidade de origem.

Variáveis para execução direta: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSFILE (0600), AGE_RECIPIENT, BACKUP_DIR. Não passar senha PostgreSQL na linha de comando. Usar diretório dedicado protegido. No Compose, o perfil opcional ops fornece backup com PostgreSQL 16/age e acesso somente à rede privada database: configurar AGE_RECIPIENT e executar `docker compose -f deploy/compose.yml --profile ops run --rm backup`. Saída criptografada fica no volume encrypted-backups; não há porta pública do banco. Esse container usa a credencial de banco existente do MVP; criar credencial dedicada de leitura para produção. Upload remoto, retenção remota e monitor/notificação ainda não estão provisionados. O timer systemd abaixo é para a execução direta com conexão privada alcançável: adaptar ExecStart para Compose se esse for o modo escolhido; não abrir porta pública do banco para atender ao timer.

Unidades systemd fornecidas para instalação pelo operador: código em /opt/omnisight, usuário omnisight-backup, configuração protegida em /etc/omnisight/backup.env, saída /var/backups/omnisight. Timer diário às 03:00 UTC com até cinco minutos de atraso e execução perdida recuperada. Não foram instaladas nem ativadas nesta entrega. Meta inicial proposta: RPO de dados até 24 horas e RTO de uma hora; dependem de backup bem-sucedido, cópia externa e teste medido. Não são SLAs comprovados. Falha retorna erro/log; conectar a um monitor que alerte e acompanhe a idade do último backup, não somente o timer.

## Procedimento de restauração

1. Manter destino isolado, API/consumidores/retention parados e banco original preservado. Criar manualmente um banco vazio com nome `omnisight_restore_*`, usando credencial de recuperação dedicada. Não apontar scripts ao banco vivo.
2. Obter backup age, identidade privada protegida, **journal mais recente independente**, chave original HMAC e checkpoint atual confiável. Copiar o journal de forma consistente, sem escrita concorrente (lock compartilhado); protegê-lo e sua chave fora do servidor de origem. Em implantação inicial sem intenções, inicializar um journal vazio via `append_deletions([])` e registrar seu checkpoint; nunca substituir journal existente por vazio.
3. Configurar PG* para o destino, BACKUP_FILE, AGE_IDENTITY_FILE, DELETION_LEDGER_PATH, DELETION_LEDGER_KEY e DELETION_LEDGER_SHA256. Executar `bash deploy/backup/restore.sh --apply`. O script deriva DATABASE_URL do mesmo PG* para evitar aplicar exclusões em outro banco.
4. O script valida journal/checkpoint antes de restaurar, exige destino vazio, decripta por pipe para pg_restore em transação, migra, reaplica exclusões, revoga todos os tokens/sessões restaurados e aplica todos os lotes de retenção. Replay é idempotente e valida o arquivo inteiro antes de apagar qualquer alvo. Em falha, o destino permanece isolado; recriar banco descartável e repetir com inputs corretos, sem remover dados do banco original.
5. Validar dados preservados, ausência dos alvos excluídos, permissões e smoke. Revisar recuperação de senhas: os hashes refletem o momento do backup; eventos posteriores não são recuperados automaticamente. Fluxo completo de reset de senha ainda não foi implementado. Só o operador decide reabrir tráfego após revisão; o script nunca promove o destino automaticamente.

Sem --apply, restore recusa executar; `reapply_deletions` simula por padrão e --validate-only verifica somente o journal. O replay é para recuperação offline, não para uma API pública ou banco em operação.

## Validação

Testes locais cobrem senha/confirmação, proprietário, coowner, cascata, exportação sem segredos, falha segura sem journal, HMAC adulterado, simulação e replay de identificadores antigos, além dos guardas dos scripts e falha do dump. Job `restore-drill` preparado no CI: PostgreSQL 16 real, dump criptografado com age, encerramento posterior ao dump, restore isolado, replay e verificação de que outra conta permanece e tokens restaurados são revogados. Evidência `restore-drill-evidence` por sete dias contém log de contagens/migrações, sem dump, journal ou chaves. Ainda não houve execução real desse job nem medição de RPO/RTO.

Referências técnicas: [pg_dump 16](https://www.postgresql.org/docs/16/app-pgdump.html), [pg_restore 16](https://www.postgresql.org/docs/16/app-pgrestore.html), [age](https://github.com/FiloSottile/age).
