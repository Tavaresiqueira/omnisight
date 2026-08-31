# OmniSight — Especificação de Requisitos de Software

| Campo | Valor |
| --- | --- |
| Documento | Software Requirements Specification (SRS) |
| Produto | OmniSight |
| Versão | 0.1.0 |
| Estado | Rascunho para revisão |
| Última atualização | 2026-08-24 |
| Fonte oficial | Este arquivo versionado no repositório |
| Tarefa de origem | [ClickUp — Elaborar especificação de requisitos de software](https://app.clickup.com/t/86e2yc289) |

## 1. Objetivo

Este documento define os requisitos funcionais, não funcionais e as regras de negócio do OmniSight. Ele serve como contrato rastreável entre produto, design, engenharia, segurança, testes, operação e avaliação acadêmica.

A estrutura é inspirada em boas práticas de Software Requirements Specification. Os requisitos de acessibilidade usam como referência a [WCAG 2.2 em português do Brasil](https://www.w3c.br/traducoes/wcag/wcag22-pt-BR/).

## 2. Visão do produto

O OmniSight é um ecossistema para:

1. detectar barreiras de acessibilidade em páginas web;
2. priorizar e explicar os problemas encontrados;
3. ensinar como corrigi-los com exemplos aplicáveis;
4. demonstrar visualmente o impacto das barreiras;
5. simular diferentes condições de percepção e interação;
6. acompanhar a evolução de sites ao longo do tempo; e
7. adaptar páginas localmente às preferências de pessoas com necessidades de acessibilidade.

O produto atende dois grupos principais:

- **Desenvolvedores e organizações:** analisam, entendem, priorizam e corrigem barreiras.
- **Pessoas com necessidades de acessibilidade:** aplicam adaptações locais e reversíveis por meio da extensão.

## 3. Escopo

### 3.1 Incluído

- Aplicação web para cadastro de sites, execução de análises e consulta de resultados.
- Scanner automatizado de HTML, semântica e propriedades de acessibilidade.
- Classificação por severidade, confiança, categoria e princípio POUR.
- Score explicável de acessibilidade.
- Recomendações de correção em português do Brasil.
- Identificação visual dos elementos problemáticos.
- Simulações visuais e cognitivas de caráter educativo.
- Histórico, comparação e dashboard de evolução.
- Extensão de navegador com adaptações locais e reversíveis.
- Controles de segurança, privacidade, confiabilidade e observabilidade.

### 3.2 Fora do escopo inicial

- Certificar legalmente que um site está integralmente em conformidade.
- Substituir auditoria humana ou testes com pessoas com deficiência.
- Alterar permanentemente o código de sites de terceiros.
- Burlar autenticação, paywalls, CAPTCHA ou controles de acesso.
- Executar varreduras irrestritas de domínios inteiros no MVP.
- Corrigir automaticamente o código-fonte remoto de um site.

## 4. Stakeholders e personas

| Ator | Necessidade principal |
| --- | --- |
| Desenvolvedor | Localizar barreiras e receber orientação técnica acionável. |
| Designer | Compreender impacto visual, interação, foco, contraste e legibilidade. |
| Pessoa de QA | Reproduzir achados e validar correções com evidências. |
| Gestor ou empresa | Acompanhar risco, evolução, SLA e qualidade do site. |
| Pessoa com deficiência ou necessidade específica | Adaptar a navegação localmente às próprias preferências. |
| Administrador do OmniSight | Operar regras, segurança, capacidade e suporte do produto. |
| Docente ou avaliador | Verificar aplicação de Engenharia de Software, Redes, Banco de Dados e Computação e Sociedade. |

## 5. Premissas, restrições e dependências

### 5.1 Premissas

- O scanner automatizado encontra apenas parte das barreiras de acessibilidade.
- Alguns critérios exigem avaliação humana e/ou tecnologia assistiva.
- O MVP prioriza análise de uma página por solicitação.
- A interface e o conteúdo principal serão oferecidos em português do Brasil.
- GitHub Actions é a opção preferencial de CI/CD e AWS é a tendência de implantação, sujeitos a ADRs.

### 5.2 Restrições

- URLs fornecidas por usuários são entradas não confiáveis.
- O sistema não deve acessar redes privadas, metadados de nuvem ou destinos proibidos.
- Conteúdo de terceiros pode ser malicioso, instável ou protegido por direitos autorais.
- Simulações não representam integralmente a experiência de uma pessoa com deficiência.
- Preferências da extensão devem ser aplicadas somente no navegador do usuário.

### 5.3 Dependências

- Engine automatizada de acessibilidade versionada.
- Navegador headless isolado para páginas que dependam de JavaScript.
- Banco de dados para usuários, sites, scans, achados e snapshots.
- Fila de processamento para scans assíncronos.
- Infraestrutura de observabilidade, backup e recuperação.
- Manifest V3 e APIs suportadas pelos navegadores-alvo.

## 6. Convenções dos requisitos

### 6.1 Identificadores

- `RF-xxx`: requisito funcional.
- `RNF-CAT-xxx`: requisito não funcional por categoria.
- `RB-xxx`: regra de negócio.

### 6.2 Prioridade

- **Alta:** necessária ao MVP, ao caminho crítico, à segurança ou à conformidade.
- **Normal:** agrega valor sem bloquear o incremento principal.
- **Baixa:** evolução posterior ou otimização não bloqueante.

### 6.3 Verificação

Cada requisito deve ser validado por um ou mais métodos:

- teste automatizado;
- teste de integração ou contrato;
- teste E2E;
- inspeção manual;
- auditoria com tecnologia assistiva;
- teste de carga, segurança ou recuperação;
- revisão de documentação e evidências.

## 7. Requisitos funcionais

### RF-001 — Cadastrar conta e organização

**Prioridade:** Alta
**Descrição:** O sistema deve permitir a criação de conta, autenticação e associação a uma organização, mantendo os dados de organizações isolados.
**Aceitação:** Um usuário autenticado só consegue consultar e alterar sites, scans e relatórios da própria organização. Tentativas de acesso cruzado devem ser negadas e registradas.
**Verificação:** Testes de autenticação, autorização e isolamento multi-tenant.

### RF-002 — Cadastrar site para acompanhamento

**Prioridade:** Alta
**Descrição:** O usuário deve poder cadastrar um site por URL HTTPS válida e atribuir um nome de exibição.
**Aceitação:** URLs inválidas, não permitidas ou duplicadas devem produzir mensagens acessíveis e acionáveis, sem iniciar o scan.
**Verificação:** Testes de formulário, API, validação de URL e mensagens de erro.

### RF-003 — Validar destino com proteção contra SSRF

**Prioridade:** Alta
**Descrição:** Antes e durante cada acesso, o sistema deve validar esquema, host, DNS, endereço IP, porta e redirecionamentos.
**Aceitação:** O sistema bloqueia loopback, link-local, redes privadas, metadados de nuvem, esquemas não permitidos e redirecionamentos para destinos proibidos.
**Verificação:** Testes de segurança com destinos e cadeias de redirecionamento controlados.

### RF-004 — Solicitar scan assíncrono

**Prioridade:** Alta
**Descrição:** O usuário deve poder solicitar uma análise e receber um identificador de scan sem bloquear a interface.
**Aceitação:** O scan transita de forma idempotente entre `pendente`, `em execução`, `concluído`, `falhou` ou `cancelado`. Repetições não criam processamento duplicado indevido.
**Verificação:** Testes de API, fila, idempotência e concorrência.

### RF-005 — Coletar a página com limites

**Prioridade:** Alta
**Descrição:** O sistema deve coletar a página respeitando timeouts, tamanho máximo, quantidade de recursos, redirecionamentos e orçamento de execução.
**Aceitação:** Ao exceder um limite, o scan termina de forma controlada, registra a razão e apresenta orientação ao usuário.
**Verificação:** Testes com páginas lentas, grandes, recursivas e indisponíveis.

### RF-006 — Executar regras automatizadas versionadas

**Prioridade:** Alta
**Descrição:** O scanner deve executar uma versão identificável do conjunto de regras sobre o documento renderizado.
**Aceitação:** Todo scan concluído registra a versão da engine, das regras e os parâmetros relevantes para reprodução.
**Verificação:** Testes determinísticos sobre fixtures HTML e inspeção do snapshot persistido.

### RF-007 — Detectar barreiras essenciais

**Prioridade:** Alta
**Descrição:** O scanner deve detectar, quando tecnicamente automatizável, ao menos: imagens sem alternativa textual, campos sem rótulo, estrutura de headings inadequada, landmarks ausentes, idioma não definido, controles ou links sem nome acessível, contraste insuficiente e alvo mínimo inadequado.
**Aceitação:** Cada categoria possui fixtures positivas e negativas e referencia os critérios WCAG relacionados.
**Verificação:** Suíte automatizada de regras e revisão da matriz WCAG.

### RF-008 — Distinguir automação de avaliação humana

**Prioridade:** Alta
**Descrição:** Cada resultado deve indicar se foi detectado automaticamente, se requer revisão humana ou se é apenas informativo.
**Aceitação:** Nenhum achado inconclusivo é apresentado como violação comprovada.
**Verificação:** Revisão de catálogo de regras e testes da apresentação do resultado.

### RF-009 — Classificar achados

**Prioridade:** Alta
**Descrição:** Cada achado deve conter severidade, confiança, categoria, princípio POUR, critério WCAG aplicável e estado de resolução.
**Aceitação:** Os valores utilizados pertencem a enumerações versionadas e aparecem consistentemente na API e na interface.
**Verificação:** Testes de schema, persistência e interface.

### RF-010 — Calcular score explicável

**Prioridade:** Alta
**Descrição:** O sistema deve calcular um score geral e um detalhamento por princípio POUR com fórmula versionada.
**Aceitação:** O relatório explica quais fatores alteraram a nota; achados de baixa confiança ou não verificados não produzem penalização equivalente a violações confirmadas.
**Verificação:** Testes unitários da fórmula, casos-limite e snapshots de relatório.

### RF-011 — Explicar impacto e correção

**Prioridade:** Alta
**Descrição:** Para cada tipo de achado, o sistema deve informar o problema, pessoas potencialmente afetadas, orientação de correção e exemplo de código quando aplicável.
**Aceitação:** A explicação referencia o critério WCAG, evita linguagem capacitista e diferencia exigência normativa de recomendação.
**Verificação:** Revisão técnica, editorial e de acessibilidade do catálogo.

### RF-012 — Localizar o elemento problemático

**Prioridade:** Alta
**Descrição:** O relatório deve oferecer seletor, trecho ou identificador reproduzível e, quando possível, destacar o elemento em uma visualização segura da página.
**Aceitação:** O destaque associa o achado correto sem executar scripts não confiáveis no contexto da aplicação.
**Verificação:** Testes E2E com páginas fixture e análise de isolamento.

### RF-013 — Filtrar e consultar achados

**Prioridade:** Alta
**Descrição:** O usuário deve poder filtrar achados por severidade, categoria, princípio POUR, critério WCAG, confiança e estado.
**Aceitação:** Filtros podem ser usados por teclado, possuem nomes acessíveis e atualizam a contagem e a lista de resultados.
**Verificação:** Testes E2E, teclado e leitor de tela.

### RF-014 — Simular condições de visualização e leitura

**Prioridade:** Normal
**Descrição:** O sistema deve oferecer simulações de baixa visão, desfoque, contraste reduzido, tipos comuns de daltonismo, dificuldade de leitura e redução de movimento.
**Aceitação:** Cada simulação pode ser ativada isoladamente, desativada imediatamente e contém aviso de que é educativa e não reproduz integralmente uma deficiência.
**Verificação:** Testes visuais, reversibilidade e revisão de conteúdo.

### RF-015 — Persistir histórico de scans

**Prioridade:** Alta
**Descrição:** O sistema deve armazenar snapshots necessários para consultar análises anteriores de um site.
**Aceitação:** O usuário acessa data, score, contagens, versão das regras e estado de cada scan autorizado.
**Verificação:** Testes de persistência, autorização e paginação.

### RF-016 — Comparar evolução

**Prioridade:** Alta
**Descrição:** O usuário deve poder comparar dois scans do mesmo site e identificar achados novos, persistentes, corrigidos ou alterados.
**Aceitação:** A comparação usa identificadores estáveis ou uma estratégia documentada de correspondência e informa quando não há confiança suficiente.
**Verificação:** Testes de diff sobre snapshots conhecidos.

### RF-017 — Exibir dashboard acessível

**Prioridade:** Alta
**Descrição:** O dashboard deve apresentar score atual, quantidade de problemas, distribuição por categoria, histórico, evolução e correções.
**Aceitação:** Toda informação visual possui alternativa textual ou tabular equivalente e não depende apenas de cor.
**Verificação:** Testes de dados, teclado, zoom/reflow e acessibilidade automatizada.

### RF-018 — Gerenciar preferências da extensão

**Prioridade:** Normal
**Descrição:** A extensão deve permitir configurar tamanho e espaçamento de texto, contraste, tamanho de alvos, cursor, destaque de links, redução de animações e zoom.
**Aceitação:** Preferências são acessíveis por teclado, persistidas localmente e não enviadas ao servidor sem consentimento explícito.
**Verificação:** Testes de extensão, armazenamento local e permissões.

### RF-019 — Aplicar Modo Idoso reversível

**Prioridade:** Normal
**Descrição:** A extensão deve oferecer um perfil combinado para aumentar legibilidade e facilidade de interação.
**Aceitação:** Ativar e desativar restaura a página sem recarregamento obrigatório e sem alterar conteúdo ou ações de negócio.
**Verificação:** Testes E2E em páginas representativas e revisão manual.

### RF-020 — Persistir regras por domínio

**Prioridade:** Normal
**Descrição:** O usuário deve poder salvar preferências por domínio, pausar adaptações e cadastrar exceções.
**Aceitação:** Regras usam o escopo mínimo necessário, são editáveis e podem ser removidas pelo usuário.
**Verificação:** Testes de correspondência de domínio e persistência local.

### RF-021 — Excluir dados sob solicitação

**Prioridade:** Alta
**Descrição:** Usuários autorizados devem poder solicitar exclusão de site, scans e dados pessoais conforme a política de retenção.
**Aceitação:** A exclusão respeita dependências, produz confirmação, registra auditoria mínima e remove dados dos sistemas ativos dentro do prazo definido.
**Verificação:** Testes de autorização, exclusão, retenção e auditoria.

### RF-022 — Registrar eventos operacionais e de auditoria

**Prioridade:** Alta
**Descrição:** O sistema deve registrar eventos relevantes de autenticação, autorização, scans, falhas, mudanças de regras e exclusões sem armazenar conteúdo sensível desnecessário.
**Aceitação:** Eventos possuem correlação, horário, ator ou serviço e resultado, com acesso restrito.
**Verificação:** Testes de geração, redação de dados e controle de acesso aos logs.

## 8. Requisitos não funcionais

As metas abaixo são baselines do MVP. Alterações devem ser registradas por ADR e refletidas nos testes, dashboards e SLIs.

### 8.1 Acessibilidade

#### RNF-ACC-001 — Conformidade da interface

**Prioridade:** Alta
**Requisito:** Os fluxos críticos da aplicação web e da extensão devem buscar conformidade WCAG 2.2 nível AA.
**Métrica:** Zero violações críticas ou sérias conhecidas nos testes automatizados adotados; conclusão integral por teclado dos fluxos críticos; revisão manual de foco, zoom de 200%, reflow a 320 CSS px, mensagens de status e nomes acessíveis.
**Verificação:** Auditoria automatizada, checklist WCAG, teclado e NVDA.

#### RNF-ACC-002 — Não dependência de automação

**Prioridade:** Alta
**Requisito:** Declarações de acessibilidade e conformidade devem combinar testes automáticos e avaliação humana.
**Métrica:** Todo relatório identifica cobertura, limitações e itens que requerem revisão manual.
**Verificação:** Revisão de relatórios e catálogo de regras.

#### RNF-ACC-003 — Conteúdo compreensível

**Prioridade:** Alta
**Requisito:** Mensagens, explicações e instruções devem usar português do Brasil claro, consistente e não capacitista.
**Métrica:** Glossário consistente; erros incluem causa e ação recomendada; nenhum estado depende somente de cor ou ícone.
**Verificação:** Revisão editorial e testes de usabilidade.

### 8.2 Segurança

#### RNF-SEC-001 — Controle de SSRF

**Prioridade:** Alta
**Requisito:** Todo acesso server-side iniciado por URL do usuário deve aplicar validação antes da conexão e após cada redirecionamento.
**Métrica:** 100% dos casos da suíte de destinos proibidos bloqueados; nenhum acesso a redes privadas, loopback, link-local ou metadados de nuvem.
**Verificação:** Testes automatizados e revisão de arquitetura.

#### RNF-SEC-002 — Isolamento do navegador

**Prioridade:** Alta
**Requisito:** Conteúdo remoto deve executar em ambiente efêmero e isolado, sem credenciais de aplicação e com privilégios mínimos.
**Métrica:** Credenciais ausentes no ambiente de renderização; filesystem e rede limitados; ambiente descartado ao final.
**Verificação:** Testes de isolamento e inspeção de infraestrutura.

#### RNF-SEC-003 — Proteção de dados em trânsito e repouso

**Prioridade:** Alta
**Requisito:** Tráfego externo deve usar TLS e dados sensíveis persistidos devem usar mecanismos de criptografia da plataforma.
**Métrica:** TLS 1.2 ou superior; bancos, backups e objetos sensíveis criptografados; segredos fora do repositório.
**Verificação:** Varredura de configuração e infraestrutura como código.

#### RNF-SEC-004 — Proteção contra abuso

**Prioridade:** Alta
**Requisito:** APIs e solicitações de scan devem aplicar autenticação, autorização, limites e quotas.
**Métrica:** Limites definidos por usuário e organização; respostas `429` observáveis; nenhuma operação privilegiada sem autorização explícita.
**Verificação:** Testes de rate limit, autorização e carga abusiva.

### 8.3 Privacidade e LGPD

#### RNF-PRI-001 — Minimização

**Prioridade:** Alta
**Requisito:** O sistema deve coletar e persistir apenas dados necessários à análise, histórico e operação.
**Métrica:** Inventário de dados com finalidade, base, retenção e acesso; conteúdo bruto de terceiros não é persistido quando um resumo técnico for suficiente.
**Verificação:** Revisão de modelo de dados e fluxo de informações.

#### RNF-PRI-002 — Retenção e exclusão

**Prioridade:** Alta
**Requisito:** Categorias de dados devem possuir prazo de retenção configurado e processo verificável de exclusão.
**Métrica:** Exclusão dos sistemas ativos dentro do prazo publicado; expiração de backups conforme ciclo documentado.
**Verificação:** Testes de lifecycle e auditoria de retenção.

#### RNF-PRI-003 — Preferências locais da extensão

**Prioridade:** Alta
**Requisito:** Preferências de adaptação devem permanecer locais por padrão.
**Métrica:** Nenhuma telemetria ou sincronização de preferências sem consentimento explícito, granular e revogável.
**Verificação:** Inspeção de permissões, tráfego e armazenamento da extensão.

### 8.4 Desempenho e capacidade

#### RNF-PER-001 — Latência da aplicação

**Prioridade:** Normal
**Requisito:** Operações síncronas que não executam scan devem responder rapidamente sob carga nominal.
**Métrica:** p95 inferior a 500 ms e p99 inferior a 1 s para leitura e escrita simples, medidos no backend e excluindo latência do cliente.
**Verificação:** Teste de carga em ambiente representativo.

#### RNF-PER-002 — Tempo de scan do MVP

**Prioridade:** Alta
**Requisito:** Uma análise de página deve finalizar dentro de orçamento conhecido.
**Métrica:** p95 inferior a 120 s para páginas que respeitem os limites publicados; timeout máximo de 180 s.
**Verificação:** Teste de carga com conjunto representativo de páginas controladas.

#### RNF-PER-003 — Degradação controlada

**Prioridade:** Alta
**Requisito:** Saturação de workers não deve indisponibilizar autenticação, dashboard ou consulta de resultados.
**Métrica:** Fila aplica backpressure; novas solicitações recebem estado ou erro controlado; APIs de leitura permanecem dentro do SLO.
**Verificação:** Teste de estresse e falha de dependências.

### 8.5 Confiabilidade, disponibilidade e recuperação

#### RNF-REL-001 — Disponibilidade

**Prioridade:** Alta
**Requisito:** A aplicação deve possuir objetivo inicial de disponibilidade mensal.
**Métrica:** SLO de 99,5% para autenticação, cadastro de URL e consulta de resultados, excluindo manutenção comunicada.
**Verificação:** Métricas de disponibilidade e cálculo mensal de error budget.

#### RNF-REL-002 — Entrega idempotente

**Prioridade:** Alta
**Requisito:** Reexecuções e retries não devem duplicar scans, achados ou efeitos externos indevidamente.
**Métrica:** Chaves idempotentes e transições válidas cobertas por testes de concorrência.
**Verificação:** Testes de retry, redelivery e corrida.

#### RNF-REL-003 — Backup e recuperação

**Prioridade:** Alta
**Requisito:** Dados persistentes devem possuir backup e procedimento testado de restauração.
**Métrica:** RPO inicial de 24 h e RTO inicial de 4 h; restauração testada ao menos uma vez por ciclo de entrega acadêmica.
**Verificação:** Evidência de restore e medição de RPO/RTO.

### 8.6 Observabilidade

#### RNF-OBS-001 — Correlação ponta a ponta

**Prioridade:** Alta
**Requisito:** Requisições, jobs e scans devem compartilhar identificadores de correlação.
**Métrica:** Um operador consegue navegar de uma falha exibida ao usuário para logs, métricas e execução do worker correspondente.
**Verificação:** Teste operacional e inspeção de traces.

#### RNF-OBS-002 — Telemetria útil e segura

**Prioridade:** Alta
**Requisito:** Logs e métricas devem apoiar diagnóstico sem expor segredos, tokens ou conteúdo pessoal desnecessário.
**Métrica:** Redação testada; alertas para erro, fila, latência, capacidade e falhas de scan; retenção definida.
**Verificação:** Testes de logging, revisão de dashboards e simulação de incidente.

### 8.7 Compatibilidade e portabilidade

#### RNF-COM-001 — Navegadores da aplicação web

**Prioridade:** Normal
**Requisito:** A aplicação deve suportar as duas versões estáveis mais recentes de Chrome, Edge e Firefox.
**Métrica:** Fluxos críticos aprovados na matriz de navegadores definida para a release.
**Verificação:** Testes E2E cross-browser.

#### RNF-COM-002 — Extensão

**Prioridade:** Normal
**Requisito:** A primeira versão da extensão deve usar Manifest V3 e declarar apenas permissões necessárias.
**Métrica:** Revisão de permissões sem curingas injustificados; testes na versão-alvo do Chrome e, quando compatível, Edge.
**Verificação:** Inspeção do manifesto e testes de instalação controlada.

### 8.8 Manutenibilidade e testabilidade

#### RNF-MAN-001 — Contratos versionados

**Prioridade:** Alta
**Requisito:** APIs, regras, fórmula de score e schema de snapshots devem ser versionados.
**Métrica:** Mudanças incompatíveis exigem migração ou nova versão e possuem testes de contrato.
**Verificação:** CI e revisão de ADRs, schemas e migrations.

#### RNF-MAN-002 — Quality gates

**Prioridade:** Alta
**Requisito:** Pull requests devem executar gates proporcionais ao risco.
**Métrica:** Build, lint, testes focados, segurança de dependências e verificações de acessibilidade aplicáveis aprovados antes do merge.
**Verificação:** GitHub Actions e regras do repositório.

#### RNF-MAN-003 — Reprodutibilidade dos achados

**Prioridade:** Alta
**Requisito:** Um achado deve guardar contexto suficiente para reprodução sem reter dados excessivos.
**Métrica:** Regra, versão, URL normalizada, seletor ou referência, evidência técnica e horário disponíveis para usuários autorizados.
**Verificação:** Testes com fixtures e auditoria do modelo de dados.

### 8.9 Usabilidade e ética

#### RNF-USA-001 — Feedback de estado

**Prioridade:** Alta
**Requisito:** A interface deve comunicar carregamento, progresso, sucesso, vazio, falha e ação de recuperação.
**Métrica:** Todos os fluxos críticos possuem os seis estados quando aplicáveis e mensagens de status perceptíveis por tecnologia assistiva.
**Verificação:** Testes E2E e WCAG 4.1.3.

#### RNF-ETH-001 — Comunicação responsável

**Prioridade:** Alta
**Requisito:** O produto deve evitar representar simulações como equivalentes à vivência de pessoas com deficiência ou o score como certificação.
**Métrica:** Avisos presentes no simulador e no relatório; nenhum texto de produto afirma garantia de conformidade integral.
**Verificação:** Revisão de conteúdo e testes de interface.

## 9. Regras de negócio

### RB-001 — Conformidade não é inferida apenas pelo score

O score é um indicador interno e explicável. Ele não constitui certificação e não pode, isoladamente, produzir uma declaração de conformidade WCAG.

### RB-002 — Achado inconclusivo não é violação confirmada

Resultados que dependem de contexto ou julgamento humano devem ser classificados para revisão, sem penalização equivalente à de um erro confirmado.

### RB-003 — Mesma página, versões distintas

Comparações devem considerar URL normalizada, viewport, versão das regras e parâmetros do scan. Diferenças relevantes devem aparecer no relatório.

### RB-004 — Severidade e confiança são dimensões distintas

Um impacto potencialmente crítico pode ter baixa confiança. A interface e a fórmula não devem confundir essas dimensões.

### RB-005 — Adaptações são locais e reversíveis

A extensão não modifica o código-fonte remoto, não realiza ações de negócio e deve permitir restauração imediata da apresentação original.

### RB-006 — Menor privilégio

Usuários, serviços, workers e extensão recebem apenas permissões necessárias ao caso de uso.

### RB-007 — Exclusão respeita retenção e auditoria mínima

Dados removidos deixam os sistemas ativos dentro do prazo publicado; evidência mínima da solicitação pode ser mantida quando necessária e justificada.

## 10. Jornadas críticas

### JC-001 — Executar e consultar um scan

1. Usuário autenticado cadastra uma URL.
2. Sistema valida a URL e cria o scan.
3. Worker coleta e analisa a página em ambiente isolado.
4. Sistema persiste score, achados e versões.
5. Usuário recebe o estado e consulta o relatório acessível.
6. Usuário filtra achados e acessa explicações e evidências.

### JC-002 — Acompanhar evolução

1. Usuário seleciona um site cadastrado.
2. Sistema lista scans autorizados.
3. Usuário escolhe duas análises.
4. Sistema apresenta novos problemas, persistências e correções.
5. Dashboard atualiza tendências e alternativas textuais.

### JC-003 — Aplicar adaptação local

1. Usuário abre o painel da extensão.
2. Configura ou seleciona um perfil.
3. Extensão aplica adaptações à página atual.
4. Usuário salva a regra para o domínio, se desejar.
5. Usuário pausa ou remove a adaptação e a página é restaurada.

## 11. Entidades conceituais

| Entidade | Responsabilidade |
| --- | --- |
| Usuário | Identidade, autenticação e preferências autorizadas. |
| Organização | Limite de isolamento e propriedade dos dados. |
| Site | URL normalizada e metadados de acompanhamento. |
| Scan | Solicitação, estado, parâmetros, versões, tempos e resultado agregado. |
| Achado | Regra, elemento, impacto, severidade, confiança, WCAG e estado. |
| Regra de scanner | Definição versionada de detecção e orientação. |
| Snapshot | Dados necessários para histórico e comparação. |
| Evento de auditoria | Registro mínimo de ação relevante e resultado. |
| Preferência da extensão | Configuração local por perfil ou domínio. |

Relacionamentos e atributos físicos serão definidos no modelo de dados e nas migrations, sem antecipar a tecnologia neste documento.

## 12. Matriz inicial de rastreabilidade

| Capacidade | Requisitos | Macroáreas do backlog | Evidência principal |
| --- | --- | --- | --- |
| Scanner automático | RF-002 a RF-009 | BACKEND, SEGURANÇA, SCANNER | Fixtures, integração e relatório de scan |
| Score e severidade | RF-009 e RF-010 | SCORE | Testes da fórmula e breakdown POUR |
| Explicação e correção | RF-011 | CONTEÚDO, COMPLIANCE | Catálogo revisado e exemplos |
| Identificação visual | RF-012 e RF-013 | VISUAL, FRONTEND | Testes E2E e isolamento |
| Simulador | RF-014, RNF-ETH-001 | SIMULADOR, DESIGN | Testes visuais e aviso educativo |
| Histórico e dashboard | RF-015 a RF-017 | DASHBOARD, BANCO DE DADOS | Snapshots, diff e gráficos acessíveis |
| Extensão adaptativa | RF-018 a RF-020 | EXTENSÃO | Testes Manifest V3 e armazenamento local |
| Privacidade e exclusão | RF-021, RNF-PRI-* | PRIVACIDADE, BANCO DE DADOS | Testes de lifecycle e inventário |
| Operação segura | RF-022, RNF-SEC-*, RNF-REL-*, RNF-OBS-* | DEVOPS, REDES, RELIABILITY | CI/CD, métricas, runbooks e restore |

A [matriz WCAG 2.2, score e adaptações](../accessibility/wcag-score-adaptation-matrix.html) detalha os critérios observados pelo scanner, a proposta versionável de pontuação e os limites das adaptações locais da extensão.

## 13. Critérios de aceite da SRS

- Todas as sete capacidades principais possuem requisitos funcionais rastreáveis.
- Todo RNF contém métrica verificável e método de validação.
- Requisitos de acessibilidade referenciam a WCAG 2.2 e distinguem automação de avaliação humana.
- Segurança de URL, isolamento, privacidade, banco de dados, CI/CD e operação estão cobertos.
- Não há promessa de certificação automática ou conformidade integral baseada somente no scanner.
- IDs são únicos e usados nas tarefas, testes, ADRs e pull requests relacionados.
- Mudanças de escopo atualizam este documento e a matriz de rastreabilidade.

## 14. Glossário

| Termo | Definição |
| --- | --- |
| Achado | Resultado de uma regra automática, revisão humana ou informação associada a uma página. |
| POUR | Princípios Perceptível, Operável, Compreensível e Robusto. |
| Scan | Execução versionada de coleta e análise de uma página. |
| Score | Indicador explicável do conjunto de achados; não é certificação. |
| SLI | Medida observada de confiabilidade ou desempenho. |
| SLO | Objetivo definido para um SLI. |
| SLA | Compromisso de nível de serviço acordado. |
| SSRF | Requisição server-side induzida para acessar destinos não autorizados. |
| WCAG | Diretrizes de Acessibilidade para Conteúdo Web do W3C. |

## 15. Referências

- [WCAG 2.2 — tradução em português do Brasil](https://www.w3c.br/traducoes/wcag/wcag22-pt-BR/)
- [WCAG 2.2 — recomendação oficial do W3C](https://www.w3.org/TR/WCAG22/)
- [Repositório OmniSight](https://github.com/Tavaresiqueira/omnisight)
- [Backlog de implementação no ClickUp](https://app.clickup.com/90171459576/v/l/li/901716124782)

## 16. Histórico de alterações

| Versão | Data | Alteração |
| --- | --- | --- |
| 0.1.0 | 2026-08-24 | Estrutura inicial, requisitos do MVP e matriz de rastreabilidade. |
