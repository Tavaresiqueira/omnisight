"""Signed deletion intents outside the database; keep latest copy independent of DB backups."""
import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import uuid
from datetime import datetime
from django.conf import settings
from django.utils import timezone

MAX_BYTES = 8 * 1024 * 1024
KINDS = {'scan', 'organization', 'user'}


def _key():
    value = settings.DELETION_LEDGER_KEY
    if not isinstance(value, str) or len(value) < 32:
        raise ValueError('Configure a chave independente do registro de exclusões.')
    return value.encode()


def _signature(record):
    return hmac.new(_key(), json.dumps(record, sort_keys=True, separators=(',', ':')).encode(), hashlib.sha256).hexdigest()


def _parse(raw):
    if len(raw) > MAX_BYTES or (raw and not raw.endswith(b'\n')):
        raise ValueError('Registro de exclusões incompleto ou maior que o limite.')
    previous = '0' * 64
    records = []
    for line in raw.splitlines():
        record = json.loads(line)
        if not isinstance(record, dict) or set(record) != {'version', 'kind', 'target', 'requestedAt', 'previous', 'signature'}:
            raise ValueError('Formato de exclusão incompatível.')
        signature = record.pop('signature')
        if any(not isinstance(record[field], str) for field in ['kind', 'target', 'requestedAt', 'previous']):
            raise ValueError('Campos de exclusão inválidos.')
        if type(record['version']) is not int or record['version'] != 1 or record['kind'] not in KINDS or record['previous'] != previous:
            raise ValueError('Cadeia de exclusões incompatível.')
        if str(uuid.UUID(record['target'])) != record['target'] or datetime.fromisoformat(record['requestedAt']).utcoffset() is None:
            raise ValueError('Identificador ou data inválidos.')
        if not isinstance(signature, str) or not re.fullmatch('[0-9a-f]{64}', signature) or not hmac.compare_digest(signature, _signature(record)):
            raise ValueError('Assinatura de exclusão inválida.')
        records.append(record)
        previous = signature
    return records, previous


def append_deletions(targets):
    _key()
    if not settings.DELETION_LEDGER_PATH:
        raise ValueError('Configure armazenamento durável do registro de exclusões.')
    path = Path(settings.DELETION_LEDGER_PATH)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'r+b') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        raw = stream.read(MAX_BYTES + 1)
        _, previous = _parse(raw)
        lines = []
        for kind, target in targets:
            if kind not in KINDS:
                raise ValueError('Tipo de exclusão inválido.')
            record = {'version': 1, 'kind': kind, 'target': str(uuid.UUID(str(target))), 'requestedAt': timezone.now().isoformat(), 'previous': previous}
            previous = _signature(record)
            lines.append(json.dumps({**record, 'signature': previous}, separators=(',', ':')).encode() + b'\n')
        data = b''.join(lines)
        if len(raw) + len(data) > MAX_BYTES:
            raise ValueError('Registro de exclusões exige rotação operacional.')
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
        # Persist the new directory entry too, before acknowledging a DB deletion.
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def read_deletions(path, expected_sha256):
    _key()
    if not re.fullmatch('[0-9a-f]{64}', expected_sha256):
        raise ValueError('Informe SHA-256 obtido de um checkpoint independente e atual.')
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), expected_sha256):
        raise ValueError('O registro não corresponde ao checkpoint informado.')
    return _parse(raw)[0]
