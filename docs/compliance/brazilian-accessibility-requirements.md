# Requisitos brasileiros complementares de acessibilidade digital

**Status:** Baseline de engenharia

**Data da revisão:** 2026-09-10

**Rastreabilidade:** ClickUp `86e2v62eq`; RF-007 a RF-011; RNF-ACC-001; RNF-ETH-001

## Escopo

Este documento complementa a WCAG 2.2 com referências brasileiras úteis ao
OmniSight. Ele orienta requisitos de produto e evidências técnicas; não determina,
sozinho, a obrigação jurídica aplicável a cada cliente.

## Referências e impactos no produto

| Norma ou obrigação | Aplicabilidade a confirmar | Decisão de produto | Evidência esperada | Fonte oficial |
| --- | --- | --- | --- | --- |
| Lei nº 13.146/2015 (LBI), art. 63: acessibilidade segundo melhores práticas e diretrizes internacionais e símbolo de acessibilidade em destaque. | Sites mantidos por empresas com sede ou representação comercial no Brasil e por órgãos de governo. O enquadramento concreto requer revisão jurídica. | Permitir relatório por URL, registrar cobertura WCAG e incluir verificação orientada do símbolo quando aplicável. Não declarar atendimento legal somente pelo score. | URL, data, versão das regras, achados e itens para revisão humana. | [LBI](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm) |
| eMAG 3.1: modelo organizado em marcação, comportamento, conteúdo, apresentação, multimídia e formulários, sem excluir boas práticas WCAG. | Sites e serviços de governo eletrônico; confirmar ente, contrato e versão exigida. | Disponibilizar o eMAG como perfil complementar, sem substituir a WCAG 2.2 nem misturar resultados silenciosamente. | Perfil selecionado, versão, regra e referência eMAG em cada achado aplicável. | [eMAG](https://emag.governoeletronico.gov.br/) |
| ABNT NBR 17225: acessibilidade em conteúdo e aplicações web. | Quando adotada por contrato, política interna, edital ou avaliação normativa específica. O texto integral deve ser consultado sob licença. | Manter referência no catálogo e realizar análise licenciada antes de afirmar cobertura detalhada. | Versão consultada, responsável pela revisão e matriz de correspondência aprovada. | [Portal Governo Digital](https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/acessibilidade-digital) |
| Lei nº 13.709/2018 (LGPD): finalidade, adequação, necessidade, transparência, segurança, prevenção e prestação de contas no tratamento de dados pessoais. | Quando o scan, cadastro, relatório, log ou evidência tratar dado pessoal dentro do âmbito territorial e material da lei; base legal e papéis devem ser definidos por caso. | Minimizar evidências, evitar segredos e dados de formulário, controlar retenção/exclusão, isolar organizações e registrar finalidade e acesso. | Inventário de dados, base legal aprovada, política de retenção, testes de isolamento e trilha de auditoria. | [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm) |
| Requisito contratual, editalício ou política do cliente. | Somente quando o instrumento aplicável definir padrão, nível, versão, páginas, evidências ou prazo. | Registrar como perfil separado e versionado; divergências não alteram silenciosamente o resultado WCAG. | Instrumento identificado, cláusula, responsável pela interpretação e matriz de cobertura aprovada. | Fonte fornecida pelo cliente e validada no projeto. |

## Requisitos derivados

1. O relatório deve identificar padrão, nível, versão e escopo efetivamente
   avaliados.
2. O perfil brasileiro deve ser aditivo: WCAG 2.2, eMAG e eventual mapeamento ABNT
   permanecem distinguíveis.
3. Requisitos que dependam de conteúdo, contexto administrativo ou interpretação
   jurídica devem ser marcados para revisão humana.
4. A presença do símbolo de acessibilidade pode ser detectada como indício, mas a
   adequação e o destaque exigem revisão contextual.
5. O catálogo deve conservar a origem normativa e a versão de cada regra para que
   um scan histórico continue reproduzível.
6. Mudanças legais ou normativas exigem revisão da matriz antes de alterar score ou
   mensagens públicas.
7. Dados pessoais encontrados em páginas auditadas não devem ser presumidos como
   necessários: coleta, screenshot e retenção exigem finalidade e minimização.

## Limites

O OmniSight fornece apoio técnico e educacional. Seus resultados não constituem
parecer jurídico, auditoria humana completa, certificação ou garantia de
conformidade com a LBI, o eMAG, a ABNT NBR 17225 ou a WCAG. A aplicabilidade a um
serviço específico deve ser avaliada por profissionais qualificados e com acesso
ao contexto integral.

## Fontes oficiais consultadas

- [Lei nº 13.146/2015 — Lei Brasileira de Inclusão](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13146.htm)
- [Lei nº 13.709/2018 — Lei Geral de Proteção de Dados](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [eMAG — Modelo de Acessibilidade em Governo Eletrônico](https://emag.governoeletronico.gov.br/)
- [Acessibilidade Digital — Governo Digital](https://www.gov.br/governodigital/pt-br/acessibilidade-e-usuario/acessibilidade-digital)
- [WCAG 2.2 — recomendação oficial do W3C](https://www.w3.org/TR/WCAG22/)
