# Política de classificação dos critérios por automação

**Status:** Aprovada para o MVP

**Data:** 2026-09-10

**Rastreabilidade:** ClickUp `86e2v62du`; RF-007 a RF-010; RNF-ACC-002; RB-001, RB-002 e RB-004

## Objetivo

Estabelecer como o OmniSight classifica a capacidade de teste de cada critério da
WCAG 2.2 e impedir que sinais incompletos sejam apresentados como violações
confirmadas. A fonte de verdade dos 86 critérios ativos continua sendo a
[matriz WCAG 2.2, score e adaptações](wcag-score-adaptation-matrix.html), na coluna
**Teste inicial**.

## Classes de teste

| Classe | Quando usar | Resultado permitido |
| --- | --- | --- |
| Automático | A regra pode decidir de forma determinística a partir de DOM, árvore de acessibilidade, estilo computado, geometria ou resposta HTTP. | Aprovado, violação confirmada ou inconclusivo quando a evidência não for suficiente. |
| Semiautomático | A máquina localiza um possível problema, mas contexto, intenção, qualidade ou interação exigem revisão humana. | Precisa de revisão; nunca deve ser convertido automaticamente em violação confirmada. |
| Manual | A avaliação depende principalmente de significado, experiência de uso, sequência, conteúdo ou interação humana. | Item de checklist com orientação e evidência a coletar. |

A classificação descreve o método inicial, não a importância do critério. Nível
WCAG, severidade, confiança e tipo de validação são dimensões independentes.

## Regras automáticas comprometidas no MVP

O primeiro scanner pode implementar somente verificações com evidência
reproduzível e baixo risco de interpretação indevida:

| Família | Evidência mínima | Limite obrigatório |
| --- | --- | --- |
| Metadados da página | Presença e validade de `title` e `lang`. | O idioma real do conteúdo pode exigir revisão. |
| Estrutura e semântica | Hierarquia de títulos, landmarks, atributos e relações programáticas. | A adequação semântica ao conteúdo permanece humana quando ambígua. |
| Formulários e nomes acessíveis | Associação entre controle, rótulo e nome acessível calculado. | Clareza e qualidade do rótulo não são inferidas apenas pela presença. |
| Contraste | Cores computadas, tamanho/peso de fonte e razão calculada. | Fundos complexos, imagens, transparência e estados dinâmicos podem ser inconclusivos. |
| Tamanho de alvo | Geometria estável do elemento e espaçamento observável. | Zoom, sobreposição e alvos condicionais exigem contexto de viewport. |
| Conteúdo não textual | Presença de alternativa e papel acessível. | A qualidade da alternativa textual sempre pode exigir revisão humana. |

Uma regra só entra nessa lista depois de possuir identificador e versão, fixtures
positivas e negativas, evidência reproduzível e mapeamento para critério WCAG.

## Tratamento no relatório e no score

- Violação confirmada: entra no score conforme fórmula e versão registradas.
- Precisa de revisão: aparece separadamente e não recebe a mesma penalização de
  uma violação confirmada.
- Aprovado: significa apenas que a regra executada não encontrou o problema no
  escopo observado.
- Não testado: deixa explícita a ausência de cobertura.

O relatório deve mostrar regra, versão, URL normalizada, elemento ou referência,
evidência técnica, viewport, horário, severidade e confiança. Nenhum agregado pode
ser descrito como certificação de conformidade.

## Governança de mudança

Alterações entre automático, semiautomático e manual exigem atualização da matriz,
registro no changelog das regras e testes correspondentes. Regressões de confiança
devem rebaixar o resultado para **Precisa de revisão**, preservando os snapshots
anteriores com a versão original.

## Evidência de aceite

- Os 86 critérios ativos e o critério 4.1.1, removido na WCAG 2.2, estão
  catalogados e filtráveis por tipo de teste na matriz.
- As classes têm critérios de entrada e saída explícitos.
- Achados inconclusivos não são promovidos a violação confirmada.
- O escopo automatizável do MVP está separado da cobertura total da WCAG 2.2.
