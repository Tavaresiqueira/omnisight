import {test} from 'node:test';import assert from 'node:assert/strict';import {readFile} from 'node:fs/promises';import {JSDOM} from 'jsdom';
const source=await readFile(new URL('./visual.js',import.meta.url),'utf8');
test('measures horizontal overflow and flags small targets as review, not violations',()=>{
 const dom=new JSDOM('<body><div>Texto</div><button>x</button></body>',{runScripts:'outside-only'});const w=dom.window;
 Object.defineProperty(w,'innerWidth',{value:390});Object.defineProperty(w.document.documentElement,'scrollWidth',{value:900});
 for(const el of w.document.body.children)el.getBoundingClientRect=()=>({x:0,y:0,left:0,right:el.tagName==='BUTTON'?12:900,width:el.tagName==='BUTTON'?12:900,height:12});
 const r=w.eval(source);assert.equal(r.checks[0].status,'review');assert.equal(r.checks[1].count,1);assert.equal(r.checks[3].count,1);assert.equal(r.checks[3].status,'review');assert.equal(r.checks[3].examples[0].rect.width,12);dom.window.close();
});
test('does not flag invisible or disabled controls as small targets',()=>{
 const dom=new JSDOM('<body><button disabled>x</button><button hidden>y</button></body>',{runScripts:'outside-only'});dom.window.document.querySelector('button').getBoundingClientRect=()=>({x:0,y:0,left:0,right:12,width:12,height:12});
 assert.equal(dom.window.eval(source).checks[3].count,0);dom.window.close();
});
