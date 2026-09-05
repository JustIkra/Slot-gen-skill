import argparse
import base64
import hashlib
import json
import mimetypes
import time
import os
import tempfile
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from .env import provider_key
from .http import download_artifact, request_json, validate_api_url
from .jobs import load_job, resume_job, submit_job

ORIGIN = 'https://openrouter.ai'
ENDPOINT = ORIGIN + '/api/v1/videos'


def run_cli():
    parser = argparse.ArgumentParser(description='Submit/resume/download an OpenRouter video without duplicate generation')
    parser.add_argument('--action', choices=['auto', 'submit', 'resume', 'download'], default='auto')
    parser.add_argument('--first')
    parser.add_argument('--last')
    parser.add_argument('--out')
    parser.add_argument('--prompt')
    parser.add_argument('--job-file')
    parser.add_argument('--model', default='kwaivgi/kling-v3.0-std')
    parser.add_argument('--duration', type=int, default=5)
    parser.add_argument('--resolution', default='720p')
    parser.add_argument('--aspect', default='1:1')
    parser.add_argument('--poll-interval', type=float, default=20)
    parser.add_argument('--max-polls', type=int, default=120)
    args = parser.parse_args()
    if args.duration <= 0 or args.poll_interval < 0 or args.max_polls < 1:
        parser.error('Invalid duration or polling parameters')
    job = Path(args.job_file) if args.job_file else Path(args.out+'.job.json') if args.out else None
    if job is None:
        parser.error('--job-file or --out is required')
    if args.action in ('auto', 'submit'):
        if not all((args.first, args.last, args.out, args.prompt)):
            parser.error('submission requires --first --last --out --prompt; use --action resume for an existing job')
        refs = [Path(args.first), Path(args.last)]
        blobs = [p.read_bytes() for p in refs]
        metadata = {'provider': 'openrouter-video', 'model': args.model, 'output': str(Path(args.out).resolve()),
                    'prompt': args.prompt, 'duration': args.duration, 'resolution': args.resolution, 'aspect': args.aspect,
                    'references': [hashlib.sha256(b).hexdigest() for b in blobs]}
        if args.action == 'auto' and job.exists():
            if load_job(job)['metadata'] != metadata:
                parser.error('Existing job has different inputs; choose a new --job-file explicitly')
        else:
            body = {'model': args.model, 'prompt': args.prompt, 'duration': args.duration, 'resolution': args.resolution,
                    'aspect_ratio': args.aspect, 'generate_audio': False, 'frame_images': []}
            for file, blob, kind in zip(refs, blobs, ['first_frame', 'last_frame']):
                mime = mimetypes.guess_type(file)[0] or 'image/png'
                body['frame_images'].append({'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,'+base64.b64encode(blob).decode()}, 'frame_type': kind})
            def submit():
                data = request_json('POST', ENDPOINT, token=provider_key('OPENROUTER_KEY'), allowed_origins={ORIGIN}, body=body)
                return {'id': data.get('id'), 'poll_url': urljoin(ENDPOINT+'/', data.get('polling_url') or str(data.get('id')))}
            submit_job(job, metadata, submit)
        if args.action == 'submit':
            print('Video job saved: '+str(job))
            return
    if load_job(job)['metadata'].get('provider') != 'openrouter-video':
        raise ValueError('Job belongs to a different provider')

    def poll(state):
        if args.action == 'download':
            raise ValueError('Job is not ready; use --action resume')
        validate_api_url(state['poll_url'], {ORIGIN})
        data = request_json('GET', state['poll_url'], token=provider_key('OPENROUTER_KEY'), allowed_origins={ORIGIN})
        if data.get('status') == 'completed':
            urls = data.get('unsigned_urls') or data.get('output', {}).get('urls') or []
            if not urls:
                raise ValueError('Completed job has no artifact URL')
            return {'status': 'ready', 'url': urls[0]}
        return {'status': 'failed' if data.get('status') in ('failed', 'error', 'canceled') else 'running'}

    def download(state):
        from .artifacts import validate_video
        output=Path(state['metadata']['output']);output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.video-download-',dir=output.parent) as folder:
            staged=Path(folder)/'video.mp4'
            download_artifact(state['url'], staged, allowed_hosts={urlsplit(state['url']).hostname}, timeout=300)
            validate_video(staged)
            os.replace(staged,output)

    for _ in range(args.max_polls):
        state = resume_job(job, poll, download)
        print(json.dumps({'id': state['id'], 'status': state['status']}), flush=True)
        if state['status'] == 'downloaded':
            return
        time.sleep(args.poll_interval)
    raise TimeoutError('Video still pending; resume the saved job, do not submit again')
