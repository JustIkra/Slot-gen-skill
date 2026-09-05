"""Extract straight-alpha light from black, retaining canvas and isolated sparks."""
import argparse
import numpy as np
from PIL import Image


def key_light(image):
    rgba = np.asarray(image.convert('RGBA'), dtype=np.float64) / 255
    intensity = rgba[..., :3].max(axis=2, keepdims=True)
    rgb = np.divide(rgba[..., :3], intensity, out=np.zeros_like(rgba[..., :3]), where=intensity > 0)
    alpha = intensity * rgba[..., 3:]
    return Image.fromarray(np.rint(np.clip(np.concatenate((rgb, alpha), axis=2), 0, 1)*255).astype(np.uint8))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    with Image.open(args.input) as image:
        result = key_light(image)
        result.save(args.output)
        print(f'Straight-alpha additive light: {result.size}; no crop, no resize')


if __name__ == '__main__':
    main()
