import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {ImportReport} from './import-report';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
const payload={schemaVersion:1,source:'extension-local',engine:'axe-core',engineVersion:'4.13.0',mode:'rendered-dom',pages:[{url:'https://example.com/',title:'<img src=x onerror=alert(1)>',checks:[],limitations:['Uma aba.']}],coverage:{pageLimit:1,externalResources:true,pageScripts:true,completeWcagAudit:false}};
it('imports locally, identifies unverified origin and renders values as text',async()=>{
 const fetcher=vi.spyOn(globalThis,'fetch');render(<ImportReport/>);
 const file=new File([JSON.stringify(payload)],'scan.json',{type:'application/json'});Object.defineProperty(file,'text',{value:async()=>JSON.stringify(payload)});
 await userEvent.setup().upload(screen.getByLabelText('Importar diagnóstico da extensão'),file);
 expect(await screen.findByText('Diagnóstico local importado')).toBeInTheDocument();
 expect(screen.getByRole('note')).toHaveTextContent('não verificada');expect(screen.getByText('<img src=x onerror=alert(1)>')).toBeInTheDocument();expect(document.querySelector('.saved-report img')).toBeNull();expect(fetcher).not.toHaveBeenCalled();
 await userEvent.setup().click(screen.getByRole('button',{name:'Limpar relatório local'}));expect(screen.queryByText('Diagnóstico local importado')).toBeNull();
});
it('rejects an invalid file without displaying a report',async()=>{
 render(<ImportReport/>);const file=new File(['{}'],'invalid.json',{type:'application/json'});Object.defineProperty(file,'text',{value:async()=>'{}'});
 await userEvent.setup().upload(screen.getByLabelText('Importar diagnóstico da extensão'),file);
 expect(await screen.findByRole('alert')).toHaveTextContent('incompatível');expect(screen.queryByText('Diagnóstico local importado')).toBeNull();
});
