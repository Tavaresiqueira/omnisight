(async () => {
              const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']},rules:{'color-contrast':{enabled:false}},resultTypes:['violations','incomplete','passes','inapplicable']});
              const checks=[];
              for (const [key,status] of [['violations','issue'],['incomplete','review'],['passes','clear'],['inapplicable','na']]) {
                for(const v of r[key]) checks.push({id:v.id,title:v.help,status,impact:v.impact||'moderate',criteria:v.tags.filter(t=>/^wcag[0-9]{3,4}$/.test(t)),count:v.nodes.length,help:v.description,helpUrl:v.helpUrl,examples:v.nodes.slice(0,5).map(n=>({selector:n.target.join(' > ').slice(0,1000),html:n.html.slice(0,400),summary:(n.failureSummary||'').slice(0,1500)}))});
              }
              return {engine:'axe-core',engineVersion:r.testEngine.version,browserVersion:navigator.userAgent,mode:'offline-html',title:document.title,checks};
            })()
