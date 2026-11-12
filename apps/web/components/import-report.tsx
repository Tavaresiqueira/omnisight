'use client';
import {useState} from 'react';
import type {ScanReport} from '@/lib/api';
import {parseLocalReport} from '@/lib/local-report';
import {ReportView} from './report-view';
export function ImportReport(){
 const [report,setReport]=useState<ScanReport|null>(null),[error,setError]=useState('');
 return <section className="site-registration" aria-labelledby="local-report-title"><h2 id="local-report-title">Analisar a página renderizada</h2><p>A extensão analisa a aba já carregada no Chrome ou Edge do computador, inclusive depois do login no seu site. Usa os estilos reais e pode testar contraste quando a engine consegue determiná-lo.</p><p><a href="/omnisight-extension.zip" download>Baixar extensão experimental (ZIP)</a> · <a href="/extensao-instalacao.html" target="_blank" rel="noreferrer">Como instalar</a></p><label className="field">Importar diagnóstico da extensão<input type="file" accept=".json,application/json" onChange={async e=>{const f=e.target.files?.[0];if(!f)return;setError('');setReport(null);try{if(f.size>1048576)throw new Error('O relatório deve ter no máximo 1 MiB.');setReport(parseLocalReport(await f.text()));}catch(err){setError(err instanceof Error?err.message:'Arquivo inválido.');}e.target.value='';}}/></label><p>Importação local: não envia automaticamente o conteúdo ao servidor e não o adiciona ao histórico.</p>{error&&<p role="alert">{error}</p>}{report&&<><button className="secondary-button" onClick={()=>setReport(null)}>Limpar relatório local</button><ReportView report={report} imported/></>}</section>;
}
