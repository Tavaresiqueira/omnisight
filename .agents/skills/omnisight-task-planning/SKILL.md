---
name: omnisight-task-planning
description: Padronizar a criação, o refinamento e a revisão de tarefas do projeto OmniSight. Usar ao criar ou alterar itens no ClickUp, planejar backlog ou sprint, definir prioridade, estimar trabalho em Fibonacci e verificar DoR/DoD, critérios de aceitação, dependências e evidências.
---

# Planejamento de tarefas do OmniSight

Criar tarefas pequenas, testáveis e rastreáveis, alinhadas ao Product Goal e à WCAG 2.2 pt-BR.

## Fluxo obrigatório

1. Confirmar valor para o usuário e macroárea.
2. Dividir itens que misturem entregas independentes.
3. Verificar a Definition of Ready antes de levar à sprint.
4. Estimar Complexidade, Incerteza e Esforço em Fibonacci.
5. Definir prioridade nativa do ClickUp pelo impacto e pelas dependências.
6. Registrar critérios de aceitação verificáveis e evidência esperada.
7. Concluir somente quando a Definition of Done estiver integralmente atendida.

## Nome

Usar `MACROÁREA | Verbo no infinitivo + resultado`.

Exemplo: `BACKEND | Implementar fila idempotente de varredura`.

## Corpo da tarefa

Usar esta estrutura:

```markdown
## História e valor
Como [persona], quero [capacidade], para [benefício mensurável].

## Escopo
- [entrega incluída]
- Fora de escopo: [limite relevante]

## Critérios de aceitação
- Dado [contexto], quando [ação], então [resultado observável].
- Cobrir estados de sucesso, erro, vazio e carregamento quando aplicável.
- Validar acessibilidade conforme WCAG 2.2 pt-BR quando houver interface ou conteúdo.

## Dependências
- [tarefa, decisão, contrato ou infraestrutura]

## Estimativas Fibonacci
- Complexidade: [1|2|3|5|8|13]
- Incerteza: [1|2|3|5|8|13]
- Esforço/tempo: [1|2|3|5|8|13]

## Evidência esperada
- [teste, captura, relatório, log, métrica, PR ou documentação]

## Definition of Done aplicável
- Código revisado e integrado quando houver código.
- Testes relevantes aprovados.
- Critérios de aceitação demonstrados.
- Segurança, privacidade, observabilidade e documentação atualizadas quando aplicável.
- Sem regressão de acessibilidade conhecida.
```

## Escala Fibonacci

- `1`: trivial, padrão conhecido, poucas horas.
- `2`: pequeno, risco baixo, até cerca de um dia.
- `3`: moderado, poucas integrações, até dois dias.
- `5`: relevante, múltiplas camadas ou até quatro dias.
- `8`: grande, risco elevado; preferir dividir antes da sprint.
- `13`: excessivo ou muito incerto; não entrar na sprint sem decomposição ou spike.

Os valores representam comparação relativa, não horas exatas. Refinar novamente quando a incerteza for `8` ou `13`.

## Prioridade

- `Urgente`: bloqueia o incremento, risco crítico ou entrega obrigatória imediata.
- `Alta`: essencial ao Sprint Goal, segurança, compliance ou caminho crítico.
- `Normal`: agrega valor sem bloquear o fluxo principal.
- `Baixa`: melhoria, otimização ou documentação não bloqueante.

Não usar prioridade para substituir dependências ou estimativas.

## Definition of Ready

Aceitar na sprint somente quando houver valor claro, escopo delimitado, critérios testáveis, dependências identificadas, estimativas Fibonacci e responsável possível. Itens `13` ou com decisão externa pendente devem ser divididos ou tratados como spike.

## Regras do OmniSight

- Referenciar critérios WCAG 2.2 pt-BR aplicáveis.
- Distinguir detecção automática de validação manual.
- Não prometer conformidade total com base apenas no scanner.
- Tratar URLs externas com proteção contra SSRF, limites e isolamento.
- Usar tags acadêmicas apenas quando houver relação real: `redes`, `computação e sociedade` ou `banco de dados`.
- Para CI/CD, considerar GitHub Actions; para cloud, considerar AWS conforme a arquitetura aprovada.
