import type {ScanReport} from './api';
/** External file boundary. Imported reports are local and never considered server attestations. */
export function parseLocalReport(raw:string):ScanReport {
 const fail=()=>{throw new Error('Arquivo de diagnóstico inválido ou incompatível. Use a exportação da extensão OmniSight.');};
 if(new TextEncoder().encode(raw).length>1024*1024)fail();
 const r=JSON.parse(raw);
 const text=(v:unknown,max:number)=>typeof v==='string'&&v.length<=max;
 if(!r||r.schemaVersion!==1||r.engine!=='axe-core'||r.engineVersion!=='4.13.0'||r.mode!=='rendered-dom'||r.source!=='extension-local'||!Array.isArray(r.pages)||r.pages.length!==1)fail();
 if(!r.coverage||r.coverage.pageLimit!==1||r.coverage.completeWcagAudit!==false||r.coverage.externalResources!==true||r.coverage.pageScripts!==true)fail();
 for(const p of r.pages){
  if(p&&'visual' in p)fail();
  if(!p||!text(p.url,4096)||!text(p.title,512)||!Array.isArray(p.checks)||p.checks.length>500||!Array.isArray(p.limitations)||p.limitations.length>20||p.limitations.some((v:unknown)=>!text(v,2000)))fail();
  let url:URL;try{url=new URL(p.url);}catch{fail();return r;}
  if(!['https:','http:'].includes(url.protocol)||url.username||url.password)fail();
  for(const c of p.checks){
   if(!c||!['issue','review','clear','na'].includes(c.status)||!Number.isInteger(c.count)||c.count<0||!['id','title','impact','help'].every(k=>text(c[k],8192)))fail();
   if(!Array.isArray(c.criteria)||c.criteria.length>30||c.criteria.some((v:unknown)=>!text(v,64)))fail();
   if(!Array.isArray(c.examples)||c.examples.length>5||c.examples.some((e:Record<string,unknown>)=>!e||!text(e.selector,1000)||!text(e.html,400)||!text(e.summary,1500)))fail();
  }
 }
 return r as ScanReport;
}
