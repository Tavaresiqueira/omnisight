import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock
spec=importlib.util.spec_from_file_location('visual',Path(__file__).resolve().parents[1]/'visual_capture.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class VisualCaptureTests(TestCase):
    def test_captures_two_bounded_viewports_without_full_page(self):
        page=Mock();page.evaluate.side_effect=[None,{'viewport':{'width':1280,'height':800},'checks':[]},None,{'viewport':{'width':390,'height':844},'checks':[]}];page.screenshot.return_value=b'jpeg-fixture'
        captures=module.capture_visual(page)
        self.assertEqual([c['name'] for c in captures],['desktop','mobile'])
        self.assertEqual(page.screenshot.call_count,2)
        self.assertTrue(all(c.kwargs['full_page'] is False for c in page.screenshot.call_args_list))
    def test_oversized_capture_is_omitted_explicitly(self):
        page=Mock();page.evaluate.side_effect=[None,{},None,{}];page.screenshot.return_value=b'x'*220001
        captures=module.capture_visual(page)
        self.assertIsNone(captures[0]['screenshot']);self.assertIn('screenshotWarning',captures[0])
    def test_runs_accessibility_again_after_each_viewport_resize(self):
        page=Mock();page.evaluate.side_effect=[None,{},None,{}];page.screenshot.return_value=b'jpeg'
        observed=[]
        def audit():
            observed.append(page.set_viewport_size.call_args.args[0]['width'])
            return {'checks':[{'id':'fixture','count':len(observed)}]}
        result=module.capture_visual(page,audit)
        self.assertEqual(observed,[1280,390])
        self.assertEqual(result[1]['accessibilityChecks'][0]['count'],2)
