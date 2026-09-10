# ADR 0001 — Monólito modular com worker de scan isolado

**Estado:** Aceita

**Data:** 2026-09-10

**Rastreabilidade:** ClickUp `86e2v67bv`; RF-001 a RF-022; RNF-SEC-001 a RNF-SEC-004; RNF-REL-001; RNF-MAN-001

## Contexto

O MVP de um mês precisa entregar autenticação, isolamento por organização,
cadastro de sites, execução assíncrona de scans, achados versionados e histórico.
O scanner acessa URLs não confiáveis e, portanto, cria uma fronteira de SSRF,
redirecionamento, consumo de recursos e conteúdo hostil diferente da interface e
das regras de negócio. A equipe ainda não selecionou framework, provedor ou banco.

## Decisão

Adotar um **monólito modular** para o plano de controle e um **worker isolado** para
coleta e análise. A integração ocorre por trabalho assíncrono versionado. Esta
decisão fixa limites e responsabilidades, mas permanece neutra quanto a linguagem,
framework, nuvem e produto de fila ou banco.

O [diagrama de componentes](../uml/component-diagram.puml) registra frontend, API,
worker, fila, banco, storage, navegador isolado e extensão, além de suas integrações.

### Módulos do plano de controle

| Módulo | Responsabilidade | Não pode fazer |
| --- | --- | --- |
| Identidade e organizações | Autenticação, associação, papéis e isolamento. | Confiar em `organization_id` enviado sem autorização server-side. |
| Catálogo de sites | Validar, normalizar e autorizar URLs cadastradas. | Buscar a URL diretamente no processo da API. |
| Orquestração de scans | Criar, cancelar, consultar estado e publicar trabalhos. | Executar navegador ou carregar conteúdo remoto. |
| Resultados | Persistir snapshots, achados, evidências mínimas e comparações. | Aceitar resultado sem versão e vínculo com o scan. |
| Catálogo de regras | Versionar regra, referência, cobertura e orientação. | Alterar retroativamente snapshots existentes. |
| Auditoria | Registrar ações relevantes, ator, organização e resultado. | Armazenar segredos ou corpos de páginas indiscriminadamente. |

### Worker de scan

O worker recebe apenas identificador do scan e configuração mínima, busca a URL já
normalizada, revalida cada resolução DNS e redirecionamento, aplica política de
egress, limites de tempo/tamanho/recursos e executa as regras versionadas. Ele não
recebe credenciais da aplicação, acesso administrativo nem permissão ampla ao banco.
Resultados retornam por contrato autenticado e idempotente.

## Fluxo e estados

1. A API autoriza organização e usuário, valida a URL e cria o scan como `queued`.
2. Um trabalho contém ID do scan, versão do contrato e parâmetros permitidos.
3. O worker assume o trabalho, muda para `running` de forma idempotente e coleta em
   ambiente isolado.
4. Evidências e achados são enviados em lotes limitados, com versões explícitas.
5. O plano de controle conclui como `completed`, `failed`, `cancelled` ou `expired`.
6. Tentativas repetidas usam chave de idempotência e não duplicam snapshots.

## Fronteiras de confiança

| Fronteira | Controle mínimo |
| --- | --- |
| Cliente → API | Autenticação, autorização por organização, validação de schema, rate limit e auditoria. |
| API → fila | Contrato versionado, payload mínimo, integridade e idempotência. |
| Worker → internet | Allow/deny de rede, bloqueio de destinos privados e metadata, revalidação de DNS/redirecionamentos e orçamento de recursos. |
| Worker → resultados | Identidade própria de menor privilégio, vínculo obrigatório ao scan e limites de tamanho. |
| Organização → persistência | Escopo server-side em toda consulta, chaves e índices coerentes e testes de isolamento. |

## Persistência conceitual

Uma base transacional mantém organizações, membros, sites, scans, snapshots,
achados, versões de regras e eventos de auditoria. Evidências grandes, se necessárias,
ficam fora das tabelas transacionais e são referenciadas por identificador opaco,
com expiração e autorização equivalentes. A escolha física será registrada em ADR
posterior junto às migrations.

## Consequências

### Benefícios

- reduz complexidade operacional no MVP sem misturar execução hostil com a API;
- mantém transações e isolamento organizacional em um único plano de controle;
- permite escalar workers separadamente e interromper scans abusivos;
- preserva liberdade de escolha tecnológica.

### Custos e riscos

- requer contrato assíncrono, idempotência e observabilidade desde o início;
- falhas parciais exigem expiração, retry limitado e reconciliação;
- modularidade depende de testes e revisão para não degradar em acoplamento interno.

## Alternativas consideradas

- **Microserviços por domínio:** adiados; aumentam superfície operacional antes de
  haver escala ou equipes que justifiquem a separação.
- **Scanner no processo da API:** rejeitado; amplia impacto de SSRF, travamentos e
  consumo de recursos sobre fluxos autenticados.
- **Aplicação síncrona sem fila:** rejeitada; scans têm latência e falhas externas
  incompatíveis com o ciclo de uma requisição interativa.

## Evidência de validação

- diagramas de sequência e atividade permanecem coerentes com a fronteira escolhida;
- testes futuros cobrem isolamento entre organizações, SSRF, redirects, idempotência,
  expiração e retries;
- qualquer implementação deve documentar os componentes físicos em ADRs adicionais
  antes de introduzir dependências de framework ou provedor.
