import importlib.util
import os
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
spec=importlib.util.spec_from_file_location('runner',Path(__file__).resolve().parents[1]/'runner.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

@unittest.skipUnless(os.environ.get('RUN_BROWSER_TESTS')=='1','Requer Chromium com sandbox; executado no CI.')
class BrowserTests(unittest.TestCase):
    def test_finds_missing_names_and_never_runs_page_scripts(self):
        html='<html lang="pt-BR"><title>Fixture</title><main><h1>Fixture</h1><img src="http://169.254.169.254/latest/meta-data/"><button></button><script>document.title="EXECUTED";fetch("http://127.0.0.1:9000/")</script></main></html>'
        r=runner.analyze(html)
        self.assertEqual(r['title'],'Fixture');self.assertEqual(r['engineVersion'],'4.13.0')
        self.assertIn('button-name',[c['id'] for c in r['checks'] if c['status']=='issue'])
        self.assertIn('image-alt',[c['id'] for c in r['checks'] if c['status']=='issue'])
        self.assertNotIn('color-contrast',[c['id'] for c in r['checks']])
        self.assertTrue(all(len(c['examples'])<=5 for c in r['checks']))

    def test_valid_fixture_has_no_missing_button_names(self):
        r=runner.analyze('<html lang="pt-BR"><title>Fixture</title><main><h1>Fixture</h1><button>Salvar</button><img alt="" src="x"></main></html>')
        self.assertFalse(any(c['id'] in ['button-name','image-alt'] and c['status']=='issue' for c in r['checks']))

    def test_visual_snapshot_detects_wide_content_and_small_targets(self):
        r=runner.analyze('<html lang="pt"><title>Visual</title><main><h1>Visual</h1><div style="width:1600px">Wide</div><button style="width:12px;height:12px;padding:0;border:0">x</button></main></html>')
        self.assertEqual([v['name'] for v in r['visual']],['desktop','mobile'])
        self.assertTrue(all(v['screenshot']['mime']=='image/jpeg' for v in r['visual']))
        self.assertEqual(r['visual'][1]['checks'][0]['status'],'review')
        self.assertGreater(r['visual'][1]['checks'][3]['count'],0)

    def test_blocked_external_css_import_does_not_abort_local_rules(self):
        result=runner.analyze(
            '<html lang="pt"><title>CSS import</title><main><h1>CSS import</h1><div class="wide">Conteúdo</div><button></button></main></html>',
            ['@import url("https://fonts.googleapis.com/css?family=Montserrat"); .wide { width: 1600px; }'],
        )
        self.assertEqual(result['title'], 'CSS import')
        self.assertIn('button-name', [check['id'] for check in result['checks'] if check['status']=='issue'])
        self.assertEqual(len(result['visual']), 2)
        self.assertEqual(result['visual'][1]['checks'][0]['status'], 'review')
