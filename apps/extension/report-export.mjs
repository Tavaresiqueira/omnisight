export function exportReport(report,includeHtml=false){
 const copy=structuredClone(report);
 if(!includeHtml)for(const page of copy.pages)for(const check of page.checks)for(const example of check.examples)example.html='';
 return JSON.stringify(copy);
}
