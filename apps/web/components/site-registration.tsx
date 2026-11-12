"use client";

import { FormEvent, useEffect, useRef, useState } from 'react';
import { ScanPanel } from './scan-panel';
import { createSite, getSites, Site } from '@/lib/api';

export function SiteRegistration({ token, canDeleteScans=false }: { token: string; canDeleteScans?: boolean }) {
 const [sites,setSites]=useState<Site[]>([]);
 const [loading,setLoading]=useState(true);
 const [loadError,setLoadError]=useState('');
 const [error,setError]=useState('');
 const [pending,setPending]=useState(false);
 const [name,setName]=useState('');
 const [url,setUrl]=useState('');
 const [success,setSuccess]=useState('');
 const submitting=useRef(false);
 useEffect(()=>{
  let active=true;
  getSites(token).then(items=>{if(active)setSites(items);}).catch(caught=>{if(active)setLoadError(caught instanceof Error?caught.message:'Não foi possível carregar os sites.');}).finally(()=>{if(active)setLoading(false);});
  return ()=>{active=false;};
 },[token]);
 async function submit(event:FormEvent<HTMLFormElement>){
  event.preventDefault(); if(submitting.current)return;
  setError(''); setSuccess('');
  try { const parsed=new URL(url); if(parsed.protocol!=='https:')throw new Error(); }
  catch {setError('Informe uma URL começando com https://.');return;}
  submitting.current=true;setPending(true);
  try {const site=await createSite(token,{displayName:name.trim(),url:url.trim()});setSites(current=>[site,...current]);setName('');setUrl('');setSuccess('Site cadastrado. Você já pode solicitar um scan.');}
  catch(caught){setError(caught instanceof Error?caught.message:'Não foi possível cadastrar o site.');}
  finally{submitting.current=false;setPending(false);}
 }
 return <section className="site-registration" aria-labelledby="sites-title">
  <h2 id="sites-title">Seus sites</h2>
  <p>Cadastre uma página pública HTTPS. Após o cadastro, solicite a análise e acompanhe seu estado.</p>
  <form onSubmit={submit} aria-busy={pending}>
   <label className="field">Nome do site<input required maxLength={120} value={name} onChange={e=>setName(e.target.value)} disabled={pending}/></label>
   <label className="field">URL HTTPS<input type="url" required maxLength={2048} placeholder="https://example.com" value={url} onChange={e=>setUrl(e.target.value)} disabled={pending} aria-describedby={error?'site-error site-url-help':'site-url-help'} aria-invalid={Boolean(error)}/></label>
   <p id="site-url-help">Endereços locais e privados são bloqueados por segurança.</p>
   {error&&<p id="site-error" role="alert">{error}</p>}
   <button className="primary-button" disabled={pending} type="submit">{pending?'Cadastrando…':'Cadastrar site'}</button>
   <p role="status">{success}</p>
  </form>
  {loading?<p role="status">Carregando sites…</p>:loadError?<p role="alert">{loadError}</p>:sites.length===0?<p>Nenhum site cadastrado.</p>:<ul>{sites.map(site=><li key={site.id}><a href={site.normalizedUrl} target="_blank" rel="noopener noreferrer">{site.displayName}</a><p>{site.normalizedUrl}</p><ScanPanel token={token} siteId={site.id} canDelete={canDeleteScans}/></li>)}</ul>}
 </section>;
}
