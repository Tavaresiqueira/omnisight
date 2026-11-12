import os
from pathlib import Path
import subprocess
import tempfile
from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


class BackupScriptGuards(SimpleTestCase):
    def test_restore_requires_apply_and_rejects_production_database_name(self):
        command = ['/bin/bash', str(ROOT / 'deploy/backup/restore.sh')]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 2)
        env = dict(os.environ, PGHOST='localhost', PGUSER='fake', PGDATABASE='production', BACKUP_FILE='/not-used', AGE_IDENTITY_FILE='/not-used', DELETION_LEDGER_PATH='/not-used', DELETION_LEDGER_KEY='test-key', DELETION_LEDGER_SHA256='0' * 64)
        response = subprocess.run(command + ['--apply'], env=env, capture_output=True)
        self.assertEqual(response.returncode, 2)
        self.assertIn(b'RESTORE_BLOCKED', response.stderr)
        env['PGDATABASE'] = 'omnisight_restore_fake dbname=production'
        self.assertEqual(subprocess.run(command + ['--apply'], env=env, capture_output=True).returncode, 2)

    def test_failed_dump_cannot_be_reported_as_success_even_if_encryptor_exits_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name, body in [('pg_dump', '#!/bin/sh\nexit 7\n'), ('age', '#!/bin/sh\ncat\n')]:
                path = directory / name; path.write_text(body); path.chmod(0o700)
            env = dict(os.environ, PATH=str(directory) + ':/usr/bin:/bin', PGHOST='localhost', PGUSER='fake', PGDATABASE='test', AGE_RECIPIENT='fake-recipient', BACKUP_DIR=str(directory / 'backups'))
            result = subprocess.run(['/bin/bash', str(ROOT / 'deploy/backup/backup.sh')], env=env, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn(b'BACKUP_FAILED', result.stderr)
            self.assertEqual(list((directory / 'backups').iterdir()), [])
