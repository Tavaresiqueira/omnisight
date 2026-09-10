# Política de conformidade e disclaimer

**Status:** Aprovada para uso no MVP

**Data:** 2026-09-10

**Rastreabilidade:** ClickUp `86e2v62fj`; RNF-ACC-002; RNF-ETH-001; RB-001, RB-002 e RB-004

## Princípio

O OmniSight comunica evidências de acessibilidade, e não certificação. Um scan
automatizado observa uma parte da página em condições conhecidas; conformidade
integral depende também de avaliação humana, fluxos completos, conteúdo, contexto
e tecnologias assistivas.

## Vocabulário obrigatório

| Estado | Uso permitido |
| --- | --- |
| Violação confirmada | A regra determinística encontrou evidência suficiente e reproduzível no escopo executado. |
| Precisa de revisão | Existe sinal técnico, mas é necessário julgamento humano. |
| Aprovado na regra | A regra executada não encontrou o problema; não significa que a página inteira esteja conforme. |
| Não testado | O critério, estado, fluxo ou tecnologia não foi coberto pelo scan. |
| Informativo | Observação sem impacto automático no score. |

São proibidas expressões como **site certificado**, **100% acessível**, **totalmente
conforme** ou equivalentes quando baseadas apenas no produto.

## Disclaimer obrigatório do relatório

> Este relatório apresenta resultados técnicos obtidos no escopo, data, viewport e
> versões de regras indicados. A ausência de achados automáticos não comprova
> conformidade integral. Critérios sem cobertura automática, conteúdo, jornadas e
> uso com tecnologias assistivas exigem avaliação humana. O score é um indicador
> interno e explicável; não é certificação, parecer jurídico nem garantia de
> atendimento à WCAG ou à legislação aplicável.

Uma versão curta pode aparecer ao lado do score, desde que haja acesso direto ao
texto completo:

> Indicador técnico, não certificação. Consulte a cobertura e os itens para revisão humana.

## Conteúdo mínimo de cada relatório

- URL normalizada, momento da coleta e viewport;
- padrão, nível e versão declarados;
- versão do engine, catálogo de regras e fórmula do score;
- quantidade de regras executadas, não testadas e inconclusivas;
- achados separados por tipo de validação, severidade e confiança;
- limitações de autenticação, navegação, conteúdo dinâmico ou coleta;
- caminho para contestação, nova análise ou revisão humana.

## Score e comparações

O score só pode comparar execuções compatíveis quanto a URL normalizada, viewport,
versões e parâmetros. Mudanças de cobertura devem ser destacadas. Itens que
precisam de revisão não podem receber a mesma penalização de uma violação
confirmada, e severidade não pode ser usada como sinônimo de confiança.

## Dados, segurança e retenção

Evidências devem ser mínimas e acessíveis somente dentro da organização autorizada.
Tokens, cookies, senhas, dados de formulário e conteúdo sensível não devem aparecer
em screenshots, logs ou relatórios. URLs e redirecionamentos passam por validação
contra SSRF antes de qualquer coleta. Retenção e exclusão seguem a política
publicada e preservam apenas a auditoria mínima justificada.

## Revisão e escalonamento

A política deve ser revisada quando houver mudança de regra, fórmula, cobertura,
padrão normativo ou posicionamento público. Alegações de certificação, dúvidas de
aplicabilidade legal e resultados de alto impacto com baixa confiança devem ser
escalonados para revisão humana qualificada antes da publicação.
