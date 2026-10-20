#!/usr/bin/env python3
"""灵动岛小螃蟹 · 把一只 CSS 动画 SVG 转成灵动岛里能跑的两层像素帧，顺手出样机

    python3 tools/from_svg.py fish 在钓鱼 "在湖边等鱼上钩" "#7FD1E8" crabs/fish/fish.svg \
        --len 10 --box 144x96 --fast fx-ring,fx-drop,fx-bub [--out out/fish]

做的事：
  1. SVG 这一段（--from 起、--len 秒）均匀压进灵动岛 40 格（10 秒一圈），每格拍一张，每个 SVG 单位 --px 个设备像素（6 = 2 点，@3x）。
     --fast 列出的 class 是快层（每格都拍）；其余是慢层（一个姿势停满 --hold 格）。
  2. 颜色收回 SVG 里写的那几种（半透明的边按最近的颜色算，不让它冒出几百种颜色）。
  3. 按 pix.simulate_tiers 的四组计时器规矩算出真实显示，写进 --out（默认 out/<key>）：
     island-compact.gif（真实）/ island-compact-想要的.gif / island-expanded.gif / island-minimal.gif / lock.gif（锁屏一秒一格）
     sheet-真实上想要下.png、report.json（残影、计时器层数）、tiers.json（给 fonts.py 造字体）、frames.json
"""
import argparse, json, os, re, subprocess, shutil, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pix import Frame, simulate, simulate_tiers, pill, save_gif, N, SLOT

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('key'); ap.add_argument('title'); ap.add_argument('detail'); ap.add_argument('accent'); ap.add_argument('svg')
ap.add_argument('--from', dest='t0', type=float, default=0); ap.add_argument('--len', dest='L', type=float, default=10)
ap.add_argument('--css', default='.breathe,.shadow{animation:none!important}')
ap.add_argument('--px', type=int, default=6)              # 6 = 一格 2 点（@3x），螃蟹身子约 30 点宽，塞满紧凑态
ap.add_argument('--box', default='120x96')                # 紧凑态左边那块最多多大（设备像素）：40×32 点
ap.add_argument('--hide-shadow', action='store_true', default=True)
ap.add_argument('--fast', default='')                       # 这些零件（class，逗号隔开）照每秒四下拍；其余的每个姿势停满 --hold 格
ap.add_argument('--hold', type=int, default=4)              # 大东西一个姿势停几格（4 格 = 1 秒，正好熄掉的点黑满一秒，没有残影）；1 = 不停
ap.add_argument('--hold-shift', type=float, default=0)      # 慢的那份取样往后挪几格（挑到好看的姿势）
ap.add_argument('--out', default='')                       # 输出目录，默认 out/<key>
o = ap.parse_args()

svg = os.path.abspath(o.svg)
src = open(svg, encoding='utf-8').read()
def hexes(t):
    out = []
    for h in re.findall(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', t):
        h = h.lower(); h = ''.join(c * 2 for c in h) if len(h) == 3 else h
        if h not in out: out.append(h)
    return out
cut = src.find('</defs>')
draw_order = hexes(src[cut:]) if cut >= 0 else hexes(src)
pal_hex = draw_order + [h for h in hexes(src) if h not in draw_order]
LET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
pal = {LET[i]: '#' + h for i, h in enumerate(pal_hex)}
rgb = {c: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for c, v in pal.items()}
z = list(pal.keys())                      # SVG 里后画的在上层

out = os.path.abspath(o.out) if o.out else os.path.join(ROOT, 'out', o.key); tmp = os.path.join(out, '_tmp')
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp, exist_ok=True)
times = [o.t0 + k * o.L / N for k in range(N)]
slow = [o.t0 + ((k // o.hold) * o.hold + o.hold_shift) * o.L / N for k in range(N)]
css = o.css + ('.shadow,[class*="shadow"]{display:none!important}' if o.hide_shadow else '')
fast = [c for c in o.fast.split(',') if c]
def shoot(ts, extra_css, sub):
    d = os.path.join(tmp, sub)
    r = subprocess.run(['node', os.path.join(ROOT, 'tools/render.mjs'), '--svg', svg, '--out', d, '--px', str(o.px),
                        '--times', ','.join(f'{t:.4f}' for t in ts), '--css', css + extra_css], capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stderr or r.stdout)
    return [Image.open(os.path.join(d, f)).convert('RGBA') for f in sorted(os.listdir(d)) if f.startswith('f_')]
if fast:
    sel = ','.join(f'#host .{c},#host .{c} *' for c in fast)
    ims = shoot(slow, ''.join(f'#host .{c}{{visibility:hidden!important}}' for c in fast), 'slow')
    top = shoot(times, '#host svg *{visibility:hidden!important}' + sel + ',#host svg defs,#host svg defs *{visibility:visible!important}', 'fast')
else:
    ims = shoot(slow if o.hold > 1 else times, '', 'all'); top = None

allims = ims + (top or [])
# 裁到所有帧合起来的内容框，四周留 1 格；超过 --box 就以螃蟹身子为中心裁（远处飘的小东西裁掉）
boxes = [im.getbbox() for im in allims if im.getbbox()]
x0 = max(0, min(b[0] for b in boxes) - 1); y0 = max(0, min(b[1] for b in boxes) - 1)
x1 = min(ims[0].size[0], max(b[2] for b in boxes) + 1); y1 = min(ims[0].size[1], max(b[3] for b in boxes) + 1)
BW, BH = map(int, o.box.split('x'))
if x1 - x0 > BW or y1 - y0 > BH:
    # 身子 = #DE886D（Clawd 橙）
    tgt = (0xDE, 0x88, 0x6D)
    bx = []
    for im in ims:
        p_ = im.load(); W_, H_ = im.size
        pts = [(x, y) for y in range(0, H_, 2) for x in range(0, W_, 2) if p_[x, y][3] >= 128 and sum(abs(a - b) for a, b in zip(p_[x, y][:3], tgt)) < 40]
        if pts: bx.append((min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts)))
    cx = (min(b[0] for b in bx) + max(b[2] for b in bx)) // 2; cy = (min(b[1] for b in bx) + max(b[3] for b in bx)) // 2
    if x1 - x0 > BW: x0 = max(0, cx - BW // 2); x1 = x0 + BW
    if y1 - y0 > BH:
        by1 = max(b[3] for b in bx) + 2            # 脚底下留一点，往上多给道具
        y1 = min(ims[0].size[1], by1); y0 = max(0, y1 - BH)
cache = {}
def near(p):
    if p not in cache:
        cache[p] = min(rgb, key=lambda c: sum((a - b) ** 2 for a, b in zip(rgb[c], p)))
    return cache[p]
def quant(im):
    im = im.crop((x0, y0, x1, y1)); W, H = im.size; px = im.load(); f = Frame(W, H)
    for y in range(H):
        for x in range(W):
            r_, g_, b_, a_ = px[x, y]
            if a_ >= 128: f.px[(x, y)] = near((r_, g_, b_))
    return f
slowf = [quant(im) for im in ims]
fastf = [quant(im) for im in top] if top else [Frame(slowf[0].w, slowf[0].h) for _ in slowf]
if o.hold > 1:
    shown, frames, bad, stats = simulate_tiers(slowf, fastf, z, o.hold)
else:
    frames = slowf; shown, bad, stats = simulate(frames, list(range(N)), z)
ms = int(SLOT * 1000)
big = lambda f, s=1: f.image(pal, s)
save_gif([pill(big(f), 'compact', o.title, o.detail, o.accent) for f in shown], f'{out}/island-compact.gif', ms)
save_gif([pill(big(f), 'compact', o.title, o.detail, o.accent) for f in frames], f'{out}/island-compact-想要的.gif', ms)
save_gif([pill(big(f, 2), 'expanded', o.title, o.detail, o.accent) for f in shown], f'{out}/island-expanded.gif', ms)
save_gif([pill(big(f), 'minimal', o.title, o.detail, o.accent) for f in shown], f'{out}/island-minimal.gif', ms)
save_gif([pill(big(frames[k * 4], 2), 'lock', o.title, o.detail, o.accent) for k in range(10)], f'{out}/lock.gif', 1000)
# 一张帧表（真实显示 vs 想要的，每 2 格取一张），给我自己看
cols = 10; s = 2; W, H = frames[0].w * s, frames[0].h * s
sheet = Image.new('RGB', (cols * (W + 4), 4 * (H + 4)), (40, 40, 46))
for i in range(0, N, 2):
    k = i // 2
    sheet.paste(shown[i].image(pal, s, bg=(0, 0, 0, 255)).convert('RGB'), ((k % cols) * (W + 4), (k // cols) * 2 * (H + 4)))
    sheet.paste(frames[i].image(pal, s, bg=(0, 0, 0, 255)).convert('RGB'), ((k % cols) * (W + 4), ((k // cols) * 2 + 1) * (H + 4)))
sheet.save(f'{out}/sheet-真实上想要下.png')
tot = frames[0].w * frames[0].h
rep = {'key': o.key, 'svg': os.path.basename(svg), '段': [o.t0, o.L], 'hold': o.hold, 'fast': fast, '格子': [frames[0].w, frames[0].h], '颜色': len(pal),
       '最多一格残影': max(bad), '残影占比%': round(100 * sum(bad) / (N * tot), 2), **stats}
json.dump({'palette': pal, 'z': z, 'grid': [frames[0].w, frames[0].h], 'hold': o.hold, 'slow': [f.rows() for f in slowf], 'fast': [f.rows() for f in fastf],
           'title': o.title, 'detail': o.detail, 'accent': o.accent},
          open(f'{out}/tiers.json', 'w'), ensure_ascii=False)
json.dump({'palette': pal, 'z': z, 'grid': [frames[0].w, frames[0].h], 'island': [f.rows() for f in frames]},
          open(f'{out}/frames.json', 'w'), ensure_ascii=False)
json.dump(rep, open(f'{out}/report.json', 'w'), ensure_ascii=False, indent=1)
shutil.rmtree(tmp, ignore_errors=True)
print(json.dumps(rep, ensure_ascii=False))
