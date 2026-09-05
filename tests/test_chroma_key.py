from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "chroma_key.py"
SPEC = importlib.util.spec_from_file_location("chroma_key", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class GreenChromaDespillTests(unittest.TestCase):
    def test_existing_transparency_does_not_become_opaque(self) -> None:
        image = Image.new("RGBA", (2, 1))
        image.putdata(((200, 140, 0, 0), (200, 140, 0, 64)))
        result = MODULE.chroma_key(image, (255, 0, 255), erode=0, despill=False)
        self.assertEqual(result.getpixel((0, 0)), (200, 140, 0, 0))
        self.assertEqual(result.getpixel((1, 0)), (200, 140, 0, 64))

    def test_green_chroma_preserves_purple_foreground(self) -> None:
        image = Image.new("RGBA", (2, 1))
        image.putdata(((0, 255, 0, 255), (180, 40, 200, 255)))

        result = MODULE.chroma_key(image, (0, 255, 0), erode=0, despill=True)

        self.assertEqual(result.getpixel((0, 0))[3], 0)
        self.assertEqual(result.getpixel((1, 0)), (180, 40, 200, 255))

    def test_green_chroma_neutralizes_retained_green_spill(self) -> None:
        image = Image.new("RGBA", (1, 1), (40, 180, 50, 255))

        result = MODULE.chroma_key(image, (0, 255, 0), erode=0, despill=True)

        self.assertEqual(result.getpixel((0, 0)), (40, 58, 50, 255))


if __name__ == "__main__":
    unittest.main()
