import importlib.util
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('server',Path(__file__).resolve().parents[1]/'server.py');server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
class ServiceTests(TestCase):
    def test_rejects_untrusted_shapes_before_process_creation(self):
        for data in [{},{'html':4},{'html':'x','url':'http://private'},{'html':'x'*2097153}]:
            with self.assertRaises(ValueError):server.execute(data)
    @patch.dict('os.environ',{'DATABASE_URL':'secret','AWS_SECRET_ACCESS_KEY':'secret'},clear=False)
    @patch.object(server.subprocess,'Popen')
    def test_child_does_not_receive_application_or_cloud_credentials(self,popen):
        popen.return_value.communicate.return_value=(b'{}',b'');popen.return_value.returncode=0
        self.assertEqual(server.execute({'html':'x'}),{})
        env=popen.call_args.kwargs['env'];self.assertNotIn('DATABASE_URL',env);self.assertNotIn('AWS_SECRET_ACCESS_KEY',env)

    @patch.object(server.os,'killpg')
    @patch.object(server.subprocess,'Popen')
    def test_timeout_kills_the_entire_process_group(self,popen,killpg):
        import subprocess,signal
        process=popen.return_value;process.pid=123;process.communicate.side_effect=[subprocess.TimeoutExpired('runner',40),(b'',b'')]
        with self.assertRaises(TimeoutError):server.execute({'html':'x'})
        killpg.assert_called_once_with(123,signal.SIGKILL)
