import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {JSDOM} from 'jsdom';
import {exportReport} from './report-export.mjs';
const source=await readFile(new URL('./scanner.js',import.meta.url),'utf8');
function fixture(){const dom=new JSDOM('<html><title>Minha plataforma</title><body><button></button></body></html>',{url:'https://example.com/conta?token=secret#private',runScripts:'outside-only'});dom.window.TextEncoder=TextEncoder;return dom;}
test('requests only temporary explicit permissions and no automatic site access',async()=>{
 const m=JSON.parse(await readFile(new URL('./manifest.json',import.meta.url),'utf8'));
 assert.deepEqual(m.permissions,['activeTab','scripting']);assert.equal(m.host_permissions,undefined);assert.equal(m.content_scripts,undefined);
});
test('scans rendered DOM with contrast enabled, strips URL query and bounds evidence',async()=>{
 const dom=fixture();let opts;
 const rule={id:'button-name',help:'Botão sem nome',description:'Dar nome',impact:'serious',tags:['wcag412'],nodes:Array.from({length:7},()=>({target:['button'],html:'<button></button>',failureSummary:'Corrigir'}))};
 dom.window.axe={version:'4.13.0',run:async(doc,options)=>{assert.equal(doc,dom.window.document);opts=options;return {testEngine:{version:'4.13.0'},violations:[rule],incomplete:[],passes:[],inapplicable:[]};}};
 const report=await dom.window.eval(source);assert.equal(report.mode,'rendered-dom');assert.equal(report.pages[0].url,'https://example.com/conta');assert.equal(report.pages[0].checks[0].count,7);assert.equal(report.pages[0].checks[0].examples.length,5);assert.equal(opts.rules,undefined);assert.equal(opts.iframes,false);assert.equal(dom.window.__omnisightRunning,false);dom.window.close();
});
test('exports without HTML by default and keeps internal evidence unchanged',()=>{
 const original={pages:[{checks:[{examples:[{html:'<input value="private">',selector:'input',summary:'Nome ausente'}]}]}]};
 assert.equal(JSON.parse(exportReport(original)).pages[0].checks[0].examples[0].html,'');
 assert.equal(JSON.parse(exportReport(original,true)).pages[0].checks[0].examples[0].html,'<input value="private">');
 assert.equal(original.pages[0].checks[0].examples[0].html,'<input value="private">');
});
test('does not start a second concurrent scan of the same document',async()=>{
 const dom=fixture();dom.window.__omnisightRunning=true;
 await assert.rejects(dom.window.eval(source),/Já existe um scan/);dom.window.close();
});
