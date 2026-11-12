"""Exercise deploy ordering/failure semantics without a Docker daemon or SSH."""
import gzip
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


DEPLOY = Path(__file__).resolve().parents[1]
SHA = 'a' * 40


class ActivationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'shared').mkdir()
        (self.root / 'shared/production.env').write_text('APP_DOMAIN=example.test\n')
        incoming = self.root / 'incoming/1-1'
        (incoming / 'deploy').mkdir(parents=True)
        (incoming / 'images').mkdir()
        for filename in ('compose.yml', 'compose.release.yml', 'smoke.sh'):
            (incoming / 'deploy' / filename).write_bytes((DEPLOY / filename).read_bytes())
        for service in ('api', 'browser', 'web', 'backup'):
            (incoming / 'images' / f'{service}.tar.gz').write_bytes(gzip.compress(b'image'))
        self.script = self.root / 'activate.sh'
        self.script.write_text((DEPLOY / 'activate.sh').read_text().replace(
            'root=/opt/omnisight', f'root={self.root}'))
        bin_dir = self.root / 'bin'
        bin_dir.mkdir()
        docker = bin_dir / 'docker'
        docker.write_text('''#!/usr/bin/env bash
set -eu
echo "$*" >> "$CALL_LOG"
if [[ "$1" == load ]]; then cat >/dev/null; fi
if [[ "$*" == *'ps --status running --services'* && "$EXISTING_DB" == 1 ]]; then echo db; fi
if [[ "$*" == *'run --rm --no-build backup'* && "$FAIL_AT" == backup ]]; then exit 1; fi
if [[ "$*" == *'run --rm --no-build migrate'* && "$FAIL_AT" == migrate ]]; then exit 1; fi
if [[ "$*" == *'exec -T api python'* ]]; then echo example.test; fi
exit 0
''')
        docker.chmod(0o700)
        for tool, body in [('curl', 'test "$FAIL_AT" != smoke'), ('sleep', 'exit 0')]:
            path = bin_dir / tool
            path.write_text('#!/bin/sh\n' + body + '\n')
            path.chmod(0o700)
        self.env = {**os.environ, 'PATH': f'{bin_dir}:' + os.environ['PATH'],
                    'CALL_LOG': str(self.root / 'calls'), 'FAIL_AT': '', 'EXISTING_DB': '1'}

    def run_activation(self, failure=''):
        return subprocess.run(['bash', str(self.script), SHA, '1-1'],
                              env={**self.env, 'FAIL_AT': failure}, capture_output=True, text=True)

    def test_success_requires_backup_before_migration_and_marks_release(self):
        result = self.run_activation()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = (self.root / 'calls').read_text()
        self.assertLess(calls.index('run --rm --no-build backup'), calls.index('stop api worker retention'))
        self.assertLess(calls.index('run --rm --no-build migrate'), calls.index('--force-recreate --wait'))
        self.assertEqual((self.root / 'deployed-sha').read_text().strip(), SHA)
        self.assertEqual((self.root / 'current').resolve(), self.root / 'releases' / SHA)

    def test_failed_backup_does_not_stop_writers(self):
        self.assertNotEqual(self.run_activation('backup').returncode, 0)
        self.assertNotIn('stop api worker retention', (self.root / 'calls').read_text())
        self.assertFalse((self.root / 'current').exists())

    def test_failed_migration_never_activates_services_or_marks_success(self):
        self.assertNotEqual(self.run_activation('migrate').returncode, 0)
        self.assertNotIn('--force-recreate --wait', (self.root / 'calls').read_text())
        self.assertFalse((self.root / 'deployed-sha').exists())

    def test_failed_smoke_preserves_previous_marker(self):
        (self.root / 'deployed-sha').write_text('previous\n')
        self.assertNotEqual(self.run_activation('smoke').returncode, 0)
        self.assertEqual((self.root / 'deployed-sha').read_text(), 'previous\n')

    def test_invalid_sha_never_calls_docker(self):
        result = subprocess.run(['bash', str(self.script), '../escape', '1-1'], env=self.env)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'calls').exists())


if __name__ == '__main__':
    unittest.main()
