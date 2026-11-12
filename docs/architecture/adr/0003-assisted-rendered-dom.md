# ADR 0003 - Análise assistida no navegador do usuário

Data: 11/11/2026. Estado: implementação experimental; instalação real pendente.

## Por que este caminho

O servidor não tem a sessão já aberta no navegador do usuário. Copiar cookies ou
executar login arbitrário no servidor introduziria outra fronteira de privacidade
e segurança. A extensão pode usar o DOM e CSS que o navegador já renderizou,
com o usuário navegando e concedendo acesso à aba explicitamente.

A solução tem três caminhos complementares:

1. **URL pública / worker:** coleta SSRF-safe, snapshot HTML isolado e diagnóstico
   persistido. Mantém o fluxo do ADR 0002 e os limites declarados de CSS/JS.
2. **Aba aberta / extensão:** axe-core sobre o documento renderizado e seus estilos,
   incluindo contraste onde determinável, com estado de revisão preservado.
   Exportação local, sem envio automático da sessão ou relatório ao servidor.
3. **Jornadas Playwright (planejado):** percorrer somente rotas e estados de teste
   definidos pelo proprietário. Usar fixtures e ambiente de teste para não
   clicar em ações destrutivas ou submeter formulários reais. Consolidação de
   vários estados e rotas ainda não está implementada.

## Entrega experimental

- Manifest V3, activeTab + scripting, sem acesso permanente a hosts, cookies,
  debugger, histórico ou scripts automáticos por domínio.
- A ação no ícone abre uma tela própria da extensão e analisa a aba original.
- Engine e tradução empacotadas; execução ISOLATED; somente documento principal.
- Contraste habilitado no DOM real; iframe:false; erros e incomplete não viram
  aprovações. Não há garantia de cobertura de shadow DOM fechado ou canvas.
- URL exportada sem query/hash; HTML de evidências excluído por padrão. Títulos,
  caminho, seletores e mensagens podem conter dados pessoais mesmo sem HTML.
- O arquivo importado é validado, limitado a 1 MiB, renderizado como texto e
  identificado como origem não verificada. Não cria scan no backend, não altera
  snapshots do servidor e não é armazenado no histórico nesta etapa.
- O arquivo não tem assinatura: não se pode tratar a engine ou origem declarada
  no JSON como prova de execução confiável. A validação é de contrato e tamanho.

## Criatividade com escopo controlado

O próximo avanço será um “roteiro de estados”: o proprietário abre login, menu,
modal e formulário no próprio ambiente de teste; cada estado gera um diagnóstico
comparável. Depois, o mesmo roteiro pode virar teste Playwright no CI. A aplicação
não vai inventar cliques ou explorar contas reais automaticamente. Nenhuma dessas
funções de gravação, multiestado ou varredura completa está concluída hoje.

## Verificação

Testes do scanner usam DOM simulado e engine simulada para contrato e opções.
Testes do importador verificam conteúdo malformado, limites, ausência de envio e
exibição sem executar HTML. Empacotamento confere permissões e arquivos.
Não substituem instalação/executarScript real em Chrome/Edge e testes de axe no
Chromium. Esses gates permanecem necessários antes de distribuir como versão final.

Referências primárias:
- https://developer.chrome.com/docs/extensions/reference/api/scripting
- https://developer.chrome.com/docs/extensions/develop/concepts/activeTab
- https://github.com/dequelabs/axe-core/blob/develop/doc/API.md
