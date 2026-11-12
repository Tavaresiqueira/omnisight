(() => {
  const visible = el => { const r=el.getBoundingClientRect(),s=getComputedStyle(el); return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'; };
  const selector = el => { const parts=[];for(let n=el;n&&n!==document.documentElement;n=n.parentElement){const same=[...n.parentElement?.children||[]].filter(s=>s.tagName===n.tagName);parts.unshift(n.tagName.toLowerCase()+`:nth-of-type(${same.indexOf(n)+1})`);}return parts.join(' > ').slice(0,1000); };
  const elements=[...document.body.querySelectorAll('*')],limit=5000,inspected=elements.slice(0,limit).filter(visible);
  const offscreen=inspected.filter(el=>{const r=el.getBoundingClientRect();return r.left < -2 || r.right > innerWidth+2;});
  const clipped=inspected.filter(el=>['hidden','clip'].includes(getComputedStyle(el).overflowX)&&el.scrollWidth>el.clientWidth+2&&el.textContent.trim());
  const controls=inspected.filter(el=>el.matches('a[href],button,input:not([type="hidden"]),select,textarea,[role="button"]')&&!el.matches(':disabled'));
  const small=controls.filter(el=>{const r=el.getBoundingClientRect();return r.width<24||r.height<24;});
  const evidence=els=>els.slice(0,5).map(el=>{const r=el.getBoundingClientRect();return {selector:selector(el),rect:{x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)}};});
  return {viewport:{width:innerWidth,height:innerHeight},documentWidth:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth),inspected:inspected.length,truncated:elements.length>limit,checks:[
    {id:'horizontal-overflow',title:'Rolagem horizontal no viewport',criterion:'1.4.10',status:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)>innerWidth+2?'review':'clear',count:Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)>innerWidth+2?1:0,help:'Verifique se o conteúdo exige rolagem horizontal e se alguma exceção de layout é aplicável. Este teste não simula zoom de 400%.',examples:[]},
    {id:'offscreen-elements',title:'Elementos além das bordas horizontais',criterion:'1.4.10',status:offscreen.length?'review':'clear',count:offscreen.length,help:'Confira menus fora de tela, animações e posições intencionais antes de corrigir. Um indício geométrico não confirma falha WCAG.',examples:evidence(offscreen)},
    {id:'clipped-content',title:'Conteúdo com possível corte horizontal',criterion:'1.4.4 / 1.4.10',status:clipped.length?'review':'clear',count:clipped.length,help:'Revise truncamento e acesso ao texto completo; ellipsis pode ser intencional. Zoom e espaçamento ainda exigem testes próprios.',examples:evidence(clipped)},
    {id:'small-targets',title:'Alvos menores que 24 CSS px',criterion:'2.5.8',status:small.length?'review':'clear',count:small.length,help:'Avalie também espaçamento entre alvos, controles alternativos e exceções como links em texto. Tamanho isolado não determina violação.',examples:evidence(small)}
  ]};
})();
