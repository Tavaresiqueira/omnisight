# Camada visual do snapshot - 11/11/2026

## Escopo implementado

O coletor busca até 3 folhas CSS do mesmo hostname, via fetch_public_url com DNS
validado/pinado, redirects revalidados, limite de 256 KiB por folha e timeout de
3 s por fetch. CSS de CDN/outro hostname, imports e assets não são carregados.
O timeout de 90 s do pipeline continua cobrindo bloqueios, inclusive DNS.

O Chromium aplica o CSS coletado ao HTML e produz screenshots JPEG dos viewports
1280x800 e 390x844. Não há full-page screenshot nem emulação de dispositivo real:
o segundo perfil altera apenas o viewport. Cada imagem é limitada a 220 kB;
acima disso ela é omitida e o relatório informa o motivo. Snapshot total: 1 MiB.

As medições inspecionam até 5.000 elementos por viewport e apontam:
- rolagem horizontal do documento;
- elementos além das bordas horizontais;
- texto com possível corte em overflow hidden/clip;
- controles menores que 24 CSS px, sem concluir violação sem avaliar exceções.

Todos os achados geométricos são REVISAO, não falhas confirmadas WCAG. O relatório
mostra seletor e retângulo de até cinco exemplos por medição. A falta de indício
não é uma aprovação de conformidade. Não se mede zoom, comportamento de teclado,
fluxos, sobreposição geral nem qualidade estética com IA.

Atualização: axe é executado separadamente após cada redimensionamento, com
resultados em accessibilityChecks de desktop e mobile. A lista geral mantém o
resultado desktop para compatibilidade. Contraste segue desabilitado neste
snapshot incompleto; a repetição da engine não elimina os limites do conteúdo. O modo da extensão continua
sendo o caminho para analisar DOM/estilos da página real já carregada.

## Exibição, armazenamento e privacidade

As capturas fazem parte do snapshot privado do scan e são retornadas apenas pela
API autorizada por organização. São pixels do HTML do alvo e podem conter dados
sensíveis. Não são enviadas a serviços de visão/IA. A importação de JSON local da
extensão não aceita imagens neste formato. A política de retenção/exclusão do
projeto continua sendo um gate antes da operação pública em produção.

## Verificação

- Testes de coleta CSS: mesmo host, limite e MIME.
- Testes de geometria: DOM/retângulos simulados, sem avaliação de pixels reais.
- Testes de captura: mocks de Playwright, perfis, formato e tamanho.
- Validação da API rejeita MIME diferente de JPEG e base64/estrutura inválidos.
- Teste real de Chromium com fixture larga e alvo pequeno incluído no CI; não
  executado aqui por restrição do ambiente ao navegador.

Não houve screenshots reais geradas, Docker executado ou deploy nesta etapa.
