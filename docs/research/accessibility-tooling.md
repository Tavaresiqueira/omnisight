# Ferramentas para aprofundar OmniSight

Pesquisa em fontes primárias - 11/11/2026. Trata-se de uma seleção técnica,
não de um benchmark executado. As integrações futuras abaixo NÃO foram instaladas.

| Ferramenta | Contribuição | Decisão para OmniSight |
| --- | --- | --- |
| axe-core | Regras automatizadas, resultados incomplete e evidências DOM | Já integrado e versionado. Agora repetido por viewport. |
| Playwright | Navegação, screenshots, emulação e snapshots ARIA | Já integrado ao snapshot isolado. Rotas/estados e ARIA snapshot são evolução futura. |
| Pa11y / Pa11y CI | Runner CLI/CI; pode usar axe ou HTML CodeSniffer | Útil para testes do próprio produto. Pa11y+axe não é segunda engine independente. HTMLCS exige avaliação de cobertura e normalização. |
| QualWeb | Avaliador com módulos de regras ACT e técnicas WCAG | Candidato para segunda opinião normativa. Validar versão, licenças, consistência das regras e execução isolada antes de integrar. |
| Lighthouse | Acessibilidade, desempenho, SEO e boas práticas | Executar futuramente na página real/ambiente de teste. Performance de snapshot offline não representa a experiência real. A parte de acessibilidade compartilha verificações axe; não somar scores como consenso independente. |
| dom-accessibility-api | Calcula nome e descrição acessíveis para testes | Útil para fixtures unitárias de nomes. Não substitui layout nem árvore real do browser. |
| W3C ACT Rules | Regras de teste documentadas e implementações listadas | Usar para rastreabilidade, aplicabilidade e fixtures positivas/negativas. Não é uma engine que se instala. |

## Prioridade proposta

1. Validar no Chromium real o pipeline existente (ainda pendente neste ambiente).
2. Corrigir cobertura por viewport: implementado nesta entrega. Cada perfil executa
   axe e mede geometria, com resultados separados; o painel geral é desktop.
3. Criar fixtures com estados permitidos (menu, modal, erro de formulário) e
   snapshots ARIA do Playwright. Nada de explorar cliques ou contas automaticamente.
4. Avaliar QualWeb em um corpus controlado e comparar condições equivalentes.
5. Adicionar Lighthouse como relatório separado em ambiente real autorizado,
   mantendo performance e acessibilidade como dimensões diferentes.

## Como comparar engines sem inventar confiança

Preservar engine, versão, regra, critério, modo, viewport e estado. Não deduplicar
só por seletor: duas regras no mesmo elemento podem apontar condições diferentes.
Não tratar duas interfaces que usam axe como duas confirmações independentes.
Uma divergência entre engines demanda análise de aplicabilidade e evidência;
quantidade de ferramentas ou concordância não comprova uma violação WCAG.
Não gerar nota universal misturando desempenho, heurísticas visuais e conformidade.

## Corpus de validação

Para cada família, preparar página positiva e negativa: imagem sem alt, nome de
controle, label visível, aria-labelledby inválido, headings e idioma, contraste
sobre fundo uniforme/complexo, alvos com e sem exceção de espaçamento, menu fora de
tela intencional e truncamento com alternativa acessível. Registrar estado e
viewport. A execução isolada não carrega todos os recursos e deve declarar isso.
Esse corpus ampliado ainda não foi executado; fixtures atuais cobrem só um subconjunto.

## Fontes consultadas

- https://github.com/pa11y/pa11y
- https://github.com/pa11y/pa11y-ci
- https://github.com/qualweb/core (documentação do motor e referência ao monorepo)
- https://github.com/qualweb/qualweb
- https://github.com/GoogleChrome/lighthouse
- https://github.com/eps1lon/dom-accessibility-api
- https://playwright.dev/python/docs/aria-snapshots
- https://www.w3.org/WAI/standards-guidelines/act/
- https://www.w3.org/WAI/standards-guidelines/act/implementations/
