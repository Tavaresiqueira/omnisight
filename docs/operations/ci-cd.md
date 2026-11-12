# CI/CD do piloto AWS

## Fluxo

PR e branches executam `Quality gates`. Na main, `Release` chama os mesmos
gates e só depois constrói quatro imagens Linux x86_64, identificadas pelo SHA
completo do commit: API, browser, web e backup. Os arquivos Docker são os mesmos
usados no Compose. As imagens são artefatos privados do Actions, retidos por um dia;
não exigem token de registry nem credenciais AWS no CI.

O deploy usa SSH com chave do host previamente conferida. Só executa na main,
depois dos gates e builds, quando a variável de **repositório** `DEPLOY_ENABLED`
vale `true`. O job utiliza o environment `production`. Configure esse environment
antes de habilitar a variável; restrinja as branches a main e, se disponível no
plano, exija aprovação. PRs nunca recebem os secrets de deploy.

O workflow não cria VM, DNS ou recursos AWS. O servidor precisa existir e estar
preparado conforme `deploy/aws/README.md`. Use uma VM de teste inicialmente.

## Configuração no GitHub

Settings → Environments → production:

| Tipo | Nome | Conteúdo |
| --- | --- | --- |
| Secret | `DEPLOY_SSH_KEY` | Chave SSH privada dedicada do usuário de deploy |
| Secret | `DEPLOY_KNOWN_HOSTS` | Linha OpenSSH do host, conferida por canal independente |
| Variable | `DEPLOY_HOST` | IP ou hostname da VM, sem protocolo |
| Variable | `DEPLOY_USER` | Usuário SSH, por exemplo `ubuntu` |

Settings → Secrets and variables → Actions → Variables:

| Nome | Valor |
| --- | --- |
| `DEPLOY_ENABLED` | `false` até o servidor estar pronto; depois `true` |

Não cole chaves na conversa. O CI não precisa de secrets para rodar os testes.
Não use `StrictHostKeyChecking=no` nem aceite automaticamente a chave retornada
por `ssh-keyscan`: compare o fingerprint com o console confiável da VM primeiro.

## Preparação do host

Docker/Compose v2 com suporte a `up --wait`, bash, flock, gzip e espaço para as
imagens/releases. O usuário SSH precisa gravar em `/opt/omnisight/incoming` e
executar a ativação com sudo sem prompt. Isso concede controle do host ao workflow:
use chave dedicada, proteja main e limite o SSH na rede. GitHub-hosted runners usam
IPs variáveis; o SSH restrito ao IP pessoal no template Lightsail não permite CD
direto. Defina antes um acesso de rede aprovado (por exemplo runner com IP fixo
permitido); este workflow não abre a porta 22 nem altera firewall.

Criar `/opt/omnisight/shared/production.env`, propriedade root e modo 600, com:

```dotenv
APP_DOMAIN=seu.dominio.example
DJANGO_SECRET_KEY=valor-aleatorio-com-pelo-menos-50-caracteres
POSTGRES_PASSWORD=valor-hexadecimal-aleatorio
DELETION_LEDGER_KEY=outro-segredo-aleatorio-com-pelo-menos-32-caracteres
AGE_RECIPIENT=age1chavepublicadobackup
```

Manter esses valores estáveis entre releases. A identidade privada age fica fora
da VM. Configurar cópia externa de backup, registro de exclusões e checkpoint
independente antes de uso público. A ativação cria backup criptografado antes de
atualizar um DB já em execução; a primeira instalação não possui DB para salvar.
O arquivo ainda precisa ser copiado para fora do host pelo procedimento operacional.

## Atualização, falha e rollback

O host confere o checksum do transporte, carrega as imagens do commit, mantém o
project-name `omnisight` e os volumes existentes. Um lock impede ativações paralelas.
Para atualizar: backup, DB pronto, pausa dos writers, migração explícita, serviços
recriados e smoke HTTPS de API/frontend. Há breve indisponibilidade durante essa
troca. O smoke não substitui a jornada E2E executada no CI.

Só após sucesso atualiza `/opt/omnisight/current` e `deployed-sha`. Falha anterior
pode já ter alterado banco e serviços; o symlink antigo não significa rollback.
Inspecione logs e schema. Não há reversão automática de migração ou restauração de
DB. Nunca use `down -v`. Imagens e diretórios antigos são mantidos para rollback de
código compatível, e exigem limpeza manual após revisão de espaço.

Para tentar novamente o mesmo SHA após falha, primeiro diagnostique o estado e
renomeie o diretório de release incompleto; o script recusa sobrescrevê-lo.
Reexecutar `Release` pela main passa de novo pelos gates e builds.

## Evidências e pendências

`actionlint` reproduziu os três erros de contexto `runner.temp` do workflow antigo.
As paths de recuperação agora são configuradas num step via `GITHUB_ENV`.
O lint também roda no CI para impedir recorrência. Jobs possuem timeout e Compose
imprime logs em caso de erro. Artefatos E2E/restore ficam disponíveis sete dias.

CI remoto, build das imagens, migrações e deploy real devem ser verificados nas
execuções do Actions; validação estática local não comprova esses resultados.
Habilitar required checks em main após a primeira execução verde. Este incremento
não configura sozinho proteção de branch, environment, backup externo ou AWS.
