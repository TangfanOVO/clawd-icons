#!/usr/bin/env python3
"""灵动岛小螃蟹 · SVG → 顺滑 GIF（推送配图 / app 里 / 聊天用）

    python3 tools/smooth.py crabs/fish/fish.svg crabs/fish/smooth.gif --len 10 [--fps 20] [--px 6] [--sheet out/fish/smooth-sheet.png]

一圈 --len 秒，按 --fps 拍；透明底，裁到所有帧合起来的内容框（四周留一点）。
--sheet 另出一张帧表（黑底，每 0.5 秒一张）给自己看。
"""
import argparse, os, shutil, subprocess, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import save_gif

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('svg'); ap.add_argument('out')
ap.add_argument('--len', type=float, default=10); ap.add_argument('--fps', type=int, default=20); ap.add_argument('--px', type=int, default=6)
ap.add_argument('--sheet', default='')
o = ap.parse_args()
tmp = o.out + '._tmp'; shutil.rmtree(tmp, ignore_errors=True)
ts = [k / o.fps for k in range(int(round(o.len * o.fps)))]
r = subprocess.run(['node', os.path.join(ROOT, 'tools/render.mjs'), '--svg', os.path.abspath(o.svg), '--out', tmp, '--px', str(o.px),
                    '--times', ','.join(f'{t:.4f}' for t in ts)], capture_output=True, text=True)
if r.returncode: raise SystemExit(r.stderr or r.stdout)
ims = [Image.open(os.path.join(tmp, f)).convert('RGBA') for f in sorted(os.listdir(tmp)) if f.startswith('f_')]
bb = [im.getbbox() for im in ims if im.getbbox()]
pad = 2 * o.px
box = (max(0, min(b[0] for b in bb) - pad), max(0, min(b[1] for b in bb) - pad),
       min(ims[0].size[0], max(b[2] for b in bb) + pad), min(ims[0].size[1], max(b[3] for b in bb) + pad))
ims = [im.crop(box) for im in ims]
os.makedirs(os.path.dirname(os.path.abspath(o.out)), exist_ok=True)
save_gif(ims, o.out, int(1000 / o.fps), transparent=True)
if o.sheet:
    step = max(1, o.fps // 2); pick = ims[::step]; cols = 8; W, H = ims[0].size
    sh = Image.new('RGB', (cols * (W + 6), ((len(pick) + cols - 1) // cols) * (H + 6)), (40, 40, 46))
    for i, im in enumerate(pick):
        b = Image.new('RGBA', im.size, (0, 0, 0, 255)); b.alpha_composite(im)
        sh.paste(b.convert('RGB'), ((i % cols) * (W + 6), (i // cols) * (H + 6)))
    os.makedirs(os.path.dirname(os.path.abspath(o.sheet)), exist_ok=True)
    sh.save(o.sheet)
shutil.rmtree(tmp, ignore_errors=True)
print(f'{o.out}: {len(ims)} 帧 {ims[0].size}')
