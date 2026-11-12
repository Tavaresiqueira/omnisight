# Coleta HTML limitada

`identity.crawler.crawl` reutiliza `fetch_public_url`, que revalida DNS e redirecionamentos e fixa a conexão no IP público validado. O crawler permite apenas o hostname inicial (subdomínios diferentes também são excluídos), HTTPS/443, até 100 páginas e profundidade até 5. Os padrões são 10 páginas, profundidade 1 e orçamento de 30 segundos. Concorrência: uma requisição por vez. Cada resposta continua limitada a 2 MiB pela camada de transporte.

Fragmentos são removidos; hostname e porta padrão são normalizados; query strings são preservadas. Links com credenciais, HTTP, portas alternativas ou outros hosts não são seguidos. Respostas diferentes de HTTP 200, conteúdo não HTML e conteúdo comprimido são rejeitados. Não são carregados scripts, imagens, iframes ou folhas de estilo. O HTML é interpretado como UTF-8 com substituição de bytes inválidos nesta primeira versão.

## Validação

Nove testes unitários usam respostas controladas, sem chamadas externas. Cobrem limites, URLs repetidas, domínio, redirects, timeout e conteúdo não suportado. O restante da suíte verifica a política SSRF e o isolamento organizacional.

## Pendências para execução em produção

O orçamento é conferido antes e depois das requisições; não substitui um supervisor de processo. Resolução DNS e operações bloqueantes precisam de término forçado no worker isolado. Este módulo ainda não está conectado ao consumidor da fila nem à engine de acessibilidade. Coleta HTML não representa avaliação WCAG nem produz score. A tarefa do ClickUp permanece em andamento até a integração e validação operacional.
