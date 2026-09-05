import runpy
import unittest
from pathlib import Path
import numpy as np
from PIL import Image


class LightAlphaTests(unittest.TestCase):
    def test_preserves_particles_canvas_and_additive_energy(self):
        extract = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'scripts/key_light.py'))['key_light']
        image = Image.new('RGBA', (4, 1))
        image.putdata([(0,0,0,255),(80,40,5,255),(8,4,1,255),(200,100,10,64)])
        result = extract(image)
        self.assertEqual(result.size, image.size)
        self.assertEqual(result.getpixel((0,0))[3], 0)
        self.assertGreater(result.getpixel((2,0))[3], 0)
        source = np.asarray(image, dtype=float)
        output = np.asarray(result, dtype=float)
        expected = source[...,:3] * source[...,3:] / 255
        actual = output[...,:3] * output[...,3:] / 255
        self.assertLessEqual(float(np.max(np.abs(expected-actual))), 1)
