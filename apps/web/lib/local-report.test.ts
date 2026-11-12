import {expect,it} from 'vitest';
import {parseLocalReport} from './local-report';
const valid={schemaVersion:1,engine:'axe-core',engineVersion:'4.13.0',mode:'rendered-dom',source:'extension-local',pages:[{url:'https://example.com/path',title:'Fixture',checks:[{id:'button-name',title:'Botão sem nome',status:'issue',impact:'serious',criteria:['wcag412'],count:1,help:'Dar nome',examples:[{selector:'button',html:'<button></button>',summary:'Revisar'}]}],limitations:['Uma aba.']}],coverage:{pageLimit:1,externalResources:true,pageScripts:true,completeWcagAudit:false}};
it('accepts only the bounded rendered-DOM report contract',()=>{
 expect(parseLocalReport(JSON.stringify(valid)).mode).toBe('rendered-dom');
 expect(()=>parseLocalReport(JSON.stringify({...valid,mode:'offline-html'}))).toThrow();
 expect(()=>parseLocalReport(JSON.stringify({...valid,pages:[{...valid.pages[0],checks:[{...valid.pages[0].checks[0],count:-1}]}]}))).toThrow();
 expect(()=>parseLocalReport('x'.repeat(1048577))).toThrow();
});
it('rejects script URLs, malformed evidence and unsupported versions',()=>{
 for(const altered of [{...valid,engineVersion:'other'},{...valid,pages:[{...valid.pages[0],url:'javascript:alert(1)'}]},{...valid,pages:[{...valid.pages[0],checks:[{...valid.pages[0].checks[0],examples:[{selector:'x',html:'x'.repeat(401),summary:'x'}]}]}]}])expect(()=>parseLocalReport(JSON.stringify(altered))).toThrow();
});
