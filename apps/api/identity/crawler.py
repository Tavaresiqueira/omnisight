"""Bounded HTML collection. No JavaScript execution or accessibility score."""
from collections import deque
from html.parser import HTMLParser
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from identity.ssrf import DestinationBlocked, fetch_public_url


def canonical_url(url):
    parts = urlsplit(url)
    if parts.scheme.lower() != 'https' or not parts.hostname:
        raise ValueError('O crawler aceita apenas URLs HTTPS.')
    if parts.username is not None or parts.password is not None or parts.port not in (None, 443):
        raise ValueError('Credenciais e portas alternativas não são permitidas.')
    host = parts.hostname.rstrip('.').encode('idna').decode('ascii').lower()
    if ':' in host:
        host = f'[{host}]'
    return urlunsplit(('https', host, parts.path or '/', parts.query, ''))


class PageLinks(HTMLParser):
    def __init__(self, admit):
        super().__init__(convert_charrefs=True)
        self.admit = admit

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href' and value:
                    self.admit(value)
                    break


def crawl(url, *, max_pages=10, max_depth=1, timeout=30):
    if type(max_pages) is not int or not 1 <= max_pages <= 100:
        raise ValueError('O limite de páginas deve estar entre 1 e 100.')
    if type(max_depth) is not int or not 0 <= max_depth <= 5:
        raise ValueError('A profundidade deve estar entre 0 e 5.')
    if not isinstance(timeout, (int, float)) or not 0 < timeout <= 120:
        raise ValueError('O orçamento de tempo deve estar entre 0 e 120 segundos.')
    root = canonical_url(url)
    host = urlsplit(root).hostname
    frontier = deque([(root, 0)])
    scheduled = {root}
    results = []
    deadline = time.monotonic() + timeout
    while frontier:
        current, depth = frontier.popleft()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('O crawl excedeu seu orçamento de tempo.')
        response = fetch_public_url(current, allowed_hostname=host, timeout=min(10, remaining))
        if time.monotonic() > deadline:
            raise TimeoutError('O crawl excedeu seu orçamento de tempo.')
        if response.status != 200:
            raise ValueError(f'A página retornou HTTP {response.status}.')
        mime = response.headers.get('content-type', '').split(';')[0].strip().lower()
        if mime not in {'text/html', 'application/xhtml+xml'}:
            raise ValueError('O crawler aceita somente respostas HTML.')
        if response.headers.get('content-encoding', 'identity').lower() not in {'identity', ''}:
            raise ValueError('Respostas comprimidas não são aceitas nesta etapa.')
        final = canonical_url(response.final_url)
        if urlsplit(final).hostname != host:
            raise DestinationBlocked('O crawl não pode sair do domínio inicial.')
        scheduled.add(final)
        results.append(response)
        if depth >= max_depth or len(results) >= max_pages:
            continue

        def admit(link):
            if len(scheduled) >= max_pages:
                return
            try:
                candidate = canonical_url(urljoin(final, link))
            except (ValueError, UnicodeError):
                return
            if urlsplit(candidate).hostname == host and candidate not in scheduled:
                scheduled.add(candidate)
                frontier.append((candidate, depth + 1))

        parser = PageLinks(admit)
        parser.feed(response.body.decode('utf-8', errors='replace'))
        parser.close()
    return results
