# Extensão renderizada - evidências de 11/11/2026

- 4 testes Node: permissões mínimas; contrato do scanner com DOM/engine simulados;
  contagem e amostras; query/hash removidos; contraste não desabilitado; exportação
  sem HTML por padrão; prevenção de segunda execução concorrente.
- 15 testes Vitest do frontend: autenticação, sites, scan, relatório, contrato de
  importação, rejeição de arquivo inválido e renderização sem executar HTML.
- Build Next.js + TypeScript concluído; prebuild produz o ZIP da extensão e guia.
- Arquivo ZIP conferido: manifest e scripts presentes, sem host_permissions ou
  content_scripts automáticos; o export estático contém o mesmo ZIP gerado.
- A execução de verdade da extensão/axe no Chrome/Edge NÃO foi validada aqui.
  Esses testes não medem contraste real nem cobertura do navegador.

## Checklist em Chrome/Edge de computador

1. Carregar o ZIP extraído sem compactação; conferir duas permissões no manifest.
2. Em página de teste, injetar botão sem nome e imagem sem alt; executar pelo ícone.
3. Confirmar que a aba de diagnóstico abre e aponta essas condições.
4. Conferir contraste em fixture com cores conhecidas e verificar incomplete.
5. Abrir site de teste com login e confirmar que o relatório não precisa receber
   cookies ou credenciais. Não usar dados pessoais reais na fixture.
6. Baixar sem HTML e conferir que os trechos estão vazios; habilitar HTML apenas
   em ambiente de teste e verificar a opção explicitamente.
7. Importar o JSON no dashboard, conferir o aviso de origem não verificada e
   confirmar que nenhum request é enviado para salvar o relatório.
8. Navegar/fechar a aba durante scan e verificar a falha explícita.
9. Testar uso por teclado e leitor de tela na tela da extensão e no importador.

Uma aba/estado por execução. Não há rastreamento automático de todas as rotas,
publicação em loja, compatibilidade Safari iOS ou integração ao histórico do DB.
