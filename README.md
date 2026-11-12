# OmniSight

Plataforma de auditoria de acessibilidade web orientada à WCAG 2.2, com achados
explicáveis, histórico de scans e adaptações locais reversíveis.

## Documentação

- [Especificação de requisitos](docs/requirements/software-requirements-specification.md)
- [Matriz WCAG, score e adaptações](docs/accessibility/wcag-score-adaptation-matrix.html)
- [Política de classificação por automação](docs/accessibility/automation-classification.md)
- [Requisitos brasileiros complementares](docs/compliance/brazilian-accessibility-requirements.md)
- [Política de conformidade e disclaimer](docs/compliance/conformity-policy-and-disclaimer.md)
- [ADRs de arquitetura](docs/architecture/adr/README.md)
- [Modelo de domínio e dados](docs/architecture/domain-model.md)
- [Contrato OpenAPI inicial](docs/architecture/openapi/openapi.json)
- [Diagramas UML](docs/architecture/uml/README.md)

## Continuação da sprint (11/11/2026)

O fluxo autenticado Django + Next foi retomado no monorepo. Scans possuem consumer,
leases e recuperação, cancel/retry, snapshots e acompanhamento no frontend.
O navegador separado integra axe-core sobre snapshot offline. Esse modo não
executa scripts ou CSS externos e não avalia contraste na página real.

- [Decisão de arquitetura e limites](docs/architecture/adr/0002-aws-pilot-offline-browser.md)
- [Deploy piloto AWS e custos](deploy/aws/README.md)
- [Verificação e gates pendentes](docs/testing/scan-pipeline.md)

Esta versão é candidata para validação de deploy: requer os gates de Chromium,
PostgreSQL/concorrência e Docker/Compose antes de publicar. Não houve deploy nem
alteração da demonstração pública simplificada. Cloudflare D1 não é usado aqui.

## Extensão experimental para a página renderizada

Após `npm run build --workspace @omnisight/web -- --webpack`, o frontend oferece
`/omnisight-extension.zip` e instruções em `/extensao-instalacao.html`.
A extensão é carregada sem compactação no Chrome/Edge de computador. Ela analisa
a aba autorizada com axe-core, exporta JSON local e permite importar no dashboard.
Não é publicada em loja; não varre automaticamente todas as rotas de um site.

- [Instalação, permissões e privacidade](apps/extension/README.md)
- [Arquitetura assistida e próximos passos](docs/architecture/adr/0003-assisted-rendered-dom.md)
- Gerar só o pacote: `python3 scripts/package_extension.py`
- Testes de contrato da extensão: `node --test apps/extension/tests.mjs`

## Medições visuais do snapshot

O serviço de navegador foi ampliado com screenshots desktop/mobile e revisões de
geometria, além de CSS do mesmo hostname obtido pelo coletor SSRF-safe. Essa camada
é uma captura parcial, não substitui a análise do DOM real da extensão e ainda
precisa passar no teste Chromium do ambiente de destino.
Veja [escopo e validação](docs/testing/visual-snapshot.md).

## Ferramentas e evolução da cobertura

[Comparativo técnico e sequência de integração](docs/research/accessibility-tooling.md):
Pa11y, QualWeb, Lighthouse, dom-accessibility-api e W3C ACT. Nesta versão, axe foi
ampliado para resultados separados por viewport; as demais engines continuam
como candidatas, sem alegação de integração ou benchmark já executado.
