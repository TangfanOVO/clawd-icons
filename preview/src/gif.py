#!/usr/bin/env python3
"""逐帧 PNG → 循环 GIF（render.mjs 跑完会自己调它）。

    python3 preview/src/gif.py 帧目录 preview/phone-demo.gif --fps 20 --scale 2

--scale 是截图比最终大几倍：按整数倍做方块平均缩回去，像素小螃蟹的边不糊。
所有帧共用一套 256 色调色板、不抖动；没变的帧并进上一帧的时长，变了的只写改动的那一块（Pillow 自己算）。
"""
import argparse
import glob
import os

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument('frames')
ap.add_argument('out')
ap.add_argument('--fps', type=float, default=20)
ap.add_argument('--scale', type=int, default=1)
ap.add_argument('--colors', type=int, default=256)
o = ap.parse_args()

paths = sorted(glob.glob(os.path.join(o.frames, 'f_*.png')))
if not paths:
    raise SystemExit('没有帧：' + o.frames)
ims = []
for p in paths:
    im = Image.open(p).convert('RGB')
    if o.scale > 1:
        im = im.reduce(o.scale)
    ims.append(im)

# 调色板从一叠抽样帧里算，所有帧共用
step = max(1, len(ims) // 40)
sample = ims[::step]
w, h = ims[0].size
stack = Image.new('RGB', (w, h * len(sample)))
for i, im in enumerate(sample):
    stack.paste(im, (0, h * i))
pal = stack.quantize(colors=o.colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)

out = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
ms = round(1000 / o.fps)
out[0].save(o.out, save_all=True, append_images=out[1:], duration=ms, loop=0, disposal=1, optimize=False)

g = Image.open(o.out)
print(f'{o.out}: {g.size[0]}×{g.size[1]}，{len(ims)} 帧 → 写进 {g.n_frames} 帧，{os.path.getsize(o.out) / 1024:.0f} KB，loop={g.info.get("loop")}')
