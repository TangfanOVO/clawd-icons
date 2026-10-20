#!/usr/bin/env python3
"""六只小螃蟹的预览动图（README 门面）：三列两行，每格 = 顺滑版 + 名字 + 灵动岛紧凑态。

    python3 tools/preview_grid.py            # 在 island/ 目录里跑，出 preview.gif

六只都是 10 秒一圈，按同一条时间线取帧，所以格子之间是对齐的。
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CRABS = [('fish', '在钓鱼'), ('care', '惦记你身体'), ('letter', '在给你写信'),
         ('window', '在看外面'), ('travel', '出门走走'), ('food', '在挑吃的')]
FPS, LOOP = 10, 10.0
BG, TILE, INK, KEY = (247, 245, 240), (35, 34, 39), (52, 56, 64), (171, 103, 78)
CW, TH, PH, GAP, M = 280, 236, 62, 20, 24
LABEL = 36
ROW = TH + 8 + LABEL + PH
W = M * 2 + CW * 3 + GAP * 2
H = M * 2 + ROW * 2 + GAP


def font(size, mono=False):
    for p in (['/System/Library/Fonts/Menlo.ttc'] if mono else []) + ['/System/Library/Fonts/Hiragino Sans GB.ttc',
              '/System/Library/Fonts/PingFang.ttc', '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def timeline(path):
    """GIF → [(结束毫秒, RGBA 帧)]，按时长展开，取帧时找第一个结束时间大于 t 的。"""
    im = Image.open(path); out = []; t = 0
    try:
        while True:
            t += im.info.get('duration', 100) or 100
            out.append((t, im.convert('RGBA').copy()))
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return out


def at(tl, ms):
    ms %= tl[-1][0]
    for end, fr in tl:
        if ms < end:
            return fr
    return tl[-1][1]


def rounded(size, r, fill):
    m = Image.new('L', size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    tile = Image.new('RGBA', size, fill + (255,)); tile.putalpha(m); return tile


smooth = {k: timeline(os.path.join(HERE, 'crabs', k, 'smooth.gif')) for k, _ in CRABS}
pill = {k: timeline(os.path.join(HERE, 'crabs', k, 'island-compact.gif')) for k, _ in CRABS}
f_name, f_key = font(17), font(13, mono=True)
tile_bg = rounded((CW, TH), 14, TILE)
base = Image.new('RGBA', (W, H), BG + (255,)); d = ImageDraw.Draw(base)
cells = []
for i, (k, name) in enumerate(CRABS):
    x = M + (i % 3) * (CW + GAP); y = M + (i // 3) * (ROW + GAP)
    base.alpha_composite(tile_bg, (x, y))
    nw = d.textlength(name, font=f_name); kw = d.textlength(k, font=f_key)
    lx = x + (CW - nw - 8 - kw) / 2; ly = y + TH + 8 + 8
    d.text((lx, ly), name, font=f_name, fill=INK)
    d.text((lx + nw + 8, ly + 4), k, font=f_key, fill=KEY)
    cells.append((k, x, y))

# 六只用同一个倍数（按最大那只能放下来算，0.5 一档取整，像素边不糊），大小才一致
S = min(min((CW - 20) / tl[0][1].width, (TH - 20) / tl[0][1].height) for tl in smooth.values())
S = max(1, int(S * 2) / 2)
frames = []
for n in range(int(LOOP * FPS)):
    ms = n * 1000 / FPS; fr = base.copy()
    for k, x, y in cells:
        c = at(smooth[k], ms)
        c = c.resize((int(c.width * S), int(c.height * S)), Image.NEAREST)
        fr.alpha_composite(c, (x + (CW - c.width) // 2, y + (TH - c.height) // 2))
        p = at(pill[k], ms); ps = CW / p.width
        p = p.resize((CW, int(p.height * ps)), Image.LANCZOS)
        fr.alpha_composite(rounded(p.size, 12, TILE), (x, y + TH + 8 + LABEL))
        m = Image.new('L', p.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, p.width - 1, p.height - 1], 12, fill=255)
        p.putalpha(m); fr.alpha_composite(p, (x, y + TH + 8 + LABEL))
    frames.append(fr.convert('RGB'))

# 共用一套调色板：从几帧里取色，不抖动，像素块边才干净
probe = Image.new('RGB', (W, H * 4))
for i, j in enumerate((0, 25, 50, 75)):
    probe.paste(frames[j], (0, H * i))
pal = probe.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
out = os.path.join(HERE, 'preview.gif')
q[0].save(out, save_all=True, append_images=q[1:], duration=int(1000 / FPS), loop=0, optimize=False, disposal=1)
print(out, W, H, len(q), os.path.getsize(out))
