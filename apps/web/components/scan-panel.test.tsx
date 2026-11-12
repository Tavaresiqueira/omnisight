import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {ScanPanel} from './scan-panel';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
const scan={id:'scan-1',siteId:'site-1',status:'queued',attempts:0,errorCode:'',requestedAt:'2026-11-11T10:00:00Z',startedAt:null,completedAt:null,correlationId:'ref'};
it('requests a persisted scan with idempotency and supports cancellation',async()=>{
 const mock=vi.spyOn(globalThis,'fetch').mockImplementation(async(url,init)=>{
  if(init?.method==='POST'&&String(url).endsWith('/scans/'))return new Response(JSON.stringify(scan),{status:202});
  if(String(url).includes('/actions/'))return new Response(JSON.stringify({...scan,status:'cancelled'}));
  return new Response(JSON.stringify({items:mock.mock.calls.some(([,i])=>i?.method==='POST')?[scan]:[]}));
 });
 render(<ScanPanel token="token" siteId="site-1"/>);await screen.findByText('Nenhum scan executado.');
 const user=userEvent.setup();await user.click(screen.getByRole('button',{name:'Executar scan'}));
 expect(await screen.findByText('Na fila')).toBeInTheDocument();
 expect(mock).toHaveBeenCalledWith(expect.stringMatching(/sites\/site-1\/scans\/$/),expect.objectContaining({method:'POST',headers:expect.objectContaining({'Idempotency-Key':expect.any(String),Authorization:'Token token'})}));
 await user.click(screen.getByRole('button',{name:'Cancelar scan'}));
 await waitFor(()=>expect(mock).toHaveBeenCalledWith(expect.stringMatching(/actions\/$/),expect.objectContaining({body:JSON.stringify({action:'cancel'})})));
});
it('renders saved findings safely and states the offline coverage',async()=>{
 vi.spyOn(globalThis,'fetch').mockImplementation(async(url)=>new Response(JSON.stringify(String(url).includes('/report/')?{engine:'axe-core',engineVersion:'4.13.0',mode:'offline-html',pages:[{url:'https://example.com/',title:'Fixture',visual:[{name:'mobile',viewport:{width:390,height:844},truncated:false,screenshot:null,screenshotWarning:'Captura omitida.',checks:[{id:'overflow',title:'Rolagem horizontal',criterion:'1.4.10',status:'review',count:1,help:'Revisar',examples:[]}]}],limitations:['Contraste não avaliado.'],checks:[{id:'button-name',title:'Botão sem nome',status:'issue',count:1,impact:'critical',criteria:['wcag412'],help:'Dar nome',examples:[{selector:'button',html:'<img src=x onerror=alert(1)>',summary:'Corrigir'}]}]}]}:{items:[{...scan,status:'completed'}]})));
 render(<ScanPanel token="token" siteId="site-1"/>);const button=await screen.findByRole('button',{name:'Ver relatório'});await userEvent.setup().click(button);
 expect(await screen.findByText('Diagnóstico salvo')).toBeInTheDocument();expect(screen.getByText('Captura omitida.')).toBeInTheDocument();expect(screen.getByText(/Revisar · Rolagem horizontal/)).toBeInTheDocument();expect(screen.getByText('Contraste não avaliado.')).toBeInTheDocument();
 expect(screen.getByText('Referências: 4.1.2')).toBeInTheDocument();
 expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeInTheDocument();expect(document.querySelector('.saved-report img')).toBeNull();
});
it('requires explicit confirmation to delete and removes the scan from the list',async()=>{
 const mock=vi.spyOn(globalThis,'fetch').mockImplementation(async(_url,init)=>init?.method==='DELETE'?new Response(null,{status:204}):new Response(JSON.stringify({items:[{...scan,status:'completed'}]})));
 render(<ScanPanel token="token" siteId="site-1" canDelete/>);
 const user=userEvent.setup();await user.click(await screen.findByRole('button',{name:'Excluir scan'}));
 expect(mock.mock.calls.some(([,init])=>init?.method==='DELETE')).toBe(false);
 await user.click(screen.getByRole('button',{name:'Manter scan'}));
 expect(screen.queryByRole('button',{name:'Confirmar exclusão'})).not.toBeInTheDocument();
 await user.click(screen.getByRole('button',{name:'Excluir scan'}));
 await user.click(screen.getByRole('button',{name:'Confirmar exclusão'}));
 expect(await screen.findByText('Scan e relatório excluídos.')).toBeInTheDocument();
 expect(mock).toHaveBeenCalledWith(expect.stringMatching(/scans\/scan-1\/$/),expect.objectContaining({method:'DELETE'}));
});
it('does not offer deletion to a viewer',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({items:[{...scan,status:'completed'}]})));
 render(<ScanPanel token="token" siteId="site-1"/>);
 await screen.findByRole('button',{name:'Ver relatório'});
 expect(screen.queryByRole('button',{name:'Excluir scan'})).not.toBeInTheDocument();
});
it('downloads the authorized report as JSON and releases the temporary URL',async()=>{
 const mock=vi.spyOn(globalThis,'fetch').mockImplementation(async(url)=>new Response(JSON.stringify(String(url).includes('/report/')?{schemaVersion:1,engine:'axe-core',pages:[]}:{items:[{...scan,status:'completed'}]})));
 const create=vi.fn(()=> 'blob:local-report'),revoke=vi.fn();
 vi.stubGlobal('URL',{createObjectURL:create,revokeObjectURL:revoke});
 const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){expect(this.download).toBe('omnisight-scan-scan-1.json');});
 render(<ScanPanel token="token" siteId="site-1"/>);
 await userEvent.setup().click(await screen.findByRole('button',{name:'Exportar relatório JSON'}));
 expect(create).toHaveBeenCalledWith(expect.any(Blob));expect(click).toHaveBeenCalledOnce();
 expect(mock).toHaveBeenCalledWith(expect.stringMatching(/scans\/scan-1\/report\/$/),expect.objectContaining({headers:expect.objectContaining({Authorization:'Token token'})}));
 await waitFor(()=>expect(revoke).toHaveBeenCalledWith('blob:local-report'),{timeout:2000});
});
