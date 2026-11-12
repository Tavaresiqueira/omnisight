import os
from pathlib import Path
import subprocess
import unittest


ENTRYPOINT = Path(__file__).resolve().parents[1] / 'railway/api-entrypoint.sh'


class RailwayPersistenceGuards(unittest.TestCase):
    def test_api_refuses_to_start_without_journal_configuration(self):
        env = {k: v for k, v in os.environ.items() if k not in {'DELETION_LEDGER_PATH', 'RAILWAY_VOLUME_MOUNT_PATH'}}
        result = subprocess.run(['sh', str(ENTRYPOINT), 'gunicorn'], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Configure DELETION_LEDGER_PATH', result.stderr)

    def test_api_refuses_to_start_without_persistent_volume(self):
        env = {k: v for k, v in os.environ.items() if k != 'RAILWAY_VOLUME_MOUNT_PATH'}
        env['DELETION_LEDGER_PATH'] = '/data/privacy-ledger/deletions.jsonl'
        result = subprocess.run(['sh', str(ENTRYPOINT), 'gunicorn'], env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Mount a persistent Railway volume', result.stderr)
