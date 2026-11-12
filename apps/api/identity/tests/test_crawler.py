from unittest import TestCase
from unittest.mock import patch
from identity.crawler import crawl
from identity.ssrf import SafeFetchResponse, DestinationBlocked


def page(url, html):
    return SafeFetchResponse(url, 200, {'content-type': 'text/html; charset=utf-8'}, html.encode(), 0)


class CrawlerTests(TestCase):
    def test_domain_normalization_deduplication_and_depth(self):
        with patch('identity.crawler.fetch_public_url', side_effect=lambda url, **kwargs: page(url, '<a href="/docs#one">one</a><a href="/docs#two">two</a><a href="https://outside.example/">outside</a><a href="/next">next</a>')) as fetch:
            result = crawl('https://Example.COM:443/#top', max_pages=10, max_depth=1)
        self.assertEqual([p.final_url for p in result], ['https://example.com/', 'https://example.com/docs', 'https://example.com/next'])
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(fetch.call_args.kwargs['allowed_hostname'], 'example.com')

    def test_page_limit_stops_collection(self):
        with patch('identity.crawler.fetch_public_url', side_effect=lambda url, **kw: page(url, '<a href="/a">a</a><a href="/b">b</a>')) as fetch:
            self.assertEqual(len(crawl('https://example.com', max_pages=2)), 2)
            self.assertEqual(fetch.call_count, 2)

    def test_private_links_credentials_non_https_and_other_ports_not_followed(self):
        html = '<a href="https://127.0.0.1/">x</a><a href="https://user:pass@example.com/">x</a><a href="http://example.com/">x</a><a href="https://example.com:444/">x</a>'
        with patch('identity.crawler.fetch_public_url', return_value=page('https://example.com/', html)) as fetch:
            crawl('https://example.com')
            self.assertEqual(fetch.call_count, 1)

    def test_non_html_and_failed_responses_are_rejected(self):
        for response in [SafeFetchResponse('https://example.com/',200,{'content-type':'application/pdf'},b'pdf',0), SafeFetchResponse('https://example.com/',500,{'content-type':'text/html'},b'',0)]:
            with patch('identity.crawler.fetch_public_url', return_value=response):
                with self.assertRaises(ValueError):
                    crawl('https://example.com')

    def test_invalid_limits_are_rejected_without_network(self):
        with patch('identity.crawler.fetch_public_url') as fetch:
            for limits in [{'max_pages':0},{'max_pages':101},{'max_depth':-1},{'max_depth':6},{'timeout':0}]:
                with self.assertRaises(ValueError):
                    crawl('https://example.com', **limits)
            fetch.assert_not_called()

    def test_redirect_to_other_domain_is_blocked_before_request(self):
        from identity.ssrf import fetch_public_url
        with patch('identity.ssrf.resolve_public_destination') as resolve, patch('identity.ssrf._request_once', return_value=(302,[('location','https://other.example/')],b'')) as request:
            resolve.return_value.hostname='example.com'
            resolve.return_value.url='https://example.com/'
            with self.assertRaises(DestinationBlocked):
                fetch_public_url('https://example.com/', allowed_hostname='example.com')
            self.assertEqual(request.call_count, 1)

    def test_same_domain_redirect_is_allowed(self):
        from identity.ssrf import fetch_public_url, PublicDestination
        with patch('identity.ssrf.resolve_public_destination', side_effect=lambda url: PublicDestination(url, 'example.com', 443, ('93.184.216.34',))), patch('identity.ssrf._request_once', side_effect=[(302,[('location','/docs')],b''),(200,[('content-type','text/html')],b'ok')]) as request:
            response = fetch_public_url('https://example.com/', allowed_hostname='example.com')
            self.assertEqual(response.final_url, 'https://example.com/docs')
            self.assertEqual(request.call_count, 2)

    def test_elapsed_budget_stops_before_fetch(self):
        with patch('identity.crawler.time.monotonic', side_effect=[0, 31]), patch('identity.crawler.fetch_public_url') as fetch:
            with self.assertRaises(TimeoutError):
                crawl('https://example.com', timeout=30)
            fetch.assert_not_called()

    def test_compressed_html_is_rejected(self):
        response = SafeFetchResponse('https://example.com/',200,{'content-type':'text/html','content-encoding':'gzip'},b'compressed',0)
        with patch('identity.crawler.fetch_public_url',return_value=response):
            with self.assertRaises(ValueError):
                crawl('https://example.com')
