from unittest import TestCase
from unittest.mock import patch
from identity.stylesheets import collect_stylesheets
from identity.ssrf import SafeFetchResponse
class StylesheetTests(TestCase):
    @patch('identity.stylesheets.fetch_public_url')
    def test_collects_same_host_css_only_and_honors_media(self,fetch):
        fetch.return_value=SafeFetchResponse('https://example.com/a.css',200,{'content-type':'text/css'},b'body{color:red}',0)
        styles,coverage=collect_stylesheets(b'<link rel="stylesheet" href="/a.css" media="screen"><link rel="stylesheet" href="https://cdn.example/style.css">','https://example.com/')
        self.assertIn('@media screen',styles[0]);self.assertEqual(coverage['skipped'],1);fetch.assert_called_once_with('https://example.com/a.css',allowed_hostname='example.com',timeout=3)
    @patch('identity.stylesheets.fetch_public_url')
    def test_rejects_non_css_and_limits_to_three(self,fetch):
        fetch.return_value=SafeFetchResponse('https://example.com/a.css',200,{'content-type':'text/css'},b'body{}',0)
        styles,coverage=collect_stylesheets(''.join(f'<link rel="stylesheet" href="/{i}.css">' for i in range(5)).encode(),'https://example.com/')
        self.assertEqual(len(styles),3);self.assertEqual(coverage['skipped'],2)
        fetch.return_value=SafeFetchResponse('https://example.com/a.css',200,{'content-type':'text/html'},b'<script>x</script>',0)
        self.assertEqual(collect_stylesheets(b'<link rel="stylesheet" href="/a.css">','https://example.com/')[0],[])

    @patch('identity.stylesheets.fetch_public_url')
    def test_malformed_optional_link_attributes_do_not_abort_scan(self,fetch):
        fetch.return_value=SafeFetchResponse('https://example.com/a.css',200,{'content-type':'text/css'},b'body{}',0)
        styles,coverage=collect_stylesheets(b'<link rel href="x"><link rel="stylesheet" href="https://["><link rel="stylesheet" href="/a.css" media>','https://example.com/')
        self.assertEqual(styles,['body{}']);self.assertEqual(coverage['skipped'],1)
