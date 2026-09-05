import io
import json
import os
import subprocess
import tempfile
from pathlib import Path


def save_png(payload, output):
    from PIL import Image
    try:
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            encoded=io.BytesIO()
            if image.format=='PNG':
                encoded.write(payload)
            else:
                image.save(encoded,format='PNG')
    except Exception as error:
        raise ValueError('Provider did not return a decodable image') from error
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent,prefix='.image-',delete=False) as file:
            temporary=Path(file.name);file.write(encoded.getvalue());file.flush();os.fsync(file.fileno())
        os.replace(temporary,output)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return str(output)


def validate_video(file):
    result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_type:format=duration','-of','json',str(file)],capture_output=True,text=True)
    if result.returncode:
        raise ValueError('Provider artifact is not a decodable video')
    data=json.loads(result.stdout)
    if not data.get('streams') or data['streams'][0].get('codec_type')!='video':
        raise ValueError('Provider artifact contains no video stream')
    return data
