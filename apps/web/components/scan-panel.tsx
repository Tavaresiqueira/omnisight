'use client';
import {ReportView} from './report-view';
import {useEffect,useRef,useState} from 'react';
import {changeScan,deleteScan,getScans,getScanReport,requestScan,Scan,ScanReport} from '@/lib/api';
const labels={queued:'Na fila',running:'Em execução',completed:'Concluído',failed:'Falhou',cancelled:'Cancelado'};
export function ScanPanel({token,siteId,canDelete=false}:{token:string;siteId:string;canDelete?:boolean}){
 const [scans,setScans]=useState<Scan[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState(''),[pending,setPending]=useState(false),[report,setReport]=useState<ScanReport|null>(null);
 const [deletingId,setDeletingId]=useState<string|null>(null),[notice,setNotice]=useState('');
 const key=useRef<string|null>(null),lock=useRef(false);
 useEffect(()=>{
  let active=true,timer:ReturnType<typeof setTimeout>|undefined;const controller=new AbortController();
  async function refresh(){try{const data=await getScans(token,siteId,controller.signal);if(!active)return;setScans(data.items);setLoading(false);setError('');if(data.items.some(s=>['queued','running'].includes(s.status)))timer=setTimeout(refresh,2000);}catch(e){if(active){setLoading(false);setError(e instanceof Error?e.message:'Falha ao carregar scans.');}}}
  refresh();return()=>{active=false;controller.abort();clearTimeout(timer);};
 },[token,siteId,pending]);
 async function submit(action:()=>Promise<unknown>){if(lock.current)return;lock.current=true;setPending(true);setError('');try{await action();}catch(e){setError(e instanceof Error?e.message:'Falha ao executar scan.');}finally{lock.current=false;setPending(false);}}
 async function exportReport(id:string){
  const data=await getScanReport(token,id);
  const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
  const link=document.createElement('a');link.href=url;link.download=`omnisight-scan-${id}.json`;
  document.body.appendChild(link);link.click();link.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 return <div className="scan-panel"><button type="button" className="primary-button" disabled={pending||loading||scans.some(s=>['queued','running'].includes(s.status))} onClick={()=>submit(async()=>{key.current??=crypto.randomUUID();const scan=await requestScan(token,siteId,key.current);key.current=null;setScans(current=>[scan,...current.filter(s=>s.id!==scan.id)]);setReport(null);})}>Executar scan</button>
 <p role="status" aria-live="polite">{loading?'Carregando scans…':scans[0]?`Último scan: ${labels[scans[0].status]}.`:'Nenhum scan executado.'}</p>{error&&<p role="alert">{error}</p>}
 <p>Snapshot HTML isolado. Scripts, imagens e fontes não são carregados. CSS do mesmo domínio pode ser coletado; contraste e interação na página real continuam pendentes.</p>
 <p>Analise páginas públicas que você tem autorização para avaliar. Evidências e capturas podem conter dados pessoais. A retenção é definida no servidor; o proprietário pode excluir scans. Arquivos exportados ficam sob seu controle.</p>
 {notice&&<p role="status">{notice}</p>}
 <ul>{scans.map(s=><li key={s.id}><strong>{labels[s.status]}</strong> · {new Date(s.requestedAt).toLocaleString('pt-BR')} · Tentativa {s.attempts}/3 {s.errorCode&&<span> · Código: {s.errorCode} · Referência: {s.correlationId}</span>}
 {['queued','running'].includes(s.status)&&<button type="button" disabled={pending} onClick={()=>submit(()=>changeScan(token,s.id,'cancel'))}>Cancelar scan</button>}
 {s.status==='failed'&&s.attempts<3&&<button type="button" disabled={pending} onClick={()=>submit(()=>changeScan(token,s.id,'retry'))}>Tentar novamente</button>}
 {s.status==='completed'&&<><button type="button" disabled={pending} onClick={()=>submit(async()=>setReport(await getScanReport(token,s.id)))}>Ver relatório</button><button type="button" disabled={pending} onClick={()=>submit(()=>exportReport(s.id))}>Exportar relatório JSON</button></>}
 {canDelete&&(deletingId===s.id?<div role="group" aria-label="Confirmar exclusão do scan"><p>Excluir permanentemente este scan, relatório e capturas? Uma execução ativa perderá a permissão de publicar resultados.</p><button type="button" disabled={pending} onClick={()=>submit(async()=>{await deleteScan(token,s.id);setScans(current=>current.filter(item=>item.id!==s.id));setReport(null);setDeletingId(null);setNotice('Scan e relatório excluídos.');})}>Confirmar exclusão</button><button type="button" disabled={pending} onClick={()=>setDeletingId(null)}>Manter scan</button></div>:<button type="button" disabled={pending} onClick={()=>{setNotice('');setDeletingId(s.id);}}>Excluir scan</button>)}
 </li>)}</ul>
 {report&&<ReportView report={report}/>}
 </div>;
}
