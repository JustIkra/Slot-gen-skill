import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def timestamp():
    return datetime.now(ZoneInfo('Europe/Moscow')).isoformat()


@contextmanager
def locked(file):
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(file)+'.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield file
    finally:
        os.close(descriptor)


def _save(file, state):
    state['updated_at'] = timestamp()
    with tempfile.NamedTemporaryFile(mode='w', dir=file.parent, prefix='.job-', delete=False) as output:
        temporary = Path(output.name)
        try:
            json.dump(state, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, file)
    finally:
        temporary.unlink(missing_ok=True)


def load_job(file):
    state = json.loads(Path(file).read_text())
    if state.get('schemaVersion') != 1:
        raise ValueError('Unsupported job schema')
    return state


def submit_job(file, metadata, submit):
    with locked(file) as file:
        if file.exists():
            raise FileExistsError('Job already exists; resume it or choose a new job file explicitly')
        state = {'schemaVersion': 1, 'metadata': metadata, 'request_hash': hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(), 'status': 'submitting', 'created_at': timestamp()}
        _save(file, state)
        try:
            receipt = submit()
            if not receipt.get('id'):
                raise ValueError('Provider returned no job ID; reconcile before resubmitting')
            state.update(receipt)
            state['status'] = 'running'
        except BaseException:
            state['status'] = 'submission_unknown'
            _save(file, state)
            raise
        _save(file, state)
        return state


def resume_job(file, poll, download=None):
    with locked(file) as file:
        state = load_job(file)
        if state['status'] in ('submitting', 'submission_unknown', 'failed') or not state.get('id'):
            raise ValueError('Job cannot resume automatically: '+state['status'])
        if state['status'] == 'downloaded':
            output = Path(state['metadata']['output'])
            if not output.is_file() or hashlib.sha256(output.read_bytes()).hexdigest() != state['sha256']:
                raise ValueError('Downloaded artifact is missing or changed; restore it before accepting this job')
            return state
        if state['status'] == 'running':
            update = poll(state)
            if update.get('status') not in ('running', 'ready', 'failed'):
                raise ValueError('Unknown provider job status')
            state.update(update)
            _save(file, state)
        if state['status'] == 'failed':
            raise ValueError('Provider job failed')
        if state['status'] == 'ready' and download is not None:
            download(state)
            output = Path(state['metadata']['output'])
            if not output.is_file() or not output.stat().st_size:
                raise ValueError('Download produced no artifact')
            state['sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
            state['status'] = 'downloaded'
            _save(file, state)
        return state
