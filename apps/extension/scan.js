import {exportReport} from './report-export.mjs';
const status = document.getElementById('status');
const error = document.getElementById('error');
let report;
const labels = {issue:'Problema detectado',review:'Revisão humana',clear:'Sem achado nesta regra',na:'Não aplicável'};
function node(tag,text){const el=document.createElement(tag);el.textContent=text;return el;}
function render(){
 const page=report.pages[0];document.getElementById('title').textContent=page.title||'Página sem título';document.getElementById('url').textContent=page.url;
 const metrics=document.getElementById('metrics');metrics.replaceChildren();
 for(const [state,label] of Object.entries(labels)){const box=node('article','');box.append(node('b',String(page.checks.filter(c=>c.status===state).length)),node('span',label));box.className=state;metrics.append(box);}
 document.getElementById('coverage').textContent=page.limitations.join(' ');
 const filter=document.getElementById('filter').value;const list=document.getElementById('checks');list.replaceChildren();
 for(const check of page.checks.filter(c=>filter==='all'||(filter==='findings'?['issue','review'].includes(c.status):c.status===filter))){
  const details=node('details','');details.append(node('summary',`${labels[check.status]} · ${check.title} · ${check.count} elementos`),node('p',check.help),node('p','WCAG: '+check.criteria.map(c=>c.replace(/^wcag(\d)(\d)(\d+)$/,'$1.$2.$3')).join(', ')));
  for(const example of check.examples){details.append(node('code',example.selector),node('p',example.summary));}
  list.append(details);
 }
}
document.getElementById('filter').addEventListener('change',()=>render());
document.getElementById('download').addEventListener('click',()=>{
 const blob=new Blob([exportReport(report,document.getElementById('include-html').checked)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='omnisight-diagnostico-local.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
});
try{
 const tabId=Number(new URL(location.href).searchParams.get('tab'));
 if(!Number.isInteger(tabId)||tabId<=0)throw new Error('Abra a extensão pelo ícone na aba que deseja analisar.');
 status.textContent='Analisando a aba selecionada. Você pode continuar nesta tela.';
 const results=await chrome.scripting.executeScript({target:{tabId,frameIds:[0]},world:'ISOLATED',files:['vendor/axe.min.js','vendor/locale.js','scanner.js']});
 report=results[0]?.result;
 if(!report||report.mode!=='rendered-dom')throw new Error('A aba não devolveu um diagnóstico.');
 render();document.getElementById('results').hidden=false;status.textContent='Análise concluída. Dados mantidos somente nesta tela até você baixar o arquivo.';
}catch(e){status.textContent='Não foi possível concluir o scan.';error.textContent='A aba pode ter sido fechada, navegado ou ser uma página restrita do navegador. Abra uma página HTTP/HTTPS, aguarde o conteúdo carregar e clique novamente no ícone. '+(e instanceof Error?e.message:'');error.hidden=false;}
