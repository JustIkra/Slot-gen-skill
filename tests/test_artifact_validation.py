import io
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from slotgen_provider.artifacts import save_png, validate_video


class ArtifactTests(unittest.TestCase):
    def test_invalid_image_does_not_overwrite_accepted_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'image.png'
            output.write_bytes(b'accepted')
            with self.assertRaises(ValueError):
                save_png(b'<html>provider error</html>',output)
            self.assertEqual(output.read_bytes(),b'accepted')

    def test_png_alpha_is_preserved(self):
        image=Image.new('RGBA',(2,1),(200,100,0,64))
        data=io.BytesIO();image.save(data,format='PNG')
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'image.png'
            save_png(data.getvalue(),output)
            with Image.open(output) as loaded:
                self.assertEqual(loaded.getpixel((0,0)),(200,100,0,64))

    def test_nonvideo_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'video.mp4'
            output.write_bytes(b'not a video')
            with self.assertRaises(ValueError):
                validate_video(output)
