import json
from unittest import TestCase
from unittest.mock import patch
from identity.pipeline import analyze_page

class AnalyzerContractTests(TestCase):
    @patch('identity.pipeline.urlopen')
    def test_rejects_unknown_engine_versions_and_malformed_contracts(self,opening):
        for payload in [{},{'engine':'axe-core','engineVersion':'unknown','mode':'offline-html','checks':[]},{'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','checks':'invalid'}]:
            opening.return_value.__enter__.return_value.read.return_value=json.dumps(payload).encode()
            with self.assertRaises(ValueError):analyze_page(b'<html>')
    @patch('identity.pipeline.urlopen')
    def test_response_size_is_bounded(self,opening):
        opening.return_value.__enter__.return_value.read.return_value=b'x'*(1024*1024+1)
        with self.assertRaises(ValueError):analyze_page(b'<html>')

    def test_rejects_unbounded_or_malformed_evidence(self):
        from identity.pipeline import validate_analysis
        base={'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','title':'Fixture','limitations':[]}
        for checks in [[3],[{'id':'x','status':'issue','count':True}],[{'id':'x','title':'x','status':'issue','count':1,'impact':'serious','help':'help','criteria':[],'examples':[{'selector':'x','html':'x'*401,'summary':'x'}]}]]:
            with self.assertRaises(ValueError):validate_analysis({**base,'checks':checks})

    def test_rejects_unsafe_visual_images(self):
        from identity.pipeline import validate_analysis
        result={'engine':'axe-core','engineVersion':'4.13.0','mode':'offline-html','title':'Fixture','limitations':[],'checks':[],'visual':[{'name':'desktop','viewport':{'width':1280,'height':800},'checks':[],'screenshot':{'mime':'image/svg+xml','dataBase64':'AAAA'}},{'name':'mobile','viewport':{'width':390,'height':844},'checks':[],'screenshot':None}]}
        with self.assertRaises(ValueError):validate_analysis(result)
