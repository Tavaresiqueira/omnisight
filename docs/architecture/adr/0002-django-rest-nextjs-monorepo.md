# ADR 0002 — Django REST Framework e Next.js em monorepo

**Estado:** Aceita

**Data:** 2026-09-24

**Rastreabilidade:** ClickUp `86e2v67qa`; RF-001; ADR 0001

## Contexto

O primeiro incremento executável do MVP precisa entregar cadastro, autenticação e
isolamento por organização. O ADR 0001 definiu os limites do monólito modular, mas
adiou a escolha física de frameworks. A equipe escolheu Python para a API e React
para a experiência web, mantendo os dois aplicativos no mesmo repositório durante
o MVP.

## Decisão

Adotar um monorepo com:

- `apps/api`: Django e Django REST Framework para identidade, organizações e os
  próximos módulos do plano de controle;
- `apps/web`: Next.js com TypeScript e App Router para a interface web;
- SQLite apenas no desenvolvimento e nos testes iniciais; a escolha do banco de
  produção permanece pendente;
- autenticação por token opaco do DRF no primeiro incremento, sempre transmitido
  por HTTPS fora do ambiente local;
- Vitest e Testing Library para componentes web, e o test runner do Django para
  modelos e contratos da API.

O tipo de conta (`extension_user` ou `platform_developer`) representa a intenção
inicial do usuário. Cada cadastro cria uma organização própria e uma associação
`owner`. Esse tipo não substitui autorização: toda consulta futura continua sendo
escopada pela associação à organização autenticada.

## Consequências

- frontend e API evoluem juntos, com contratos explícitos entre os aplicativos;
- o modelo customizado de usuário precisa existir desde a primeira migration;
- tokens do MVP podem ser revogados no servidor, mas expiração e rotação serão
  revisitadas antes de produção;
- CORS, cookies, persistência segura no navegador e banco de produção precisam de
  decisões próprias antes de um deploy público;
- contas demo são criadas por comando explícito e só recebem senha padrão quando
  `DEBUG` está ativo.

## Evidência esperada

- testes de cadastro, autenticação e isolamento entre organizações;
- testes dos dois caminhos de perfil e dos atalhos de demonstração;
- build dos aplicativos e inspeção manual da página de autenticação.
