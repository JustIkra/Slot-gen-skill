import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class ClientParityTests(unittest.TestCase):
    def test_bun_and_python_produce_identical_dry_run_payloads(self):
        args=['--prompt','fixture','--model','nano-banana-2','--size','2K','--reasoning','high','--dry-run']
        python=subprocess.check_output([sys.executable,'-B',str(ROOT/'scripts/openrouter_image.py'),'generate',*args])
        bun=subprocess.check_output(['bun','run',str(ROOT/'tools/generate-image.ts'),*args])
        self.assertEqual(json.loads(python),json.loads(bun))
        self.assertEqual(json.loads(python)['image_config'],{'aspect_ratio':'1:1','image_size':'2K'})

    def test_unsupported_request_fails_before_credentials_or_spend(self):
        result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/openrouter_image.py'),'generate','--prompt','fixture','--size','4K','--dry-run'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('no automatic',result.stderr)
