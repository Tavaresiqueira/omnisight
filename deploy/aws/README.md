# OmniSight - piloto AWS Lightsail

## Escolha e custo (consulta oficial: 11/11/2026)

Alvo: uma VM x86_64 Ubuntu 24.04 com Docker Compose. PostgreSQL + Django/API +
consumer + serviço Chromium/axe-core + frontend estático + Caddy/HTTPS.

Referência Lightsail Linux com IPv4: 2 GB a US$ 12/mês; é o mínimo experimental,
sem benchmark de memória deste conjunto. Para folga do Chromium, avaliar 4 GB
antes de uso contínuo. Conferir preço/região no console antes de criar a instância.
Não inclui domínio, impostos, câmbio, backups nem tráfego excedente.

Novas contas AWS podem receber US$ 100 iniciais e até US$ 100 adicionais em
créditos. Free plan: até 6 meses ou esgotamento dos créditos. Contas anteriores,
contas Paid e elegibilidade de cada serviço têm regras diferentes. Não presumir
12 meses de EC2 grátis nem três meses de Lightsail grátis: a FAQ atual de Lightsail
informa que ofertas antigas foram substituídas pelo novo Free Tier.

Fontes:
- https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html
- https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html
- https://docs.aws.amazon.com/en_en/lightsail/latest/userguide/amazon-lightsail-frequently-asked-questions-faq-billing-and-account-management.html

## Gates antes de provisionar

1. Executar `.github/workflows/quality.yml` e exigir todos os jobs verdes,
   especialmente sandbox do Chromium e smoke do Compose. Aqui o host bloqueou
   sockets necessários ao Chromium, e Docker não está disponível.
2. Verificar plano da conta, créditos, serviço disponível e alertas de orçamento.
   Alertas avisam; não limitam automaticamente a conta Paid.
3. Executar localmente `aws cloudformation validate-template --template-body
   file://deploy/aws/lightsail.json` com AWS CLI autenticada.
4. Selecionar região, AZ, blueprint Ubuntu e bundle x86_64 reais retornados pelos
   comandos abaixo. O template não inventa IDs nem cria recursos automaticamente.

```sh
aws lightsail get-blueprints --query 'blueprints[?isActive].[blueprintId,name]'
aws lightsail get-bundles --no-include-inactive --query 'bundles[?isActive].[bundleId,ramSizeInGb,price,supportedPlatforms]'
aws lightsail get-regions --include-availability-zones
```

Escolher um bundle Linux/IPv4 x86_64, memória >= 2 GB. A imagem Playwright foi
preparada para x86_64; ARM não foi validado. O template cria VM + IP estático,
abre 80/443 e restringe SSH ao IPv4/32 informado. Isso cria recursos cobrados.
Criar o stack pelo console CloudFormation, informando todos os parâmetros.

## Instalação no servidor

O bootstrap instala Docker/Compose. Aguarde sua conclusão. Faça upload do ZIP
completo e extraia em `/opt/omnisight` usando SSH/SCP. Não envie secrets na conversa.
O usuário ubuntu não foi adicionado ao grupo docker; use sudo nos comandos abaixo.

```sh
cd /opt/omnisight
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
python3 -c 'import secrets; print(secrets.token_hex(40))'
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Preencher `deploy/.env`: domínio real em APP_DOMAIN (sem https://), primeiro segredo
em DJANGO_SECRET_KEY e segundo em POSTGRES_PASSWORD (hexadecimal, URL-safe).
Aponte um registro A do subdomínio ao IP estático. Caddy obtém HTTPS por ACME;
80/443 precisam ser acessíveis. Se usar Cloudflare DNS, inicialmente DNS only;
depois validar o modo Full (strict) e os certificados. Não é necessário Route 53.

```sh
sudo docker compose --env-file deploy/.env -f deploy/compose.yml config --quiet
sudo docker compose --env-file deploy/.env -f deploy/compose.yml build
sudo docker compose --env-file deploy/.env -f deploy/compose.yml up -d
sudo docker compose --env-file deploy/.env -f deploy/compose.yml ps
```

A migração é um serviço de execução única que precisa concluir antes da API e do
consumer. Demo login fica desabilitado em produção. Cadastre uma conta normal na
interface para testar o fluxo. API, PostgreSQL e browser não possuem portas públicas.

## Smoke e validação

```sh
APP_DOMAIN=seu.dominio.example sh deploy/smoke.sh
sudo docker compose --env-file deploy/.env -f deploy/compose.yml exec -T -e RUN_BROWSER_TESTS=1 browser python -m unittest discover -s tests -v
```

Testar cadastro/login, URL, scan queued → running → completed, relatório, cancelar
e retry. Uma falha de browser deve aparecer como failed e nunca como relatório
aprovado. Não expor o piloto sem revisar rate limit/abuso e os demais gates do ADR.

## Backup, atualização e rollback

Antes de atualizar, exporte o DB com `pg_dump`, mantenha o backup fora da VM e
confirme um restore em banco separado. Não há backup automatizado nesta entrega.
Guardar também o ZIP e identificação da versão anterior. Builds frontend/Chromium
consomem RAM: preferir construir imagens no CI e transferi-las quando possível.

```sh
sudo docker compose --env-file deploy/.env -f deploy/compose.yml exec -T db pg_dump -U omnisight -d omnisight > backup.sql
chmod 600 backup.sql
```

As migrações desta entrega adicionam campos/tabela, sem apagar os anteriores.
Rollback de código: recuperar o ZIP anterior e reconstruir imagens; não reverter
migrações nem restaurar DB sem avaliar os dados gravados depois do deploy.
Não usar `docker compose down -v` no servidor: apaga os volumes persistentes.
Parar uma VM pode manter cobranças; para encerrar o piloto, exportar os dados e
remover os recursos cobrados de forma consciente, inclusive IPs/snapshots avulsos.

## Cloudflare

D1 não é usado por esta configuração. O Django continua com PostgreSQL, mantendo
suas transações e modelos. Uma migração para Worker/D1 seria uma mudança de
arquitetura separada. O deploy rápido anterior permanece independente deste ZIP.
