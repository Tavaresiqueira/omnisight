# OmniSight - extensão experimental 0.1.0

Chrome ou Edge de computador, Manifest V3. Não publicada nas lojas. Não é uma
extensão instalável no Chrome do iPhone ou no Safari iOS nesta versão.

1. Extraia o ZIP da extensão numa pasta permanente.
2. Abra chrome://extensions ou edge://extensions.
3. Ative Modo do desenvolvedor > Carregar sem compactação > escolha essa pasta.
4. Abra o seu site, faça login normalmente e navegue ao estado que quer testar.
5. Clique no ícone OmniSight. Uma aba da extensão acompanha o scan da aba original.
6. Baixe o JSON e importe no dashboard em “Importar diagnóstico da extensão”.

A extensão requer apenas activeTab e scripting. Não há host_permissions,
content_scripts automáticos, cookies, debugger, tabs ou acesso ao histórico.
O acesso à aba é temporário, concedido pela ação explícita do usuário.

Axe-core 4.13.0 é distribuído localmente, com tradução pt-BR e licença MPL 2.0.
A análise acontece no isolated world do documento principal. Usa o DOM e estilos
renderizados, com contraste habilitado; inconclusões continuam como revisão.
Não faz login por você, percorre outras rotas, lê backend, simula teclado,
acessa frames de outras origens ou certifica conformidade WCAG.

A aplicação não envia automaticamente o relatório a servidores. O download
exclui trechos HTML por padrão. Se habilitar evidências HTML, revise os dados
antes de compartilhar: podem conter valores ou atributos sensíveis do DOM.
URL (sem query/hash), título, seletores e mensagens também podem ser sensíveis.
Não são capturados cookies, localStorage, tokens de rede ou screenshots.

O resultado importado no dashboard fica apenas em memória e é identificado como
arquivo externo não verificado. Não altera snapshots produzidos pelo servidor.

Se a análise exceder 30 segundos, recarregue a aba original antes de repetir.
Se navegar ou fechar a aba original durante o scan, a análise pode falhar.
As páginas internas do navegador e suas lojas de extensões não permitem injeção.

Validação: testes de contrato/DOM simulado. A instalação e execução real como
extensão ainda precisam ser verificadas em Chrome/Edge no ambiente de destino.
