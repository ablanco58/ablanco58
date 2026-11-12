"""Ensambla los renders de Blender en un GIF transparente de 3 segundos.

Requiere Pillow: python -m pip install pillow
"""
from pathlib import Path
import argparse
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', default='stormtrooper')
parser.add_argument('--name', default='stormtrooper-spin.gif')
options = parser.parse_args()
frames = sorted((ROOT / 'output' / options.source).glob('frame-*.png'))
if len(frames) != 72:
    raise SystemExit(f'Se necesitan 72 fotogramas. Encontrados: {len(frames)}')

with Image.open(frames[0]) as image:
    size = image.size
atlas = Image.new('RGB', (size[0] * 4, size[1] * 3))
for cell, index in enumerate(range(0, len(frames), 6)):
    with Image.open(frames[index]) as image:
        atlas.paste(image.convert('RGB'), (cell % 4 * size[0], cell // 4 * size[1]))
palette = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
# Reserva un color ajeno al modelo para que el negro del traje no se vuelva transparente.
palette.putpalette(palette.getpalette()[:765] + [255, 0, 255])

images, durations = [], []
for index, file in enumerate(frames):
    with Image.open(file) as source:
        source = source.convert('RGBA')
        frame = source.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE)
        transparent = source.getchannel('A').point(lambda value: 255 if value < 128 else 0)
        frame.paste(255, mask=transparent)
        frame.info['transparency'] = 255
        images.append(frame)
    durations.append(round((index + 1) * 100 / 24) * 10 - round(index * 100 / 24) * 10)

target = ROOT / 'assets' / options.name
target.parent.mkdir(exist_ok=True)
images[0].save(target, save_all=True, append_images=images[1:], duration=durations,
    loop=0, disposal=2, transparency=255, background=255, optimize=False)
print(f'{target}: {len(images)} frames, {sum(durations)} ms, {target.stat().st_size:,} bytes')
