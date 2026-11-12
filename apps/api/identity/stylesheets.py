"""Collect at most three same-host stylesheets through the SSRF-safe fetcher."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from identity.ssrf import fetch_public_url,DestinationBlocked

class StylesheetLinks(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='link' and 'stylesheet' in (attrs.get('rel') or '').lower().split() and attrs.get('href') and 'disabled' not in attrs:
            self.links.append((attrs['href'],attrs.get('media') or 'all'))

def collect_stylesheets(html,url):
    parser=StylesheetLinks();parser.feed(html.decode('utf-8',errors='replace'))
    styles=[];skipped=0;seen=set();host=urlsplit(url).hostname
    for href,media in parser.links:
        try:
            target=urljoin(url,href)
            target_parts=urlsplit(target)
        except ValueError:
            skipped+=1;continue
        if target in seen:continue
        seen.add(target)
        if len(styles)>=3 or target_parts.hostname!=host or target_parts.scheme!='https':skipped+=1;continue
        try:
            response=fetch_public_url(target,allowed_hostname=host,timeout=3)
            if response.status!=200 or response.headers.get('content-type','').split(';')[0].strip().lower()!='text/css' or len(response.body)>262144 or response.headers.get('content-encoding','identity') not in ('','identity'):
                skipped+=1;continue
            css=response.body.decode('utf-8',errors='replace')
            styles.append(css if media in ('','all') else '@media '+media+'{'+css+'}')
        except (DestinationBlocked,TimeoutError,OSError):skipped+=1
    return styles,{'loaded':len(styles),'skipped':skipped,'importsAndAssetsLoaded':False}
