import tempfile
import unittest
from pathlib import Path
from slotgen_provider.jobs import load_job, resume_job, submit_job


class JobTests(unittest.TestCase):
    def test_restart_resumes_without_another_submit(self):
        with tempfile.TemporaryDirectory() as folder:
            job = Path(folder)/'job.json'
            output = Path(folder)/'result.bin'
            sent = []
            def submit():
                sent.append(True)
                return {'id': 'task-1'}
            submit_job(job, {'provider': 'fixture', 'model': 'fixture', 'output': str(output)}, submit)
            def download(state):
                output.write_bytes(b'valid output')
            resume_job(job, lambda state: {'status': 'ready', 'url': 'https://cdn.example/file'}, download)
            resume_job(job, lambda state: self.fail('completed jobs must not poll'), download)
            self.assertEqual(sent, [True])
            self.assertEqual(load_job(job)['status'], 'downloaded')
            with self.assertRaises(FileExistsError):
                submit_job(job, {'output': str(output)}, submit)
            self.assertEqual(sent, [True])

    def test_lost_submit_response_is_recorded_and_not_resubmitted(self):
        with tempfile.TemporaryDirectory() as folder:
            job = Path(folder)/'job.json'
            def submit():
                raise TimeoutError('fixture')
            with self.assertRaises(TimeoutError):
                submit_job(job, {'provider': 'fixture'}, submit)
            self.assertEqual(load_job(job)['status'], 'submission_unknown')
            with self.assertRaises(ValueError):
                resume_job(job, lambda state: self.fail('no task ID'), lambda state: None)
