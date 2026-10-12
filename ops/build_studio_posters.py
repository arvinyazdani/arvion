"""Build-only Pillow==11.3.0: AVIF variants of the same rendered poster pixels.

Original WebP files remain intact for browsers without AVIF. Dimensions, crop,
composition and colour profile are preserved; no image generation or redesign.
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'core/static/core/studio/posters'


def build():
    original_size = output_size = 0
    for room in ('workshop', 'exam', 'library', 'reception'):
        for device in ('desktop', 'mobile'):
            source = ROOT / f'{room}-{device}.webp'
            target = source.with_suffix('.avif')
            with Image.open(source) as image:
                image.save(target, format='AVIF', quality=60, speed=6,
                           icc_profile=image.info.get('icc_profile'))
                with Image.open(target) as encoded:
                    assert encoded.size == image.size
            original_size += source.stat().st_size
            output_size += target.stat().st_size
            print(source.name, source.stat().st_size, '→', target.stat().st_size)
    print('Total poster bytes:', original_size, '→', output_size)


if __name__ == '__main__':
    build()
