import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from slotgen_provider.video import run_cli


class Response:
    def __init__(self,payload):
        self.status=200;self.headers={};self.body=io.BytesIO(payload)
    def read(self,n=-1):return self.body.read(n)
    def close(self):pass


class VideoJobsTests(unittest.TestCase):
    def test_invalid_download_preserves_output_and_resume_does_not_resubmit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);anchor=root/'anchor.png';movie=root/'fixture.mp4'
            Image.new('RGB',(4,4),'yellow').save(anchor)
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=yellow:s=32x32:d=0.1','-c:v','libx264',str(movie)],check=True)
            good=movie.read_bytes();downloads=[b'not video',good];sent=[]
            def send(method,url,headers,body,timeout):
                sent.append((method,url,headers))
                if method=='POST':
                    payload=json.loads(body)
                    self.assertEqual(len(payload['frame_images']),2)
                    self.assertEqual(payload['model'],'kwaivgi/kling-v3.0-std')
                    return Response(b'{"id":"task-1"}')
                if url.endswith('/task-1'):return Response(b'{"status":"completed","unsigned_urls":["https://cdn.example/video.mp4"]}')
                return Response(downloads.pop(0))
            output=root/'output.mp4';output.write_bytes(b'accepted');job=root/'job.json'
            initial=['video','--first',str(anchor),'--last',str(anchor),'--prompt','fixture','--out',str(output),'--job-file',str(job),'--poll-interval','0']
            with patch('slotgen_provider.video.provider_key',return_value='fixture-key'),patch('slotgen_provider.http._open_once',side_effect=send):
                with patch.object(sys,'argv',initial),self.assertRaises(ValueError):run_cli()
                self.assertEqual(output.read_bytes(),b'accepted')
                self.assertEqual(json.loads(job.read_text())['status'],'ready')
                with patch.object(sys,'argv',['video','--action','resume','--job-file',str(job)]):run_cli()
            self.assertEqual(sum(method=='POST' for method,_,_ in sent),1)
            self.assertEqual(output.read_bytes(),good)
            self.assertNotIn('Authorization',sent[-1][2])
            self.assertNotIn('fixture-key',job.read_text())
