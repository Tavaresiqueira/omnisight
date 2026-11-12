(async () => {
  // This script runs in the extension's isolated world in the explicitly selected tab.
  if (globalThis.__omnisightRunning) throw new Error('Já existe um scan desta aba em execução.');
  globalThis.__omnisightRunning = true;
  let timedOut = false;
  try {
    if (!globalThis.axe || axe.version !== '4.13.0') throw new Error('Engine indisponível.');
    let timeout;
    try {
      const result = await Promise.race([
        axe.run(document, {
          iframes: false,
          runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
          resultTypes: ['violations', 'incomplete', 'passes', 'inapplicable'],
        }),
        new Promise((_, reject) => { timeout = setTimeout(() => { timedOut=true; reject(new Error('O scan excedeu 30 segundos. Recarregue a aba antes de tentar novamente.')); }, 30000); }),
      ]);
      const checks = [];
      for (const [group, status] of [['violations', 'issue'], ['incomplete', 'review'], ['passes', 'clear'], ['inapplicable', 'na']]) {
        for (const rule of result[group]) {
          checks.push({ id: rule.id, title: rule.help, status, impact: rule.impact || 'moderate', criteria: rule.tags.filter(t => /^wcag\d{3,4}$/.test(t)), count: rule.nodes.length, help: rule.description, examples: rule.nodes.slice(0, 5).map(node => ({ selector: node.target.join(' > ').slice(0, 1000), html: node.html.slice(0, 400), summary: (node.failureSummary || '').slice(0, 1500) })) });
        }
      }
      const report = {
        schemaVersion: 1, engine: 'axe-core', engineVersion: result.testEngine.version,
        mode: 'rendered-dom', source: 'extension-local', createdAt: new Date().toISOString(),
        pages: [{ url: location.origin + location.pathname, title: document.title.slice(0, 512), checks,
          limitations: ['Somente o documento principal e o estado atual da aba foram analisados; outras rotas e frames não foram percorridos.', 'Contraste é avaliado onde a engine consegue determinar as cores; resultados inconclusivos exigem revisão.', 'Áreas não carregadas, shadow roots fechados, teclado, fluxos completos e conteúdo de canvas podem exigir avaliação adicional.', 'Este relatório foi produzido localmente no cliente; não é uma certificação de conformidade WCAG.'] }],
        coverage: { pageLimit: 1, externalResources: true, pageScripts: true, completeWcagAudit: false, framesAnalyzed: false },
      };
      if (new TextEncoder().encode(JSON.stringify(report)).length > 1024 * 1024) throw new Error('O relatório excedeu 1 MiB. Reduza o conteúdo da página e tente novamente.');
      return report;
    } finally { clearTimeout(timeout); }
  } finally { if(!timedOut) globalThis.__omnisightRunning = false; }
})();
