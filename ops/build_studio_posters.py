"""Build-only Pillow==11.3.0: AVIF variants of the same rendered poster pixels.

Original WebP files remain intact for browsers without AVIF. Crop, aspect ratio,
composition and colour profile are preserved; no image generation or redesign.
Mobile previews use 675x1200 (over 1.7x a 390px phone) while the actual animated
canvas retains its independent device-pixel-ratio policy.
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
                preview = image.resize((675,1200), Image.Resampling.LANCZOS) if device == 'mobile' else image
                preview.save(target, format='AVIF', quality=45 if device == 'mobile' else 60, speed=6,
                           icc_profile=image.info.get('icc_profile'))
                with Image.open(target) as encoded:
                    assert encoded.size == preview.size
            original_size += source.stat().st_size
            output_size += target.stat().st_size
            print(source.name, source.stat().st_size, '→', target.stat().st_size)
    print('Total poster bytes:', original_size, '→', output_size)


if __name__ == '__main__':
    build()
