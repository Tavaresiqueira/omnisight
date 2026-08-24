# Evidências UML do OmniSight

Estes diagramas apoiam o entendimento do negócio e o refinamento do backlog. Eles representam a
visão conceitual definida na SRS e não fixam framework, banco de dados ou provedor de nuvem.

| Diagrama | Finalidade ágil | Rastreabilidade principal |
| --- | --- | --- |
| [Caso de uso](use-case.puml) | Delimitar atores, escopo e capacidades que originam histórias de usuário | RF-001 a RF-022; JC-001 a JC-003 |
| [Classes](class-diagram.puml) | Visualizar entidades, responsabilidades e relações conceituais | Seção 11; RF-001, RF-002, RF-004, RF-009, RF-015, RF-018 e RF-022 |
| [Sequência do scan](scan-sequence.puml) | Refinar mensagens, limites de confiança e ordem temporal do scan | JC-001; RF-003 a RF-012; RNF-SEC-001/002 e RNF-REL-002 |
| [Atividade do scan](scan-activity.puml) | Explicitar decisões, falhas controladas e revisão humana | JC-001; RF-003 a RF-010; RB-001 e RB-002 |

## Evidência e validação

- Fonte: arquivos PlantUML textuais e versionados neste diretório.
- Referência funcional: `docs/requirements/software-requirements-specification.md` versão 0.1.0.
- Escopo: modelo de análise de uma página, histórico e extensão adaptativa do MVP.
- Limitação: os diagramas documentam requisitos e interações; não provam implementação nem
  conformidade WCAG.

Validar a sintaxe com PlantUML instalado:

```bash
plantuml -checkonly docs/architecture/uml/*.puml
```

Gerar SVGs acessíveis como apoio visual, preservando os fontes como artefato oficial:

```bash
plantuml -tsvg docs/architecture/uml/*.puml
```

Após mudanças relevantes em requisitos, atualizar o diagrama afetado e sua rastreabilidade na mesma
entrega.
