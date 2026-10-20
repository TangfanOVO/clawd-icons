#!/usr/bin/env python3
"""灵动岛小螃蟹 · 把转好的状态造成「计时器字体」＋ Swift 对照表

    python3 tools/fonts.py <字体输出目录> <Swift 输出路径> [--from out] 在钓鱼=fish 在看外面=window ... [_phase]

读 <--from>/<key>/tiers.json（from_svg.py 出的：slow / fast 两层，每层 40 格 × 0.25 秒；--from 默认 out）。
参数写成「显示名=key」时，Swift 表里用显示名当键；只写 key 就用 key。每一层造一套 TTF：
  数字 0–9 = 这一层的十个字形，冒号零宽；计时器秒的个位走到几就显示第几个。
  · 慢层：一种颜色一套，起点不挪（phase 0）。第 d 个字形 = 第 4d 格（慢层每 4 格才换，整块交给这一组）。
  · 快层：一种颜色四套，起点晚 0 / 0.25 / 0.5 / 0.75 秒。第 g 组第 d 个字形 = 第 4d+g 格。
  · 蒙版：四套纯黑，同样四组错开；第 g 组第 d 个字形 = 快层范围里「接下来 4 格都该是黑底」的点。
  叠的顺序（下→上）：慢层 → 快层 → 蒙版。
特殊 key「_phase」：测节拍用，四根柱子各归一组，柱高 = 那一组秒的个位 + 1。

三条踩过的坑：lsb 要等于 xMin；PostScript 名 / 全名必须有；每套字体的名字不能撞（这里一律 XF 开头）。
字体里一格 = 10 单位，1 em = 100 格；Swift 里 .font(.custom(名, fixedSize: 一格几点 × 100))。
"""
import json, os, sys
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_a = sys.argv[1:]
SRC = os.path.join(ROOT, 'out')
if '--from' in _a:
    _i = _a.index('--from'); SRC = _a[_i + 1]; del _a[_i:_i + 2]
OUT, SWIFT, ARGS = _a[0], _a[1], _a[2:]
# 参数可以写成「显示名=key」（在钓鱼=fish），表里用显示名；同一个 key 只造一次字体
PAIRS = [(a.split('=', 1) if '=' in a else (a, a)) for a in ARGS]
KEYS = list(dict.fromkeys(k for _, k in PAIRS))
os.makedirs(OUT, exist_ok=True)
U = 10
DIG = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def rects(pts):
    """一堆格子并成尽量少的长方形：先横着连成段，再把上下相同的段并起来。"""
    rows = {}
    for x, y in pts: rows.setdefault(y, []).append(x)
    runs = {}
    for y, xs in rows.items():
        xs.sort(); s = xs[0]; prev = xs[0]
        for x in xs[1:] + [None]:
            if x is not None and x == prev + 1: prev = x; continue
            runs.setdefault(y, []).append((s, prev + 1))
            if x is not None: s = prev = x
    out, open_ = [], {}
    prev = None
    for y in sorted(runs):
        # 1021：中间隔着空行就先把开着的块收口，不然上下两块同宽同位的会被连成一根竖条（出门走走的鸟和尘土连成白条）
        if prev is not None and y != prev + 1:
            for r, y0 in open_.items(): out.append((r[0], y0, r[1] - r[0], prev + 1 - y0))
            open_ = {}
        cur = {}
        for r in runs[y]:
            if r in open_: cur[r] = open_.pop(r)
            else: cur[r] = y
        for r, y0 in open_.items(): out.append((r[0], y0, r[1] - r[0], y - y0))
        open_ = cur
        prev = y
    for r, y0 in open_.items(): out.append((r[0], y0, r[1] - r[0], max(runs) + 1 - y0))
    return out


def glyph(pts, H):
    pen = TTGlyphPen(None)
    for x, y, w, h in rects(pts):
        ax0, ax1 = x * U, (x + w) * U
        ay1, ay0 = (H - y) * U, (H - y - h) * U
        pen.moveTo((ax0, ay0)); pen.lineTo((ax0, ay1)); pen.lineTo((ax1, ay1)); pen.lineTo((ax1, ay0)); pen.closePath()
    return pen.glyph()


def build_font(fam, digits, W, H):
    order = [".notdef", "space", "colon"] + DIG
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    cmap = {0x20: "space", 0x3A: "colon"}; cmap.update({0x30 + i: n for i, n in enumerate(DIG)})
    fb.setupCharacterMap(cmap)
    empty = TTGlyphPen(None).glyph
    gl = {".notdef": empty(), "space": empty(), "colon": empty()}
    gl.update({n: glyph(digits[i], H) for i, n in enumerate(DIG)})
    fb.setupGlyf(gl)
    gt = fb.font["glyf"]; lsb = {}
    for n in order:
        g = gt[n]; g.recalcBounds(gt)
        lsb[n] = getattr(g, "xMin", 0) if g.numberOfContours else 0
    fb.setupHorizontalMetrics({n: ((0 if n == "colon" else W * U), lsb[n]) for n in order})
    fb.setupHorizontalHeader(ascent=H * U, descent=0)
    fb.setupNameTable({"familyName": fam, "styleName": "Regular", "fullName": fam, "psName": fam,
                       "uniqueFontIdentifier": f"{fam}-1020", "version": "Version 1.000"})
    fb.setupOS2(sTypoAscender=H * U, sTypoDescender=0, usWinAscent=H * U, usWinDescent=0)
    fb.setupPost()
    fb.save(f"{OUT}/{fam}.ttf")
    return f"{fam}.ttf"


def parse(rows):
    return {(x, y): c for y, r in enumerate(rows) for x, c in enumerate(r) if c != '.'}


states, files = [], []
for si, key in enumerate(KEYS, 1):
    layers = []
    if key == '_phase':
        W, H = 9, 11
        cols = [0xFF5A5A, 0xFFD34D, 0x5AE07A, 0x5AA8FF]
        for g in range(4):
            dig = [[(2 * g + i, H - 1 - j) for i in range(2) for j in range(d + 1)] for d in range(10)]
            fam = f"XF{si:02d}{g:02d}"; files.append(build_font(fam, dig, W, H))
            layers.append((fam, cols[g], g * 0.25, 1))
        states.append((key, W, H, layers)); continue
    T = json.load(open(os.path.join(SRC, key, 'tiers.json'), encoding='utf-8'))
    W, H = T['grid']; pal = T['palette']; z = T['z']
    slow = [parse(r) for r in T['slow']]; fast = [parse(r) for r in T['fast']]
    n = len(slow)
    rgb = lambda c: int(pal[c][1:], 16)
    zi = {c: i for i, c in enumerate(z)}
    li = 0
    slow_cols = sorted({c for f in slow for c in f.values()}, key=lambda c: zi.get(c, -1))
    for c in slow_cols:
        dig = [[p for p, v in slow[4 * d].items() if v == c] for d in range(10)]
        fam = f"XF{si:02d}{li:02d}"; li += 1; files.append(build_font(fam, dig, W, H)); layers.append((fam, rgb(c), 0.0, 0))
    fast_cols = sorted({c for f in fast for c in f.values()}, key=lambda c: zi.get(c, -1))
    for c in fast_cols:
        for g in range(4):
            dig = [[p for p, v in fast[(4 * d + g) % n].items() if v == c] for d in range(10)]
            fam = f"XF{si:02d}{li:02d}"; li += 1; files.append(build_font(fam, dig, W, H)); layers.append((fam, rgb(c), g * 0.25, 1))
    if fast_cols:
        region = {p for f in fast for p in f}
        tgt = [{**s, **f} for s, f in zip(slow, fast)]
        for g in range(4):
            dig = []
            for d in range(10):
                k = 4 * d + g
                base = {p for p in region if all(p not in tgt[(k + e) % n] for e in range(4))}
                # 往外扩一格，盖住快层字形抗锯齿的那圈边（只扩进接下来 4 格也都是黑底的点，不会盖到该显示的东西）
                grow = {(x + dx, y + dy) for x, y in base for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
                grow = {q for q in grow if 0 <= q[0] < W and 0 <= q[1] < H and all(q not in tgt[(k + e) % n] for e in range(4))}
                dig.append(sorted(base | grow))
            fam = f"XF{si:02d}{li:02d}"; li += 1; files.append(build_font(fam, dig, W, H)); layers.append((fam, 0x000000, g * 0.25, 2))
    states.append((key, W, H, layers))

rows = []
byk = {key: (W, H, layers) for key, W, H, layers in states}
for name, key in PAIRS:
    W, H, layers = byk[key]
    rows.append(f'    "{name}": CrabState2(w: {W}, h: {H}, layers: [\n        ' +
                ",\n        ".join(f'CrabLayer2(font: "{f}", color: 0x{c:06X}, phase: {ph}, kind: {kd})' for f, c, ph, kd in layers) + "]),")
open(SWIFT, "w").write(
    "//  自动生成：tools/fonts.py —— 别手改。\n"
    "//  每层一套字体（数字 0–9 = 十个字形），phase = 这层计时器的起点晚几秒（0 / 0.25 / 0.5 / 0.75）。\n"
    "//  叠的顺序就是数组顺序：慢层 → 快层 → 黑蒙版。一格 = 10 单位，1 em = 100 格。\n\n"
    "//  kind：0 慢层 / 1 快层 / 2 黑蒙版。锁屏（液态玻璃底）只用 phase 0 且不是蒙版的层：一秒一换、不留残影。\n"
    "struct CrabLayer2 { let font: String; let color: UInt32; let phase: Double; let kind: Int }\n"
    "struct CrabState2 { let w: Int; let h: Int; let layers: [CrabLayer2] }\n\n"
    "let CRAB_STATES_2: [String: CrabState2] = [\n" + "\n".join(rows) + "\n]\n\n"
    "let CRAB_FONT_FILES_2: [String] = [" + ", ".join(f'"{x}"' for x in files) + "]\n")
print(len(files), "套字体；", {k: len(l) for k, _, _, l in states})
